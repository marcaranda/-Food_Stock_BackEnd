from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from src.model.model import Meal, MealBD

client = MongoClient("mongodb+srv://tfgmarcaranda:foodstock@food-stock-cluster.lpjtt.mongodb.net/food_stock?retryWrites=true&w=majority&appName=food-stock-cluster")
db = client["foodstock"]
collection = db["meal"]
collection.create_index("date", unique=True)

router = APIRouter()

# Custom serializer para ObjectId
def serialize_document(document):
    return {**document, "_id": str(document["_id"])}
            
@router.get("/meal")
async def get_meal():
    meals = []
    for doc in collection.find():
        meals.append(serialize_document(doc))
    return {"meals": meals}
  
@router.get("/meal/{date}")
async def get_meal(date: str):
    try:
        meal = collection.find_one({"date": date})
        return {"meal": serialize_document(meal)}
    except:
        raise HTTPException(status_code=404, detail="Comida no encontrada.")
    
@router.put("/meal")
async def add_meal(meal: Meal):
    try:
        meal_check(meal)

        result = collection.update_one({"date": meal.date}, {"$addToSet": {"meals": meal.meal}}, upsert=True
        )

        if result.acknowledged:
            return {"message": "Comida añadida.", "id": str(result.upserted_id)}
        else:
            raise HTTPException(status_code=500, detail="Error al insertar el documento.")
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Esta comida ya existe.")
    
def meal_check(meal):
    if not meal.date:
        raise HTTPException(status_code=400, detail="Fecha no especificada.")
    if not meal.meal:
        raise HTTPException(status_code=400, detail="Alimentos no especificados.")