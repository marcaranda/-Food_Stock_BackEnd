from pydantic import BaseModel
from typing import List, Dict

class Food(BaseModel):
    name: str
    quantity: int
    unit: str

class Diet(BaseModel):
    name: str
    days: Dict[str, Dict[str, List[Dict[str, Food]]]]
    favorite: bool

class Meal(BaseModel):
    date: str
    meal: Dict[str, List[Dict[str, Food]]]

class Exercise(BaseModel):
    name: str
    type: str
    information: str

class Training(BaseModel):
    name: str
    days: Dict[str, Dict[str, Exercise]]
    favorite: bool

class ConfirmedExercise(BaseModel):
    date: str
    exercise : Dict[str, Exercise]