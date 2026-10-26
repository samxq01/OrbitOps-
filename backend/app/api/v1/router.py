"""API v1 master router aggregating all sub-routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import health

api_v1_router = APIRouter()
api_v1_router.include_router(health.router, tags=["Health"])
