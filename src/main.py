from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.service.stock import router as stock_router
from src.service.diet import router as diet_router
from src.service.meal import router as meal_router
from src.service.training import router as training_router
from src.service.exercise import router as exercise_router
from src.service.confirmDay import router as confirmDay_router

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
app.include_router(meal_router, tags=["Meal"])
app.include_router(training_router, tags=["Training"])
app.include_router(exercise_router, tags=["Exercise"])
app.include_router(confirmDay_router, tags=["ConfirmDay"])