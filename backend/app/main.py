
import os
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import (
    create_engine, Column, Integer, String, Numeric,
    DateTime, ForeignKey, Text, text
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session


# CONFIGURATION

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://stockflow:stockflow_dev_2026@localhost:5433/stockflow"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False
)
Base = declarative_base()

app = FastAPI(title="StockFlow API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CENT = Decimal("0.01")


def money(value):
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


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
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
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


# NEW SALES TABLES

class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    gross_total = Column(Numeric(12, 2), nullable=False)
    discount = Column(Numeric(12, 2), default=0, nullable=False)
    total = Column(Numeric(12, 2), nullable=False)
    seller_name = Column(String(150), default="Não informado", nullable=False)
    status = Column(String(20), default="concluida", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    product_name = Column(String(150), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False)


class SalePayment(Base):
    __tablename__ = "sale_payments"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    payment_method = Column(String(50), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    fee_amount = Column(Numeric(12, 2), default=0, nullable=False)
    net_amount = Column(Numeric(12, 2), nullable=False)


# Creates new tables without deleting existing data.
Base.metadata.create_all(bind=engine)
# Existing databases were created with product_id required. Allow custom sale
# items to be stored without linking them to an inventory product.
with engine.begin() as connection:
    connection.execute(text(
        "ALTER TABLE sale_items ALTER COLUMN product_id DROP NOT NULL"
    ))
    connection.execute(text(
        "ALTER TABLE sales ADD COLUMN IF NOT EXISTS seller_name VARCHAR(150) "
        "NOT NULL DEFAULT 'Não informado'"
    ))


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


class SaleItemCreate(BaseModel):
    # Item do estoque: product_id. Item avulso/serviço: product_name + unit_price.
    product_id: int | None = None
    product_name: str | None = Field(default=None, min_length=1, max_length=150)
    unit_price: Decimal | None = Field(default=None, ge=0)
    quantity: int = Field(gt=0)


class SalePaymentCreate(BaseModel):
    payment_method: str = Field(min_length=1, max_length=50)
    amount: Decimal = Field(gt=0)
    fee_amount: Decimal = Field(default=Decimal("0"), ge=0)


class SaleCreate(BaseModel):
    items: list[SaleItemCreate] = Field(min_length=1)
    seller_name: str = Field(default="Não informado", min_length=1, max_length=150)
    discount: Decimal = Field(default=Decimal("0"), ge=0)
    payments: list[SalePaymentCreate] = Field(min_length=1)


# SERIALIZATION

def sale_to_dict(sale, db):
    items = db.query(SaleItem).filter(
        SaleItem.sale_id == sale.id
    ).all()

    payments = db.query(SalePayment).filter(
        SalePayment.sale_id == sale.id
    ).all()

    return {
        "id": sale.id,
        "gross_total": sale.gross_total,
        "discount": sale.discount,
        "total": sale.total,
        "seller_name": sale.seller_name,
        "status": sale.status,
        "created_at": sale.created_at,
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "subtotal": item.subtotal
            }
            for item in items
        ],
        "payments": [
            {
                "id": payment.id,
                "payment_method": payment.payment_method,
                "amount": payment.amount,
                "fee_amount": payment.fee_amount,
                "net_amount": payment.net_amount
            }
            for payment in payments
        ]
    }


# BASIC ROUTES

@app.get("/")
def home():
    return {"message": "StockFlow API funcionando!"}


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}


# PRODUCTS

@app.get("/products")
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).order_by(Product.id.desc()).all()


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
        raise HTTPException(
            400,
            "Não foi possível cadastrar. Verifique o código SKU."
        )


@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(404, "Produto não encontrado")

    movements = db.query(StockMovement).filter(
        StockMovement.product_id == product_id
    ).first()

    sold = db.query(SaleItem).filter(
        SaleItem.product_id == product_id
    ).first()

    if movements or sold:
        raise HTTPException(
            409,
            "Produto possui histórico de movimentação ou vendas."
        )

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

    try:
        with db.begin():
            product = db.query(Product).filter(
                Product.id == data.product_id
            ).with_for_update().first()

            if not product:
                raise HTTPException(404, "Produto não encontrado")

            if data.movement_type == "saida":
                if product.stock < data.quantity:
                    raise HTTPException(400, "Estoque insuficiente")
                product.stock -= data.quantity
            else:
                product.stock += data.quantity

            movement = StockMovement(**data.model_dump())
            db.add(movement)
            db.flush()

            result = {
                "id": movement.id,
                "product_id": product.id,
                "movement_type": movement.movement_type,
                "quantity": movement.quantity,
                "current_stock": product.stock
            }

        return {
            "message": "Movimentação registrada",
            "movement": result,
            "current_stock": result["current_stock"]
        }

    except HTTPException:
        raise


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


# SALES

