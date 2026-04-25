from fastapi import APIRouter

from app.api.v1 import admin_dashboard, auth, datasets, jobs, models, rag, training, user_settings

api_v1 = APIRouter(prefix="/api/v1")

api_v1.include_router(auth.router)
api_v1.include_router(auth.admin_router)
api_v1.include_router(auth.users_router)
api_v1.include_router(user_settings.router)
api_v1.include_router(admin_dashboard.router)
api_v1.include_router(jobs.router)
api_v1.include_router(rag.router)
api_v1.include_router(models.router)
api_v1.include_router(datasets.router)
api_v1.include_router(training.router)
