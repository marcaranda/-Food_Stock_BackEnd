from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from src.model.model import ConfirmedMeal, ConfirmedExercise
import re, requests

client = MongoClient("mongodb+srv://tfgmarcaranda:foodstock@food-stock-cluster.lpjtt.mongodb.net/food_stock?retryWrites=true&w=majority&appName=food-stock-cluster")
db = client["foodstock"]
collection = db["confirmedDay"]
collection.create_index("date", unique=True)

router = APIRouter()

# Custom serializer para ObjectId
def serialize_document(document):
    return {**document, "_id": str(document["_id"])}

@router.get("/confirmedDay/{date}")
async def get_confirmedDay(date: str):
    try:
        confirmedDay = collection.find_one({"date": date})
        if confirmedDay:
            return {"confirmedDay": serialize_document(confirmedDay)}
        else:
            return {"confirmedDay": {"date": date, "meals": [], "exercises": []}}
    except:
        raise HTTPException(status_code=404, detail="Día no encontrado.")
    
@router.get("/confirmedDay/{date}/{dietName}/meals")
async def get_confirmedMeals(date: str, dietName: str):
    try:
        confirmedDay = collection.find_one({"date": date})
        if confirmedDay and 'diets' in confirmedDay:
            for diet in confirmedDay['diets']:
                if dietName in diet:
                    return {"confirmedMeals": diet[dietName]['meal']}
        return {"confirmedMeals": []}
    except:
        raise HTTPException(status_code=404, detail="Comida no encontrada.")
    
@router.get("/confirmedDay/{date}/{trainingName}/exercises")
async def get_confirmedExercises(date: str, trainingName: str):
    try:
        confirmedDay = collection.find_one({"date": date})
        if confirmedDay and 'trainings' in confirmedDay:
            for training in confirmedDay['trainings']:
                if trainingName in training:
                    return {"confirmedExercises": training[trainingName]['exercise']}
        return {"confirmedExercises": []}
    except:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado.")

@router.put("/confirmMeal")
async def add_confirmedMeal(meal: ConfirmedMeal):
    try:
        meal_check(meal)
        meal_dict = {meal.dietName : meal.dict(exclude={'date', 'dietName'})}

        dbData = collection.find_one({"date": meal.date})
        if dbData and 'diets' in dbData:
            if any(meal.dietName in diet for diet in dbData['diets']):
                for diet in dbData['diets']:
                    if meal.dietName in diet: 
                        diet[meal.dietName]['meal'].extend(meal_dict[meal.dietName]['meal'])
                        result = collection.update_one({"date": meal.date}, {"$set": {"diets": dbData['diets']}})
            else:
                result = collection.update_one({"date": meal.date}, {"$addToSet": {"diets": meal_dict}}, upsert=True)
        else:
            result = collection.update_one({"date": meal.date}, {"$addToSet": {"diets": meal_dict}}, upsert=True)

        if result.acknowledged:
            return {"message": "Comida añadida.", "id": str(result.upserted_id)}
        else:
            raise HTTPException(status_code=500, detail="Error al insertar el documento.")
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Esta comida ya existe.")
    
@router.put("/confirmExercise")
async def add_confirmedExercise(code: str, exercise: ConfirmedExercise):
    try:
        exercise_check(exercise)
        exercise_dict = {exercise.trainingName : exercise.dict(exclude={'date', 'trainingName'})}

        exercise_url = get_exercise_url(exercise)
        if exercise_url and code:
            activity_data = get_url_data(exercise_url, code)
            exercise_dict["urlData"] = activity_data

        dbData = collection.find_one({"date": exercise.date})
        if dbData and 'trainings' in dbData:
            if any(exercise.trainingName in training for training in dbData['trainings']):
                for training in dbData['trainings']:
                    if exercise.trainingName in training: 
                        training[exercise.trainingName]['exercise'].extend(exercise_dict[exercise.trainingName]['exercise'])
                        result = collection.update_one({"date": exercise.date}, {"$set": {"trainings": dbData['trainings']}})
            else:
                result = collection.update_one({"date": exercise.date}, {"$addToSet": {"trainings": exercise_dict}}, upsert=True)
        else:
            result = collection.update_one({"date": exercise.date}, {"$addToSet": {"trainings": exercise_dict}}, upsert=True)
        
        if result.acknowledged:
            return {"message": "Ejercicio añadido.", "id": str(result.upserted_id)}
        else:
            raise HTTPException(status_code=500, detail="Error al insertar el documento.")
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Este ejercicio ya existe.")

def get_exercise_url(exercise):
    for confirmedExercise in exercise.exercise:
        for key, value in confirmedExercise.items():
            if hasattr(value, 'url'):
                url = value.url
                return url  
    return False

def get_url_data(url, code):
    if "strava.com" in url:
        id = extract_strava_id(url)
        token = get_strava_token(code)
        
        activity_url = f"https://www.strava.com/api/v3/activities/{id}"
        headers = {'Authorization': f'Bearer {token}'}
        
        response = requests.get(activity_url, headers=headers)
        response.raise_for_status()

        stravaJson = response.json()
        stravaData = {
            "name" : stravaJson["name"],
            "distance" : stravaJson["distance"],
            "moving_time" : stravaJson["moving_time"],
            "id" : stravaJson["id"],
            "start_date_local" : stravaJson["start_date_local"],
            "calories" : stravaJson["calories"],
        }

        return stravaData
    
    else:
        return None

def extract_strava_id(stravaUrl):
    match = re.search(r"strava.com/activities/(\d+)", stravaUrl)
    if match:
        return match.group(1)  # Devuelve el ID de la actividad
    else:
        raise ValueError("URL de Strava no válida.")
    
def get_strava_token(code):
    CLIENT_ID = "142165"
    CLIENT_SECRET = "58b55e039725ca1a9d9cfcaff0e70fff0d707a00"

    token_url = "https://www.strava.com/oauth/token"
    response = requests.post(token_url, data={
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code'
    })
    
    response.raise_for_status()
    return response.json()['access_token']

def meal_check(meal):
    if not meal.dietName:
        raise HTTPException(status_code=400, detail="Nombre de la dieta no especificado.")
    if not meal.date:
        raise HTTPException(status_code=400, detail="Fecha no especificada.")
    if not meal.meal:
        raise HTTPException(status_code=400, detail="Alimentos no especificados.")
    
def exercise_check(exercise):
    if not exercise.trainingName:
        raise HTTPException(status_code=400, detail="Nombre de la rutina no especificado.")
    if not exercise.date:
        raise HTTPException(status_code=400, detail="Fecha no especificada.")
    if not exercise.exercise:
        raise HTTPException(status_code=400, detail="Ejercicios no especificados.")