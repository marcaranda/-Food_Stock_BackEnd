from pydantic import BaseModel
from typing import List, Dict

class Food(BaseModel):
    name: str
    quantity: int
    unit: str

class Diet(BaseModel):
    name: str
    days: Dict[str, Dict[str, List[Dict[str, Food]]]]

class Meal(BaseModel):
    date: str
    meal: str

class MealBD(BaseModel):
    date: str
    meals: List[str]