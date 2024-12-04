from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from src.model.model import Diet, Food

client = MongoClient("mongodb+srv://tfgmarcaranda:foodstock@food-stock-cluster.lpjtt.mongodb.net/food_stock?retryWrites=true&w=majority&appName=food-stock-cluster")
db = client["foodstock"]
collection = db["diet"]
collection.create_index("name", unique=True)
collection.create_index("favorite", unique=True, partialFilterExpression={"favorite": True})

router = APIRouter()

# Custom serializer para ObjectId
def serialize_document(document):
    return {**document, "_id": str(document["_id"])}

@router.get("/diet")
async def get_diet():
    diets = []
    for doc in collection.find().sort("order", 1):
        diets.append(serialize_document(doc))
    return {"diets": diets}

@router.get("/diet/{name}")
async def get_diet(name: str):
    try:
      diet = collection.find_one({"name": name})
      return {"diet": serialize_document(diet)}
    except:
      raise HTTPException(status_code=404, detail="Dieta no encontrada.")
    
@router.get("/diet/favorite/{bool}")
async def get_favorite_diet(bool: bool):
    try:
        diet = collection.find_one({"favorite": bool})
        return {"diet": serialize_document(diet)}
    except:
        raise HTTPException(status_code=404, detail="No hay ninguna dieta favorita.")
    
@router.post("/diet")
async def add_diet(diet: Diet):
    try:
        diet_check(diet)
        totalFood = get_total_food(diet.days)
        order = get_diet_order()
        
        diet_dict = diet.dict()
        diet_dict["totalFood"] = totalFood
        diet_dict["order"] = order
        diet_dict["favorite"] = False
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
    result = collection.update_one({"name": diet.name}, {"$set": diet_dict})
    if result.modified_count == 1:
        return {"message": "Dieta actualizada."}
    else:
        raise HTTPException(status_code=404, detail="Dieta no encontrada.")
    
@router.put("/diet/changeOrder/{dietName}/{newOrder}")
async def change_diet_order(dietName: str, newOrder: int):
    diet = collection.find_one({"name": dietName})
    diet2 = collection.find_one({"order": newOrder})
    if diet and diet2:
        currentOrder = diet["order"]

        result = collection.update_one({"name": dietName}, {"$set": {"order": newOrder}})
        result2 = collection.update_one({"name": diet2["name"]}, {"$set": {"order": currentOrder}})

        if result.modified_count == 1 and result2.modified_count == 1:
            return {"message": "Orden de dieta actualizado."}
        else:
            raise HTTPException(status_code=500, detail="Error al actualizar el orden de la dieta.")
    else:
        raise HTTPException(status_code=404, detail="Dieta no encontrada.")
    
def diet_check(diet: Diet):    
    for day in diet.days:
        for meal in diet.days[day]:
            for food_dict in diet.days[day][meal]:
                for key, food in food_dict.items():
                    food.name = food.name.capitalize()

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
                    existing_food = next((f for f in totalFood if f["name"] == food.name), None)
                    if existing_food:
                        existing_food["quantity"] += food.quantity
                    else:
                        new_food = Food(name=food.name, quantity=food.quantity, unit=food.unit)
                        totalFood.append(new_food.dict())
    return totalFood

def get_diet_order():
    max_order = collection.find_one({}, sort=[("order", -1)])
    return max_order["order"] + 1 if max_order else 1