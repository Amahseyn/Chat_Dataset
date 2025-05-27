from fastapi import APIRouter
from api.v1.property_routes import router as property_router
from api.v1.chat_route import router as chat_router
from api.v1 import routes, chat_route, property_routes, query_routes, auth_routes

router = APIRouter()
router.include_router(property_router, prefix="/properties", tags=["Properties"])
router.include_router(chat_router, prefix="/chat", tags=["Chat"])
router.include_router(auth_routes.router, prefix="/auth", tags=["Auth"])