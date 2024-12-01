from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
from pymongo.errors import DuplicateKeyError
from src.model.model import Diet

client = MongoClient("mongodb+srv://tfgmarcaranda:foodstock@food-stock-cluster.lpjtt.mongodb.net/food_stock?retryWrites=true&w=majority&appName=food-stock-cluster")
db = client["foodstock"]
collection = db["diet"]
collection.create_index("name", unique=True)

router = APIRouter()

# Custom serializer para ObjectId
def serialize_document(document):
    return {**document, "_id": str(document["_id"])}

@router.get("/diet/{name}")
async def get_diet(name: str):
    try:
      diet = collection.find.one({"name": name})
      return {"diet": serialize_document(diet)}
    except:
      raise HTTPException(status_code=404, detail="Dieta no encontrada.")
    
@router.post("/diet")
async def add_diet(diet: Diet):
    try:
        diet_check(diet)
        totalFood = get_total_food(diet.days)
        
        diet_dict = diet.dict()
        diet_dict["totalFood"] = totalFood
        result = collection.insert_one(diet_dict)
        if result.acknowledged:
            return {"message": "Dieta añadida.", "id": str(result.inserted_id)}
        else:
            raise HTTPException(status_code=500, detail="Error al insertar el documento.")
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Esta dieta ya existe.")
    
@router.delete("/diet/{name}")
async def delete_diet(name: str):
    result = collection.delete_one({"name": name})
    if result.deleted_count == 1:
        return {"message": "Dieta eliminada."}
    else:
        raise HTTPException(status_code=404, detail="Dieta no encontrada.")
    
@router.put("/diet")
async def update_diet(diet: Diet):
    diet_check(diet)
    totalFood = get_total_food(diet.days)
    
    diet_dict = diet.dict()
    diet_dict["totalFood"] = totalFood
    result = collection.insert_one(diet_dict)
    result = collection.update_one({"name": diet.name}, {"$set": diet_dict})
    if result.modified_count == 1:
        return {"message": "Dieta actualizada."}
    else:
        raise HTTPException(status_code=404, detail="Dieta no encontrada.")
    
def diet_check(diet: Diet):    
    for day in diet.days:
        for meal in diet.days[day]:
            for food_dict in diet.days[day][meal]:
                for key, food in food_dict.items():
                    if (food.quantity < 0):
                        raise HTTPException(status_code=400, detail="La cantidad no puede ser negativa.")
                    
                    if (food.unit not in ["g", "u"]):
                        raise HTTPException(status_code=400, detail="La medida debe ser 'g' o 'u'.")
    return True

def get_total_food(days):
    totalFood = []

    for day in days:
        for meal in days[day]:
            for food_dict in days[day][meal]:
                for key, food in food_dict.items():
                    existing_food = next((f for f in totalFood if f[0] == food.name), None)
                    if existing_food:
                        existing_food[1] += food.quantity
                    else:
                        totalFood.append([food.name, food.quantity, food.unit])
    return totalFood