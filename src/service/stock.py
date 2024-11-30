from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
from pymongo.errors import DuplicateKeyError
from src.model.model import Food 


client = MongoClient("mongodb+srv://tfgmarcaranda:foodstock@food-stock-cluster.lpjtt.mongodb.net/food_stock?retryWrites=true&w=majority&appName=food-stock-cluster")
db = client["foodstock"]
collection = db["stock"]
collection.create_index("name", unique=True)

router = APIRouter()

# Custom serializer para ObjectId
def serialize_document(document):
    return {**document, "_id": str(document["_id"])}

@router.get("/stock")
async def get_stock():
    stocks = []
    for doc in collection.find():
        stocks.append(serialize_document(doc))
    return {"stocks": stocks}

@router.post("/stock")
async def add_stock(food: Food):
    try:
        stock_check(food)
        totalFood = get_total_food(food.days)
        
        result = collection.insert_one(food.dict())
        if result.acknowledged:
            return {"message": "Alimento añadido.", "id": str(result.inserted_id)}
        else:
            raise HTTPException(status_code=500, detail="Error al insertar el documento.")
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Este Alimento ya existe.")
    
@router.delete("/stock/{name}")
async def delete_stock(name: str):
    result = collection.delete_one({"name": name})
    if result.deleted_count == 1:
        return {"message": "Alimento eliminado."}
    else:
        raise HTTPException(status_code=404, detail="Alimento no encontrado.")
    
@router.put("/stock")
async def update_stock(food: Food):
    stock_check(food)
    totalFood = get_total_food(food.days)
    
    result = collection.update_one({"name": food.name}, {"$set": food.dict()})
    if result.modified_count == 1:
        return {"message": "Alimento actualizado."}
    else:
        raise HTTPException(status_code=404, detail="Stock no encontrado.")
    
def stock_check(food: Food):
    if (food.quantity < 0):
        raise HTTPException(status_code=400, detail="La cantidad no puede ser negativa.")
    
    if (food.measure not in ["g", "u"]):
        raise HTTPException(status_code=400, detail="La medida debe ser 'g' o 'u'.")

    return True

def get_total_food(days):
    totalFood = []

    for day in days:
        for meal in days[day]:
            for food in days[day][meal]:
                if (food["name"] not in totalFood):
                    totalFood.append([food["name"], food["quantity"], food["measure"]])
                else:
                    for updateFood in totalFood:
                        if (updateFood[0] == food["name"]):
                            updateFood[1] += food["quantity"]
    return totalFood