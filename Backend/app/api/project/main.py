from fastapi import APIRouter

from app.api.endpoints import calls

api_router = APIRouter()
api_router.include_router(calls.router, prefix="/calls", tags=["calls"])
