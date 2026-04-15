from fastapi import APIRouter, Depends
from schemas.schema import PotionCreate, PotionUpdate
from services import service
from db.db import get_db

router = APIRouter()


@router.post("/potions")
def create_potion(potion: PotionCreate, db=Depends(get_db)):
    return service.create_potion(db, potion)


@router.patch("/potions/{potion_id}")
def update_potion(potion_id: int, update: PotionUpdate, db=Depends(get_db)):
    return service.update_potion(db, potion_id, update)


@router.delete("/potions/{potion_id}")
def delete_potion(potion_id: int, db=Depends(get_db)):
    return service.delete_potion(db, potion_id)


@router.get("/potions")
def get_potions(db=Depends(get_db)):
    return service.get_potions(db)


@router.get("/potions/{potion_id}")
def get_potion(potion_id: int, db=Depends(get_db)):
    return service.get_potion(db, potion_id)
