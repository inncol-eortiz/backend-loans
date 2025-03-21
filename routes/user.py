"""
This module defines the Routes Users
"""

from fastapi import HTTPException, Depends, Request
from sqlalchemy.orm import Session
from typing import List
import crud.users
import config.db
import models.user
import schemas.user

from .base_url import protected_route
from config.rate_limit import limiter


models.user.Base.metadata.create_all(bind=config.db.engine)


def get_db():
    db = config.db.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@protected_route.get("/users", response_model=List[schemas.user.User], tags=["Users"])
@limiter.limit("100/minute")
async def read_users(request: Request, skip: int = 0, db: Session = Depends(get_db)):
    db_users = crud.users.get_users(db=db, skip=skip)
    return db_users


@protected_route.get(
    "/users/active", response_model=List[schemas.user.User], tags=["Users"]
)
@limiter.limit("100/minute")
async def read_active_users(
    request: Request, skip: int = 0, db: Session = Depends(get_db)
):
    db_users = crud.users.get_active_users(db=db, skip=skip)
    return db_users


@protected_route.get("/users/{id}", response_model=schemas.user.User, tags=["Users"])
async def read_user(id: int, db: Session = Depends(get_db)):
    db_user = crud.users.get_user(db=db, id=id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@protected_route.post("/users", response_model=schemas.user.User, tags=["Users"])
def create_user(user: schemas.user.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.users.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.users.create_user(db=db, user=user)


@protected_route.put("/users/{id}", response_model=schemas.user.User, tags=["Users"])
async def update_user(
    id: int, user: schemas.user.UserUpdate, db: Session = Depends(get_db)
):
    db_user = crud.users.update_user(db=db, id=id, user=user)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@protected_route.delete("/users/{id}", response_model=schemas.user.User, tags=["Users"])
async def delete_user(id: int, db: Session = Depends(get_db)):
    try:
        db_user = crud.users.delete_user(db=db, id=id)
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return db_user
    except HTTPException as e:
        if e.status_code == 400 and "active loans" in e.detail:
            raise HTTPException(
                status_code=400, detail="User has active loans and cannot be deleted"
            )
        else:
            raise e
