"""
项目名称: llm-chatbot
技术领域: 03-llm-agents
模块说明: deps.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.services.user_store import UserStore

security = HTTPBearer(auto_error=False)


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> dict:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="未登录")
    user = UserStore().get_user_by_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="登录已失效")
    return user


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="只有管理员可以执行该操作")
    return current_user