@app.post("/sales")
def create_sale(data: SaleCreate, db: Session = Depends(get_db)):
    try:
        with db.begin():
            # Lock only registered products. Custom items/services do not affect stock.
            product_ids = sorted(set(
                item.product_id for item in data.items
                if item.product_id is not None
            ))

            locked_products = []
            if product_ids:
                locked_products = db.query(Product).filter(
                    Product.id.in_(product_ids)
                ).order_by(Product.id).with_for_update().all()

            products = {product.id: product for product in locked_products}
            if len(products) != len(product_ids):
                raise HTTPException(404, "Um ou mais produtos não foram encontrados.")

            quantities = {}
            for item in data.items:
                if item.product_id is not None:
                    quantities[item.product_id] = (
                        quantities.get(item.product_id, 0) + item.quantity
                    )
                elif not item.product_name or item.unit_price is None:
                    raise HTTPException(
                        400,
                        "Para vender sem estoque, informe o nome e o preço unitário."
                    )

            for product_id, quantity in quantities.items():
                if products[product_id].stock < quantity:
                    raise HTTPException(
                        400, f"Estoque insuficiente para {products[product_id].name}."
                    )

            sale_items = []
            gross_total = Decimal("0.00")
            for item in data.items:
                if item.product_id is not None:
                    product = products[item.product_id]
                    if product.price is None:
                        raise HTTPException(
                            400, f"O produto {product.name} não possui preço cadastrado."
                        )
                    product_name = product.name
                    unit_price = money(product.price)
                else:
                    product_name = item.product_name.strip()
                    unit_price = money(item.unit_price)
                    if unit_price <= 0:
                        raise HTTPException(400, "O preço unitário deve ser maior que zero.")

                subtotal = money(unit_price * item.quantity)
                gross_total += subtotal
                sale_items.append({
                    "product_id": item.product_id,
                    "product_name": product_name,
                    "quantity": item.quantity,
                    "unit_price": unit_price,
                    "subtotal": subtotal
                })

            gross_total = money(gross_total)
            discount = money(data.discount)
            if discount >= gross_total:
                raise HTTPException(400, "O desconto deve ser menor que o valor bruto.")
            total = money(gross_total - discount)

            payment_total = money(sum(
                (money(payment.amount) for payment in data.payments),
                Decimal("0.00")
            ))
            if payment_total != total:
                raise HTTPException(
                    400,
                    f"Os pagamentos somam R$ {payment_total}, "
                    f"mas o total da venda é R$ {total}."
                )

            allowed_methods = {
                "Dinheiro", "Pix", "Cartão de crédito", "Cartão de débito",
                "Transferência", "Outros"
            }
            for payment in data.payments:
                if payment.payment_method not in allowed_methods:
                    raise HTTPException(
                        400, f"Forma de pagamento inválida: {payment.payment_method}"
                    )
                if money(payment.fee_amount) > money(payment.amount):
                    raise HTTPException(400, "A taxa não pode ser maior que o pagamento.")

            sale = Sale(
                gross_total=gross_total,
                discount=discount,
                total=total,
                seller_name=data.seller_name.strip() or "Não informado",
                status="concluida"
            )
            db.add(sale)
            db.flush()

            for item_data in sale_items:
                db.add(SaleItem(sale_id=sale.id, **item_data))

            # Only inventory products are deducted and recorded as stock movements.
            for product_id, quantity in quantities.items():
                product = products[product_id]
                product.stock -= quantity
                db.add(StockMovement(
                    product_id=product_id,
                    movement_type="saida",
                    quantity=quantity,
                    description=f"Venda #{sale.id}"
                ))

            for payment in data.payments:
                amount = money(payment.amount)
                fee = money(payment.fee_amount)
                net_amount = money(amount - fee)
                db.add(SalePayment(
                    sale_id=sale.id,
                    payment_method=payment.payment_method,
                    amount=amount,
                    fee_amount=fee,
                    net_amount=net_amount
                ))
                if net_amount > 0:
                    db.add(CashMovement(
                        movement_type="entrada",
                        description=f"Venda #{sale.id}",
                        category="Venda",
                        amount=net_amount,
                        payment_method=payment.payment_method
                    ))

            db.flush()
            sale_id = sale.id

        saved_sale = db.query(Sale).filter(Sale.id == sale_id).first()
        return sale_to_dict(saved_sale, db)

    except HTTPException:
        raise


@app.get("/sales")
def list_sales(db: Session = Depends(get_db)):
    sales = db.query(Sale).order_by(
        Sale.id.desc()
    ).all()

    return [sale_to_dict(sale, db) for sale in sales]


@app.get("/sales/{sale_id}")
def get_sale(sale_id: int, db: Session = Depends(get_db)):
    sale = db.query(Sale).filter(
        Sale.id == sale_id
    ).first()

    if not sale:
        raise HTTPException(404, "Venda não encontrada")

    return sale_to_dict(sale, db)


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
