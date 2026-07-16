from pydantic import BaseModel, Field
from typing import Optional


class ItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="物品名称")
    description: Optional[str] = Field(None, max_length=500, description="物品描述")
    price: float = Field(..., ge=0, description="价格，必须大于等于 0")
    in_stock: bool = Field(True, description="是否有库存")


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[float] = Field(None, ge=0)
    in_stock: Optional[bool] = None


class ItemOut(ItemBase):
    id: int

    class Config:
        from_attributes = True
