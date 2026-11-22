
import os
from datetime import datetime
from decimal import Decimal

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import (
    create_engine, Column, Integer, String, Numeric,
    DateTime, ForeignKey, Text
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://stockflow:stockflow_dev_2026@localhost:5433/stockflow"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()

app = FastAPI(title="StockFlow API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# DATABASE MODELS

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    sku = Column(String(60), unique=True, nullable=True)
    category = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    price = Column(Numeric(12, 2), nullable=True)
    stock = Column(Integer, default=0, nullable=False)
    min_stock = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    movement_type = Column(String(20), nullable=False)
    quantity = Column(Integer, nullable=False)
    description = Column(String(250), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class CashMovement(Base):
    __tablename__ = "cash_movements"

    id = Column(Integer, primary_key=True, index=True)
    movement_type = Column(String(20), nullable=False)
    description = Column(String(250), nullable=False)
    category = Column(String(100), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    payment_method = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# REQUEST SCHEMAS

class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    sku: str | None = None
    category: str | None = None
    description: str | None = None
    image_url: str | None = None
    price: Decimal | None = Field(default=None, ge=0)
    stock: int = Field(default=0, ge=0)
    min_stock: int = Field(default=0, ge=0)


class StockMovementCreate(BaseModel):
    product_id: int
    movement_type: str
    quantity: int = Field(gt=0)
    description: str = Field(min_length=1, max_length=250)


class CashMovementCreate(BaseModel):
    movement_type: str
    description: str = Field(min_length=1, max_length=250)
    category: str
    amount: Decimal = Field(gt=0)
    payment_method: str


# BASIC ROUTES

@app.get("/")
def home():
    return {"message": "StockFlow API funcionando!"}


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(__import__("sqlalchemy").text("SELECT 1"))
    return {"status": "ok", "database": "connected"}


# PRODUCTS

@app.get("/products")
def list_products(db: Session = Depends(get_db)):
    products = db.query(Product).order_by(Product.id.desc()).all()
    return products


@app.post("/products")
def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    product = Product(**data.model_dump())
    db.add(product)
    try:
        db.commit()
        db.refresh(product)
        return product
    except Exception:
        db.rollback()
        raise HTTPException(400, "Não foi possível cadastrar. Verifique o código SKU.")


@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "Produto não encontrado")

    movements = db.query(StockMovement).filter(
        StockMovement.product_id == product_id
    ).first()

    if movements:
        raise HTTPException(409, "Produto possui histórico de movimentação")

    db.delete(product)
    db.commit()
    return {"message": "Produto excluído"}


# STOCK

@app.post("/stock/movements")
def create_stock_movement(
    data: StockMovementCreate,
    db: Session = Depends(get_db)
):
    if data.movement_type not in ["entrada", "saida"]:
        raise HTTPException(400, "Tipo deve ser entrada ou saida")

    product = db.query(Product).filter(
        Product.id == data.product_id
    ).with_for_update().first()

    if not product:
        raise HTTPException(404, "Produto não encontrado")

    if data.movement_type == "saida" and product.stock < data.quantity:
        raise HTTPException(400, "Estoque insuficiente")

    if data.movement_type == "entrada":
        product.stock += data.quantity
    else:
        product.stock -= data.quantity

    movement = StockMovement(**data.model_dump())
    db.add(movement)
    db.commit()
    db.refresh(movement)

    return {
        "message": "Movimentação registrada",
        "movement": movement,
        "current_stock": product.stock
    }


@app.get("/stock/movements")
def list_stock_movements(db: Session = Depends(get_db)):
    return db.query(StockMovement).order_by(
        StockMovement.id.desc()
    ).all()


# CASH

@app.post("/cash/movements")
def create_cash_movement(
    data: CashMovementCreate,
    db: Session = Depends(get_db)
):
    if data.movement_type not in ["entrada", "saida"]:
        raise HTTPException(400, "Tipo deve ser entrada ou saida")

    movement = CashMovement(**data.model_dump())
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement


@app.get("/cash/movements")
def list_cash_movements(db: Session = Depends(get_db)):
    return db.query(CashMovement).order_by(
        CashMovement.id.desc()
    ).all()


# DASHBOARD

@app.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    cash = db.query(CashMovement).all()

    entries = sum(
        (m.amount for m in cash if m.movement_type == "entrada"),
        Decimal("0")
    )
    exits = sum(
        (m.amount for m in cash if m.movement_type == "saida"),
        Decimal("0")
    )

    return {
        "total_products": len(products),
        "total_stock": sum(p.stock for p in products),
        "low_stock": sum(
            1 for p in products if p.stock <= p.min_stock
        ),
        "cash_entries": entries,
        "cash_exits": exits,
        "cash_balance": entries - exits
    }
