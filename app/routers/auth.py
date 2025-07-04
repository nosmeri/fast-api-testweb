from config.db import get_db
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from models.user import ChangePassword, UserCreate, UserLogin, UserResponse
from services import auth_service, jwt_service
from sqlalchemy.orm import Session
from typing import Dict, Any
from utils.deps import get_current_user, get_current_user_optional, get_refresh_token
from utils.path import templates

router = APIRouter()


# 로그인 페이지
@router.get("/login")
def login_form(
    request: Request, user: UserResponse | None = Depends(get_current_user_optional)
):
    if user:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request, "login.html")


# 로그인
@router.post("/login")
def login(user_login: UserLogin, db: Session = Depends(get_db)) -> JSONResponse:
    username = user_login.username
    password = user_login.password
    try:
        user = auth_service.authenticate_user(db, username, password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid username or password",
        )

    access_token = jwt_service.create_access_token(
        user_id=user.id, is_admin=user.is_admin, username=user.username
    )
    refresh_tocken = jwt_service.create_refresh_token(user_id=user.id, db=db)
    response = JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "success", "message": "Login successful"},
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="strict",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_tocken,
        httponly=True,
        secure=True,
        samesite="strict",
    )
    return response


# 회원가입 페이지
@router.get("/register")
def register_form(
    request: Request, user: UserResponse | None = Depends(get_current_user_optional)
):
    if user:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request, "register.html")


# 회원가입
@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)) -> JSONResponse:
    try:
        new_user = auth_service.create_user(db, user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    access_token = jwt_service.create_access_token(
        user_id=new_user.id, is_admin=new_user.is_admin, username=new_user.username
    )
    refresh_tocken = jwt_service.create_refresh_token(user_id=new_user.id, db=db)
    response = JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "status": "success",
            "message": "User created successfully",
        },
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="strict",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_tocken,
        httponly=True,
        secure=True,
        samesite="strict",
    )
    return response


# 비밀번호 변경 페이지
@router.get("/changepw")
def change_password_form(
    request: Request, user: UserResponse = Depends(get_current_user)
):
    data: Dict[str, Any] = {
        "user": {"username": user.username, "is_admin": user.is_admin}
    }

    return templates.TemplateResponse(request, "changepw.html", data)


# 비밀번호 변경
@router.post("/changepw")
def change_password(
    request: Request,
    change_password: ChangePassword,
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
) -> JSONResponse:
    if not auth_service.authenticate_user(
        db, user.username, change_password.currentPassword
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    try:
        updated_user = auth_service.change_password(
            db, user.id, change_password.newPassword
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "success", "message": "Password changed successfully"},
    )


# 로그아웃
@router.get("/logout")
def logout(
    request: Request,
    db: Session = Depends(get_db),
    refresh_token: str = Depends(get_refresh_token),
) -> RedirectResponse:
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    jwt_service.revoke_refresh_token(db, refresh_token)
    return response
