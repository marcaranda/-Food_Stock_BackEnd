from pydantic import BaseModel
from typing import List, Dict, Optional

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
    information: Optional[str]

class Training(BaseModel):
    name: str
    days: Dict[str, Dict[str, Exercise]]
    favorite: bool

class ExerciseConfirmed(BaseModel):
    name: str
    type: str
    information: Optional[str]
    duration: Optional[str]
    intensity: Optional[str]
    url: Optional[str]


class ConfirmedExercise(BaseModel):
    trainingName: str
    date: str
    exercise: Dict[str, ExerciseConfirmed]