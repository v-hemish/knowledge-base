from pydantic import BaseModel


class PotionCreate(BaseModel):
    name: str
    description: str | None = None
    price: int
    stock: int


class PotionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: int | None = None
    stock: int | None = None
