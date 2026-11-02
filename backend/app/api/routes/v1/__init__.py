from fastapi import APIRouter

from .datasets import router as datasets_router
from .experiments import router as experiments_router
from .playground import router as playground_router
from .results import router as results_router

v1_router = APIRouter()
v1_router.include_router(datasets_router, tags=["datasets"])
v1_router.include_router(experiments_router, tags=["experiments"])
v1_router.include_router(results_router, tags=["results"])
v1_router.include_router(playground_router, tags=["playground"])
