from pydantic import BaseModel
from typing import List, Dict

class Food(BaseModel):
    name: str
    quantity: int
    measure: str

class Diet(BaseModel):
    name: str
    days: Dict[str, Dict[str, List[Dict[str, Food]]]]