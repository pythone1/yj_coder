"""
项目名称: llm-chatbot
技术领域: 03-llm-agents
模块说明: auth.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

from sqlite3 import IntegrityError

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user, require_admin
from app.models.schemas import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    UpdateUserRoleRequest,
    UserProfile,
)
from app.services.user_store import UserStore

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest) -> AuthResponse:
    store = UserStore()
    try:
        user = store.create_user(payload.email, payload.password)
    except IntegrityError as exc:
        raise HTTPException(status_code=400, detail="该邮箱已注册") from exc
    token = store.issue_token(user["id"])
    return AuthResponse(token=token, user=UserProfile(**user))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    store = UserStore()
    user = store.authenticate(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    token = store.issue_token(user["id"])
    return AuthResponse(token=token, user=UserProfile(**user))


@router.get("/me", response_model=UserProfile)
def me(current_user: dict = Depends(get_current_user)) -> UserProfile:
    return UserProfile(**current_user)


@router.get("/admin/users", response_model=list[UserProfile])
def list_users(current_user: dict = Depends(require_admin)) -> list[UserProfile]:
    users = UserStore().list_users()
    return [UserProfile(**item) for item in users]


@router.patch("/admin/users/{user_id}", response_model=UserProfile)
def update_user_role(
    user_id: str,
    payload: UpdateUserRoleRequest,
    current_user: dict = Depends(require_admin),
) -> UserProfile:
    store = UserStore()
    updated = store.set_admin(user_id, payload.is_admin, actor_user_id=current_user["id"])
    if not updated:
        raise HTTPException(status_code=404, detail="用户不存在")
    return UserProfile(**updated)
