from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.service.stock import router as stock_router
from src.service.diet import router as diet_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Tu URL del frontend
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos HTTP
    allow_headers=["*"],  # Permite todos los encabezados
)

# Incluir rutas desde routes.py
app.include_router(stock_router, tags=["Stock"])
app.include_router(diet_router, tags=["Diet"])
