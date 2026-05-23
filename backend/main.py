from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.compute import router as compute_router
from api.frontier import router as frontier_router
from api.config import router as config_router
from api.health import router as health_router

app = FastAPI(title="Portfolio Analytics API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(compute_router)
app.include_router(frontier_router)
app.include_router(config_router)
app.include_router(health_router)
