from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from src.model.model import Training, Exercise

client = MongoClient("mongodb+srv://tfgmarcaranda:foodstock@food-stock-cluster.lpjtt.mongodb.net/food_stock?retryWrites=true&w=majority&appName=food-stock-cluster")
db = client["foodstock"]
collection = db["training"]
collection.create_index("name", unique=True)

router = APIRouter()

# Custom serializer para ObjectId
def serialize_document(document):
    return {**document, "_id": str(document["_id"])}

@router.get("/training")
async def get_training():
    trainings = []
    for doc in collection.find().sort("order", 1):
        trainings.append(serialize_document(doc))
    return {"trainings": trainings}

@router.get("/training/{name}")
async def get_training(name: str):
    try:
      training = collection.find_one({"name": name})
      return {"training": serialize_document(training)}
    except:
      raise HTTPException(status_code=404, detail="Entrenamiento no encontrado.")
    
@router.get("/training/favorite/{bool}")
async def get_favorite_training(bool: bool):
    try:
        training = collection.find_one({"favorite": bool})
        return {"training": serialize_document(training)}
    except:
        raise HTTPException(status_code=404, detail="No hay ningun entrenamiento favorito.")
            
@router.post("/training")
async def add_training(training: Training):
    try:
        #training_check(training)
        order = get_training_order()

        if (order == 1):
            training.favorite = True
        
        training_dict = training.dict()
        training_dict["order"] = order
        result = collection.insert_one(training_dict)

        if training.favorite:
            collection.update_many({"favorite": True}, {"$set": {"favorite": False}})

        if result.acknowledged:
            return {"message": "Entrenamiento añadido.", "id": str(result.inserted_id)}
        else:
            raise HTTPException(status_code=500, detail="Error al insertar el documento.")
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Este entrenamiento ya existe.")
    
@router.delete("/training/{name}")
async def delete_training(name: str):
    result = collection.delete_one({"name": name})
    if result.deleted_count == 1:
        return {"message": "Entrenamiento eliminado."}
    else:
        raise HTTPException(status_code=404, detail="Entrenamiento no encontrado.")
    
@router.put("/training")
async def update_training(training: Training):
    try:
        training_check(training)
        result = collection.update_one({"name": training.name}, {"$set": training.dict()})
        
        if training.favorite:
          collection.update_many({"favorite": True}, {"$set": {"favorite": False}})

        if result.modified_count == 1:
            return {"message": "Entrenamiento actualizado."}
        else:
            raise HTTPException(status_code=404, detail="Entrenamiento no encontrado.")
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Este entrenamiento ya existe.")
    
@router.put("/training/changeOrder/{trainingName}/{newOrder}")
async def change_training_order(trainingName: str, newOrder: int):
    training = collection.find_one({"name": trainingName})
    training2 = collection.find_one({"order": newOrder})
    if training and training2:
        currentOrder = training["order"]

        result = collection.update_one({"name": trainingName}, {"$set": {"order": newOrder}})
        result2 = collection.update_one({"name": training2["name"]}, {"$set": {"order": currentOrder}})

        if result.modified_count == 1 and result2.modified_count == 1:
            return {"message": "Orden cambiado."}
        else:
            raise HTTPException(status_code=500, detail="Error al cambiar el orden.")
    else:
        raise HTTPException(status_code=404, detail="Entrenamiento no encontrado.")
    
def training_check(training: Training):
    for day in training.days:
        for session in training.days[day]:
            if not isinstance(training.days[day][session], Exercise):
                raise HTTPException(status_code=400, detail="El ejercicio no es valido.")
                
    return True

def get_training_order():
    try:
        result = collection.find().sort("order", -1).limit(1)
        order = next(result, {}).get("order", 0)
        return order + 1
    except Exception as e:
        return 1