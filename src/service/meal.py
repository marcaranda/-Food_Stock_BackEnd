from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from src.model.model import Meal

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
        if meal:
            return {"meal": serialize_document(meal)}
        else:
            return {"meal": {"date": date, "meals": []}}
    except:
        raise HTTPException(status_code=404, detail="Comida no encontrada.")
    
@router.put("/meal")
async def add_meal(fullMeal: Meal):
    try:
        meal_check(fullMeal)

        meal_dict = fullMeal.dict(exclude={'date'})
        result = collection.update_one({"date": fullMeal.date}, {"$addToSet": {"meals": meal_dict}}, upsert=True
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