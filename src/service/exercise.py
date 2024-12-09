from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from src.model.model import ConfirmedExercise

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
async def add_confirmedExercise(fullConfirmedExercise: ConfirmedExercise):
    try:
        confirmedExercise_check(fullConfirmedExercise)

        confirmedExercise_dict = fullConfirmedExercise.dict(exclude={'date'})
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