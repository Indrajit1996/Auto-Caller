from fastapi import APIRouter

from app.api.keystone.routes import (
    auth,
    groups,
    invitations,
    notifications,
    transactions,
    user_settings,
    users,
    utils,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(invitations.router)
api_router.include_router(groups.router)
api_router.include_router(user_settings.router)
api_router.include_router(notifications.router)
api_router.include_router(utils.router)
api_router.include_router(transactions.router)
