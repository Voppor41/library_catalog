from fastapi import APIRouter, status

from ..schemas.user import TokenResponse, UserCreate, UserLogin, UserPublic
from ...dependencies import AuthServiceDep


router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, service: AuthServiceDep):
    return await service.create_user(data)

@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, service: AuthServiceDep):
    return await service.login_user(data)