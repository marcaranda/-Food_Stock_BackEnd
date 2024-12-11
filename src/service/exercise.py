from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from src.model.model import ConfirmedExercise
import re, requests, json

client = MongoClient("mongodb+srv://tfgmarcaranda:foodstock@food-stock-cluster.lpjtt.mongodb.net/food_stock?retryWrites=true&w=majority&appName=food-stock-cluster")
db = client["foodstock"]
collection = db["confirmedExercise"]
collection.create_index("date", unique=True)

router = APIRouter()

# Custom serializer para ObjectId
def serialize_document(document):
    return {**document, "_id": str(document["_id"])}
            
@router.get("/confirmedExercise")
async def get_confirmedExercise():
    confirmedExercises = []
    for doc in collection.find():
        confirmedExercises.append(serialize_document(doc))
    return {"confirmedExercises": confirmedExercises}

@router.get("/confirmedExercise/{date}")
async def get_confirmedExercise(date: str):
    try:
        confirmedExercise = collection.find_one({"date": date})
        if confirmedExercise:
            return {"confirmedExercise": serialize_document(confirmedExercise)}
        else:
            return {"confirmedExercise": {"date": date, "exercises": []}}
    except:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado.")

@router.put("/confirmedExercise")
async def add_confirmedExercise(code: str, fullConfirmedExercise: ConfirmedExercise):
    try:
        confirmedExercise_check(fullConfirmedExercise)
        
        exercise_url = get_exercise_url(fullConfirmedExercise)
        if exercise_url:
            activity_data = get_url_data(exercise_url, code)

        confirmedExercise_dict = fullConfirmedExercise.dict(exclude={'date'})
        confirmedExercise_dict["urlData"] = activity_data
        result = collection.update_one({"date": fullConfirmedExercise.date}, {"$addToSet": {"exercises": confirmedExercise_dict}}, upsert=True
        )

        if result.acknowledged:
            return {"message": "Ejercicio añadido.", "id": str(result.upserted_id)}
        else:
            raise HTTPException(status_code=500, detail="Error al insertar el documento.")
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Este ejercicio ya existe.")

def confirmedExercise_check(confirmedExercise):
  if not confirmedExercise.date:
      raise HTTPException(status_code=400, detail="Fecha no especificada.")
  if not confirmedExercise.exercise:
      raise HTTPException(status_code=400, detail="Ejercicio no especificado.")
  
def get_exercise_url(confirmedExercise):
    for key, value in confirmedExercise.exercise.items():
        if hasattr(value, 'url'):
            url = value.url
            return url
    else:
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