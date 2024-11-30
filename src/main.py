from fastapi import FastAPI

from src.service.stock import router as stock_router
from src.service.diet import router as diet_router

app = FastAPI()

# Incluir rutas desde routes.py
app.include_router(stock_router, tags=["Stock"])
app.include_router(diet_router, tags=["Diet"])
