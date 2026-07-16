from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, engine, get_db

# 应用启动时自动建表（简单项目够用；生产建议用 Alembic 做迁移）
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="物品管理 CRUD API",
    description="一个用于演示 Docker 部署的 FastAPI + Vue 增删改查项目",
    version="1.0.0",
)

# 允许跨域：开发时 Vue 直接访问后端，生产时经 Nginx 反代同源也不受影响。
# 简单项目用 "*"；生产建议收窄到具体域名。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["健康检查"])
def root():
    """根路径，用来确认服务是否存活。"""
    return {"message": "服务运行中，访问 /docs 查看接口文档"}


@app.get("/health", tags=["健康检查"])
def health():
    """健康检查接口，供 Docker / 负载均衡探活使用。"""
    return {"status": "ok"}


@app.post(
    "/api/items",
    response_model=schemas.ItemOut,
    status_code=status.HTTP_201_CREATED,
    tags=["物品"],
)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    """新增一个物品。"""
    db_item = models.Item(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@app.get("/api/items", response_model=list[schemas.ItemOut], tags=["物品"])
def list_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """分页查询物品列表。"""
    return db.query(models.Item).offset(skip).limit(limit).all()


@app.get("/api/items/{item_id}", response_model=schemas.ItemOut, tags=["物品"])
def get_item(item_id: int, db: Session = Depends(get_db)):
    """根据 ID 查询单个物品。"""
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="物品不存在")
    return db_item


@app.put("/api/items/{item_id}", response_model=schemas.ItemOut, tags=["物品"])
def update_item(
    item_id: int, item: schemas.ItemUpdate, db: Session = Depends(get_db)
):
    """更新物品信息，只更新传入的字段。"""
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="物品不存在")

    update_data = item.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)

    db.commit()
    db.refresh(db_item)
    return db_item


@app.delete(
    "/api/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["物品"],
)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    """删除物品。"""
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="物品不存在")
    db.delete(db_item)
    db.commit()
    return None
