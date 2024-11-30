from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
from pymongo.errors import DuplicateKeyError
from src.model.model import Diet

client = MongoClient("mongodb+srv://tfgmarcaranda:foodstock@food-stock-cluster.lpjtt.mongodb.net/food_stock?retryWrites=true&w=majority&appName=food-stock-cluster")
db = client["foodstock"]
collection = db["stock"]
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
        
        result = collection.insert_one(diet.dict())
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
    
    result = collection.update_one({"name": diet.name}, {"$set": diet.dict()})
    if result.modified_count == 1:
        return {"message": "Dieta actualizada."}
    else:
        raise HTTPException(status_code=404, detail="Dieta no encontrada.")
    
def diet_check(diet: Diet):
    if (diet.days != 7):
        raise HTTPException(status_code=400, detail="Número incorrecto de días.")
    
    for day in diet.days:
        for meal in diet.days[day]:
            for food in diet.days[day][meal]:
                if (food.quantity < 0):
                    raise HTTPException(status_code=400, detail="La cantidad no puede ser negativa.")
                
                if (food.measure not in ["g", "u"]):
                    raise HTTPException(status_code=400, detail="La medida debe ser 'g' o 'u'.")
    
    return True