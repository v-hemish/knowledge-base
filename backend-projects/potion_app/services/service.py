from models.model import Potion
from schemas.schema import PotionCreate, PotionUpdate
from sqlalchemy.orm import Session
from sqlalchemy import select


def create_potion(db: Session, potion: PotionCreate):
    db_potion = Potion(**potion.model_dump())
    db.add(db_potion)
    db.commit()
    db.refresh(db_potion)
    return db_potion


def update_potion(db: Session, potion_id: int, update: PotionUpdate):
    db_potion = get_potion(db, potion_id)

    if db_potion is None:
        return None

    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_potion, key, value)
    db.commit()
    db.refresh(db_potion)
    return db_potion


def delete_potion(db: Session, potion_id: int):
    db_potion = get_potion(db, potion_id)
    if db_potion is None:
        return None
    db.delete(db_potion)
    db.commit()
    return db_potion


def get_potions(db: Session):
    statement = select(Potion)
    result = db.execute(statement)
    return result.scalars().all()


def get_potion(db: Session, potion_id: int):
    statement = select(Potion).where(Potion.id == potion_id)
    result = db.execute(statement)
    return result.scalar_one_or_none()
