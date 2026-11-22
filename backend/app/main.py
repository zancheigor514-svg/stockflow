
import os
from pathlib import Path
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import quote_plus

from fastapi import FastAPI, Depends, HTTPException, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import (
    create_engine, Column, Integer, String, Numeric, LargeBinary,
    DateTime, Date, ForeignKey, Text, text, or_, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
from starlette.responses import Response


# CONFIGURATION

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT / "backend" / ".env", override=False)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    db_user = quote_plus(os.getenv("POSTGRES_USER", "stockflow"))
    db_password = quote_plus(os.getenv("POSTGRES_PASSWORD", "stockflow_dev_2026"))
    db_name = quote_plus(os.getenv("POSTGRES_DB", "stockflow"))
    db_port = os.getenv("POSTGRES_PORT", "5433")
    DATABASE_URL = f"postgresql://{db_user}:{db_password}@localhost:{db_port}/{db_name}"

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
    installments = Column(Integer, default=1, nullable=False)
    fee_amount = Column(Numeric(12, 2), default=0, nullable=False)
    net_amount = Column(Numeric(12, 2), nullable=False)


class StoreProfile(Base):
    __tablename__ = "store_profile"

    id = Column(Integer, primary_key=True)
    store_name = Column(String(150), nullable=False, default="StockFlow")
    logo_data = Column(LargeBinary, nullable=True)
    logo_content_type = Column(String(50), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SellerOption(Base):
    __tablename__ = "seller_options"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), unique=True, nullable=False)


class CreditCustomer(Base):
    __tablename__ = "credit_customers"

    id = Column(Integer, primary_key=True, index=True)
    cpf = Column(String(11), unique=True, nullable=False, index=True)
    rg = Column(String(30), nullable=False)
    full_name = Column(String(150), nullable=False)
    address = Column(String(500), nullable=False)
    document_photo_data = Column(LargeBinary, nullable=True)
    document_photo_type = Column(String(50), nullable=True)
    person_photo_data = Column(LargeBinary, nullable=True)
    person_photo_type = Column(String(50), nullable=True)
    residence_proof_data = Column(LargeBinary, nullable=True)
    residence_proof_type = Column(String(50), nullable=True)
    observations = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class CreditContract(Base):
    __tablename__ = "credit_contracts"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("credit_customers.id"), nullable=False, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False, unique=True)
    installment_count = Column(Integer, nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(20), default="em_aberto", nullable=False)


class CreditInstallment(Base):
    __tablename__ = "credit_installments"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("credit_contracts.id"), nullable=False, index=True)
    installment_number = Column(Integer, nullable=False)
    due_date = Column(Date, nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(20), default="pendente", nullable=False)
    paid_at = Column(DateTime, nullable=True)
    interest_paid = Column(Numeric(12, 2), default=0, nullable=False)


class CreditReceipt(Base):
    __tablename__ = "credit_receipts"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("credit_customers.id"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    interest_amount = Column(Numeric(12, 2), default=0, nullable=False)
    payment_method = Column(String(50), nullable=False)
    paid_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class CreditReceiptItem(Base):
    __tablename__ = "credit_receipt_items"
    __table_args__ = (UniqueConstraint("installment_id", name="uq_credit_receipt_installment"),)

    id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(Integer, ForeignKey("credit_receipts.id"), nullable=False, index=True)
    installment_id = Column(Integer, ForeignKey("credit_installments.id"), nullable=False)
    principal_amount = Column(Numeric(12, 2), nullable=False)
    interest_amount = Column(Numeric(12, 2), default=0, nullable=False)


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


    connection.execute(text(
        "ALTER TABLE sale_payments ADD COLUMN IF NOT EXISTS installments INTEGER "
        "NOT NULL DEFAULT 1"
    ))
    for column in (
        "document_photo_data", "document_photo_type", "person_photo_data",
        "person_photo_type", "residence_proof_data", "residence_proof_type"
    ):
        connection.execute(text(
            f"ALTER TABLE credit_customers ALTER COLUMN {column} DROP NOT NULL"
        ))

with SessionLocal() as db:
    for seller_name in ("Loja", "Luana"):
        if not db.query(SellerOption).filter(SellerOption.name.ilike(seller_name)).first():
            db.add(SellerOption(name=seller_name))
    db.commit()


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
    installments: int = Field(default=1, ge=1, le=120)
    fee_amount: Decimal = Field(default=Decimal("0"), ge=0)


class CreditSaleTerms(BaseModel):
    customer_id: int = Field(gt=0)
    installment_count: int = Field(ge=1, le=120)
    upfront_amount: Decimal = Field(default=Decimal("0"), ge=0)
    upfront_payment_method: str | None = None
    upfront_card_installments: int = Field(default=1, ge=1, le=36)


class SaleCreate(BaseModel):
    items: list[SaleItemCreate] = Field(min_length=1)
    seller_name: str = Field(default="Não informado", min_length=1, max_length=150)
    discount: Decimal = Field(default=Decimal("0"), ge=0)
    payments: list[SalePaymentCreate] = Field(min_length=1)
    credit_terms: CreditSaleTerms | None = None


class CreditCollectionCreate(BaseModel):
    customer_id: int = Field(gt=0)
    installment_ids: list[int] = Field(min_length=1)
    payment_method: str = Field(min_length=1, max_length=50)


def normalize_cpf(value):
    digits = "".join(character for character in value if character.isdigit())
    if len(digits) != 11 or len(set(digits)) == 1:
        return None
    first = sum(int(digits[i]) * (10 - i) for i in range(9))
    first_digit = (first * 10) % 11
    first_digit = 0 if first_digit == 10 else first_digit
    second = sum(int(digits[i]) * (11 - i) for i in range(10))
    second_digit = (second * 10) % 11
    second_digit = 0 if second_digit == 10 else second_digit
    if digits[-2:] != f"{first_digit}{second_digit}":
        return None
    return digits


def local_business_date():
    return datetime.now().date()


def overdue_interest(principal, due_date, as_of=None):
    as_of = as_of or local_business_date()
    late_days = max(0, (as_of - due_date).days)
    interest = money(Decimal(principal) * Decimal("0.01") * Decimal(late_days) / Decimal("30"))
    return late_days, interest


def split_amount_into_installments(total, count):
    total_cents = int((money(total) * 100).to_integral_value())
    if count < 1 or count > total_cents:
        raise HTTPException(400, "Cada parcela precisa ter pelo menos R$ 0,01.")
    cents, remainder = divmod(total_cents, count)
    return [
        money(Decimal(cents + (1 if i < remainder else 0)) / Decimal("100"))
        for i in range(count)
    ]


async def read_credit_photo(upload, label):
    if not upload or not upload.filename:
        return None, None
    if upload.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(400, f"A foto de {label} deve ser JPG, PNG ou WebP.")
    data = await upload.read(5 * 1024 * 1024 + 1)
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(400, f"A foto de {label} deve ter no máximo 5 MB.")
    valid_signature = (
        (upload.content_type == "image/png" and data.startswith(b"\x89PNG\r\n\x1a\n")) or
        (upload.content_type == "image/jpeg" and data.startswith(b"\xff\xd8\xff")) or
        (upload.content_type == "image/webp" and len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP")
    )
    if not valid_signature:
        raise HTTPException(400, f"O arquivo de {label} não é uma imagem válida.")
    return data, upload.content_type


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
                "installments": payment.installments,
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


@app.get("/store/profile")
def get_store_profile(db: Session = Depends(get_db)):
    profile = db.query(StoreProfile).filter(StoreProfile.id == 1).first()
    if not profile:
        return {"store_name": "StockFlow", "has_logo": False, "updated_at": None}
    return {
        "store_name": profile.store_name,
        "has_logo": profile.logo_data is not None,
        "updated_at": profile.updated_at
    }


@app.put("/store/profile")
async def update_store_profile(
    store_name: str = Form(...),
    logo: UploadFile | None = File(default=None),
    remove_logo: bool = Form(default=False),
    db: Session = Depends(get_db)
):
    store_name = store_name.strip()
    if not store_name or len(store_name) > 150:
        raise HTTPException(400, "O nome da loja deve ter entre 1 e 150 caracteres.")

    profile = db.query(StoreProfile).filter(StoreProfile.id == 1).first()
    if not profile:
        profile = StoreProfile(id=1, store_name=store_name)
        db.add(profile)
    profile.store_name = store_name

    if remove_logo:
        profile.logo_data = None
        profile.logo_content_type = None
    elif logo and logo.filename:
        allowed_types = {"image/png", "image/jpeg", "image/webp"}
        if logo.content_type not in allowed_types:
            raise HTTPException(400, "Envie uma imagem PNG, JPG ou WebP.")
        logo_data = await logo.read(3 * 1024 * 1024 + 1)
        if len(logo_data) > 3 * 1024 * 1024:
            raise HTTPException(400, "A imagem deve ter no máximo 3 MB.")
        valid_signature = (
            (logo.content_type == "image/png" and logo_data.startswith(b"\x89PNG\r\n\x1a\n")) or
            (logo.content_type == "image/jpeg" and logo_data.startswith(b"\xff\xd8\xff")) or
            (logo.content_type == "image/webp" and len(logo_data) >= 12 and logo_data[:4] == b"RIFF" and logo_data[8:12] == b"WEBP")
        )
        if not valid_signature:
            raise HTTPException(400, "O conteúdo enviado não corresponde a uma imagem válida.")
        profile.logo_data = logo_data
        profile.logo_content_type = logo.content_type

    db.commit()
    db.refresh(profile)
    return {
        "store_name": profile.store_name,
        "has_logo": profile.logo_data is not None,
        "updated_at": profile.updated_at
    }


@app.get("/store/logo")
def get_store_logo(db: Session = Depends(get_db)):
    profile = db.query(StoreProfile).filter(StoreProfile.id == 1).first()
    if not profile or not profile.logo_data or not profile.logo_content_type:
        raise HTTPException(404, "A loja ainda não possui logotipo.")
    return Response(
        content=profile.logo_data,
        media_type=profile.logo_content_type,
        headers={"Cache-Control": "no-cache"}
    )


# CREDIT CUSTOMERS

@app.get("/sellers")
def list_sellers(db: Session = Depends(get_db)):
    return db.query(SellerOption).order_by(SellerOption.name).all()


@app.post("/sellers")
def create_seller(data: dict, db: Session = Depends(get_db)):
    name = str(data.get("name", "")).strip()
    if not name or len(name) > 150:
        raise HTTPException(400, "O nome da vendedora deve ter entre 1 e 150 caracteres.")
    if db.query(SellerOption).filter(SellerOption.name.ilike(name)).first():
        raise HTTPException(409, "Essa vendedora já está cadastrada.")
    seller = SellerOption(name=name)
    db.add(seller)
    try:
        db.commit()
        db.refresh(seller)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Essa vendedora já está cadastrada.")
    return seller


@app.put("/sellers/{seller_id}")
def update_seller(seller_id: int, data: dict, db: Session = Depends(get_db)):
    seller = db.query(SellerOption).filter(SellerOption.id == seller_id).first()
    if not seller:
        raise HTTPException(404, "Vendedora não encontrada.")
    name = str(data.get("name", "")).strip()
    if not name or len(name) > 150:
        raise HTTPException(400, "O nome da vendedora deve ter entre 1 e 150 caracteres.")
    duplicate = db.query(SellerOption).filter(
        SellerOption.id != seller_id, SellerOption.name.ilike(name)
    ).first()
    if duplicate:
        raise HTTPException(409, "Essa vendedora já está cadastrada.")
    seller.name = name
    try:
        db.commit()
        db.refresh(seller)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Essa vendedora já está cadastrada.")
    return seller


@app.delete("/sellers/{seller_id}")
def delete_seller(seller_id: int, db: Session = Depends(get_db)):
    seller = db.query(SellerOption).filter(SellerOption.id == seller_id).first()
    if not seller:
        raise HTTPException(404, "Vendedora não encontrada.")
    db.delete(seller)
    db.commit()
    return {"message": "Vendedora removida."}

def credit_customer_to_dict(customer):
    return {
        "id": customer.id,
        "cpf": customer.cpf,
        "rg": customer.rg,
        "full_name": customer.full_name,
        "address": customer.address,
        "observations": customer.observations,
        "has_document_photo": customer.document_photo_data is not None,
        "has_person_photo": customer.person_photo_data is not None,
        "has_residence_proof": customer.residence_proof_data is not None,
        "created_at": customer.created_at
    }


def validate_customer_fields(cpf, rg, full_name, address):
    normalized_cpf = normalize_cpf(cpf)
    if not normalized_cpf:
        raise HTTPException(400, "Informe um CPF válido.")
    rg = rg.strip()
    full_name = full_name.strip()
    address = address.strip()
    if not rg or len(rg) > 30:
        raise HTTPException(400, "Informe um RG válido, com até 30 caracteres.")
    if not full_name or len(full_name) > 150:
        raise HTTPException(400, "Informe o nome completo, com até 150 caracteres.")
    if not address or len(address) > 500:
        raise HTTPException(400, "Informe o endereço completo, com até 500 caracteres.")
    return normalized_cpf, rg, full_name, address


@app.get("/credit/customers")
def list_credit_customers(q: str = "", db: Session = Depends(get_db)):
    query = db.query(CreditCustomer)
    search = q.strip()
    if search:
        cpf_search = "".join(character for character in search if character.isdigit())
        query = query.filter(or_(
            CreditCustomer.full_name.ilike(f"%{search}%"),
            CreditCustomer.cpf.ilike(f"%{cpf_search}%") if cpf_search else text("false")
        ))
    customers = query.order_by(CreditCustomer.id.desc()).limit(100).all()
    return [credit_customer_to_dict(customer) for customer in customers]


@app.post("/credit/customers")
async def create_credit_customer(
    cpf: str = Form(...),
    rg: str = Form(...),
    full_name: str = Form(...),
    address: str = Form(...),
    observations: str = Form(default=""),
    document_photo: UploadFile | None = File(default=None),
    person_photo: UploadFile | None = File(default=None),
    residence_proof: UploadFile | None = File(default=None),
    db: Session = Depends(get_db)
):
    cpf, rg, full_name, address = validate_customer_fields(cpf, rg, full_name, address)
    if db.query(CreditCustomer.id).filter(CreditCustomer.cpf == cpf).first():
        raise HTTPException(409, "Já existe um cliente cadastrado com esse CPF.")
    document_data, document_type = await read_credit_photo(document_photo, "documento")
    person_data, person_type = await read_credit_photo(person_photo, "pessoa")
    residence_data, residence_type = await read_credit_photo(residence_proof, "comprovante de residência")
    customer = CreditCustomer(
        cpf=cpf,
        rg=rg,
        full_name=full_name,
        address=address,
        observations=observations.strip() or None,
        document_photo_data=document_data,
        document_photo_type=document_type,
        person_photo_data=person_data,
        person_photo_type=person_type,
        residence_proof_data=residence_data,
        residence_proof_type=residence_type
    )
    db.add(customer)
    try:
        db.commit()
        db.refresh(customer)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Já existe um cliente cadastrado com esse CPF.")
    return credit_customer_to_dict(customer)


@app.put("/credit/customers/{customer_id}")
async def update_credit_customer(
    customer_id: int,
    cpf: str = Form(...),
    rg: str = Form(...),
    full_name: str = Form(...),
    address: str = Form(...),
    observations: str = Form(default=""),
    document_photo: UploadFile | None = File(default=None),
    person_photo: UploadFile | None = File(default=None),
    residence_proof: UploadFile | None = File(default=None),
    db: Session = Depends(get_db)
):
    customer = db.query(CreditCustomer).filter(CreditCustomer.id == customer_id).first()
    if not customer:
        raise HTTPException(404, "Cliente não encontrado.")
    cpf, rg, full_name, address = validate_customer_fields(cpf, rg, full_name, address)
    duplicate = db.query(CreditCustomer.id).filter(
        CreditCustomer.cpf == cpf, CreditCustomer.id != customer_id
    ).first()
    if duplicate:
        raise HTTPException(409, "Já existe outro cliente cadastrado com esse CPF.")

    customer.cpf = cpf
    customer.rg = rg
    customer.full_name = full_name
    customer.address = address
    customer.observations = observations.strip() or None
    for upload, data_attr, type_attr, label in [
        (document_photo, "document_photo_data", "document_photo_type", "documento"),
        (person_photo, "person_photo_data", "person_photo_type", "pessoa"),
        (residence_proof, "residence_proof_data", "residence_proof_type", "comprovante de residência")
    ]:
        if upload and upload.filename:
            photo_data, photo_type = await read_credit_photo(upload, label)
            setattr(customer, data_attr, photo_data)
            setattr(customer, type_attr, photo_type)
    try:
        db.commit()
        db.refresh(customer)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Já existe outro cliente cadastrado com esse CPF.")
    return credit_customer_to_dict(customer)


@app.get("/credit/customers/{customer_id}/documents/{document_kind}")
def get_credit_customer_document(
    customer_id: int,
    document_kind: str,
    db: Session = Depends(get_db)
):
    customer = db.query(CreditCustomer).filter(CreditCustomer.id == customer_id).first()
    if not customer:
        raise HTTPException(404, "Cliente não encontrado.")
    documents = {
        "identity": (customer.document_photo_data, customer.document_photo_type),
        "person": (customer.person_photo_data, customer.person_photo_type),
        "residence": (customer.residence_proof_data, customer.residence_proof_type)
    }
    if document_kind not in documents:
        raise HTTPException(404, "Documento não encontrado.")
    content, content_type = documents[document_kind]
    if not content or not content_type:
        raise HTTPException(404, "Este documento ainda não foi enviado.")
    return Response(content=content, media_type=content_type, headers={"Cache-Control": "no-store"})


@app.get("/credit/customers/{customer_id}/account")
def get_credit_customer_account(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(CreditCustomer).filter(CreditCustomer.id == customer_id).first()
    if not customer:
        raise HTTPException(404, "Cliente não encontrado.")
    as_of = local_business_date()
    contracts = db.query(CreditContract).filter(
        CreditContract.customer_id == customer_id
    ).order_by(CreditContract.id.desc()).all()
    contract_data = []
    for contract in contracts:
        installments = db.query(CreditInstallment).filter(
            CreditInstallment.contract_id == contract.id
        ).order_by(CreditInstallment.installment_number).all()
        installment_data = []
        for installment in installments:
            days_late, interest = overdue_interest(installment.amount, installment.due_date, as_of)
            installment_data.append({
                "id": installment.id,
                "installment_number": installment.installment_number,
                "due_date": installment.due_date,
                "amount": installment.amount,
                "status": installment.status,
                "display_status": "atrasada" if installment.status == "pendente" and days_late > 0 else installment.status,
                "days_late": days_late,
                "interest_due": interest if installment.status == "pendente" else Decimal("0.00"),
                "total_due": money(installment.amount + interest) if installment.status == "pendente" else Decimal("0.00"),
                "interest_paid": installment.interest_paid,
                "paid_at": installment.paid_at
            })
        contract_data.append({
            "id": contract.id,
            "sale_id": contract.sale_id,
            "installment_count": contract.installment_count,
            "total_amount": contract.total_amount,
            "status": contract.status,
            "created_at": contract.created_at,
            "installments": installment_data
        })

    receipts = db.query(CreditReceipt).filter(
        CreditReceipt.customer_id == customer_id
    ).order_by(CreditReceipt.id.desc()).all()
    receipt_data = []
    for receipt in receipts:
        allocations = db.query(CreditReceiptItem).filter(
            CreditReceiptItem.receipt_id == receipt.id
        ).all()
        receipt_data.append({
            "id": receipt.id,
            "amount": receipt.amount,
            "interest_amount": receipt.interest_amount,
            "payment_method": receipt.payment_method,
            "paid_at": receipt.paid_at,
            "installments_paid": len(allocations)
        })
    return {
        "customer": credit_customer_to_dict(customer),
        "contracts": contract_data,
        "receipts": receipt_data
    }


@app.post("/credit/payments")
def collect_credit_payment(data: CreditCollectionCreate, db: Session = Depends(get_db)):
    allowed_methods = {
        "Dinheiro", "Pix", "Cartão de crédito", "Cartão de débito", "Transferência", "Outros"
    }
    if data.payment_method not in allowed_methods:
        raise HTTPException(400, "Forma de pagamento inválida para quitar parcelas.")
    if len(set(data.installment_ids)) != len(data.installment_ids):
        raise HTTPException(400, "A lista contém parcelas repetidas.")

    try:
        with db.begin():
            customer = db.query(CreditCustomer).filter(
                CreditCustomer.id == data.customer_id
            ).first()
            if not customer:
                raise HTTPException(404, "Cliente não encontrado.")

            installments = db.query(CreditInstallment).join(
                CreditContract, CreditContract.id == CreditInstallment.contract_id
            ).filter(
                CreditContract.customer_id == data.customer_id,
                CreditInstallment.id.in_(data.installment_ids)
            ).order_by(CreditInstallment.id).with_for_update().all()
            if len(installments) != len(data.installment_ids):
                raise HTTPException(404, "Uma ou mais parcelas não pertencem a este cliente.")
            if any(installment.status != "pendente" for installment in installments):
                raise HTTPException(409, "Uma ou mais parcelas já foram pagas.")

            paid_at = datetime.utcnow()
            as_of = local_business_date()
            interest_by_id = {}
            total_interest = Decimal("0.00")
            total_amount = Decimal("0.00")
            for installment in installments:
                _, interest = overdue_interest(installment.amount, installment.due_date, as_of)
                interest_by_id[installment.id] = interest
                total_interest += interest
                total_amount += money(installment.amount + interest)
            total_interest = money(total_interest)
            total_amount = money(total_amount)

            receipt = CreditReceipt(
                customer_id=customer.id,
                amount=total_amount,
                interest_amount=total_interest,
                payment_method=data.payment_method,
                paid_at=paid_at
            )
            db.add(receipt)
            db.flush()

            contract_ids = set()
            for installment in installments:
                interest = interest_by_id[installment.id]
                installment.status = "paga"
                installment.paid_at = paid_at
                installment.interest_paid = interest
                contract_ids.add(installment.contract_id)
                db.add(CreditReceiptItem(
                    receipt_id=receipt.id,
                    installment_id=installment.id,
                    principal_amount=installment.amount,
                    interest_amount=interest
                ))

            db.flush()
            for contract_id in contract_ids:
                contract = db.query(CreditContract).filter(
                    CreditContract.id == contract_id
                ).first()
                remaining = db.query(CreditInstallment.id).filter(
                    CreditInstallment.contract_id == contract_id,
                    CreditInstallment.status == "pendente"
                ).first()
                if contract and not remaining:
                    contract.status = "quitado"

            db.add(CashMovement(
                movement_type="entrada",
                description=f"Pagamento crediário cliente #{customer.id} - recibo #{receipt.id}",
                category="Crediário",
                amount=total_amount,
                payment_method=data.payment_method
            ))
            db.flush()
            result = {
                "receipt_id": receipt.id,
                "customer_id": customer.id,
                "amount": total_amount,
                "interest_amount": total_interest,
                "installments_paid": len(installments)
            }
        return result
    except HTTPException:
        raise


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

            credit_schedule = []
            credit_upfront_amount = Decimal("0.00")
            credit_balance = Decimal("0.00")
            credit_customer = None
            terms = data.credit_terms
            credit_rows = [payment for payment in data.payments if payment.payment_method == "Crediário"]
            if terms:
                credit_customer = db.query(CreditCustomer).filter(
                    CreditCustomer.id == terms.customer_id
                ).first()
                if not credit_customer:
                    raise HTTPException(404, "Cliente do crediário não encontrado.")
                credit_upfront_amount = money(terms.upfront_amount)
                if credit_upfront_amount < 0 or credit_upfront_amount >= total:
                    raise HTTPException(400, "O valor de entrada precisa ser menor que o total da venda.")
                credit_balance = money(total - credit_upfront_amount)
                credit_schedule = split_amount_into_installments(credit_balance, terms.installment_count)
                if len(credit_rows) != 1 or money(credit_rows[0].amount) != credit_balance:
                    raise HTTPException(400, "O valor do crediário não corresponde às parcelas em aberto.")
                if credit_rows[0].installments != terms.installment_count:
                    raise HTTPException(400, "A quantidade de parcelas do crediário não corresponde ao contrato.")
                immediate_rows = [payment for payment in data.payments if payment.payment_method != "Crediário"]
                if credit_upfront_amount > 0:
                    if terms.upfront_payment_method not in {
                        "Dinheiro", "Pix", "Cartão de crédito", "Cartão de débito", "Transferência", "Outros"
                    }:
                        raise HTTPException(400, "Informe como o pagamento inicial foi recebido.")
                    if len(immediate_rows) != 1 or immediate_rows[0].payment_method != terms.upfront_payment_method:
                        raise HTTPException(400, "O pagamento inicial não corresponde ao crediário informado.")
                    if (
                        terms.upfront_payment_method == "Cartão de crédito"
                        and immediate_rows[0].installments != terms.upfront_card_installments
                    ):
                        raise HTTPException(400, "A quantidade de parcelas do cartão inicial não corresponde ao valor informado.")
                    if money(immediate_rows[0].amount) != credit_upfront_amount:
                        raise HTTPException(400, "O pagamento inicial não corresponde ao valor informado.")
                elif immediate_rows:
                    raise HTTPException(400, "Há um pagamento inicial sem parcelas pagas na hora.")
            elif credit_rows:
                raise HTTPException(400, "Informe cliente e condições para vender no crediário.")

            allowed_methods = {
                "Crediário",
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
                if payment.installments > 1 and payment.payment_method not in {"Cartão de crédito", "Crediário"}:
                    raise HTTPException(400, "A quantidade de parcelas só se aplica ao cartão de crédito ou crediário.")
                if payment.payment_method == "Cartão de crédito" and payment.installments > 36:
                    raise HTTPException(400, "O cartão de crédito permite até 36 parcelas.")
                if payment.payment_method == "Crediário" and money(payment.fee_amount) != 0:
                    raise HTTPException(400, "O crediário não pode ter taxa de cartão.")

            sale = Sale(
                gross_total=gross_total,
                discount=discount,
                total=total,
                seller_name=data.seller_name.strip() or "Não informado",
                status="concluida"
            )
            db.add(sale)
            db.flush()

            if terms:
                contract = CreditContract(
                    customer_id=credit_customer.id,
                    sale_id=sale.id,
                    installment_count=terms.installment_count,
                    total_amount=credit_balance,
                    status="em_aberto"
                )
                db.add(contract)
                db.flush()
                sale_date = local_business_date()
                credit_installments = []
                sale_paid_at = datetime.utcnow()
                for index, installment_amount in enumerate(credit_schedule, start=1):
                    installment = CreditInstallment(
                        contract_id=contract.id,
                        installment_number=index,
                        due_date=sale_date + timedelta(days=30 * index),
                        amount=installment_amount,
                        status="pendente",
                        paid_at=None,
                        interest_paid=Decimal("0.00")
                    )
                    credit_installments.append(installment)
                    db.add(installment)
                db.flush()

                if credit_upfront_amount > 0:
                    upfront_receipt = CreditReceipt(
                        customer_id=credit_customer.id,
                        amount=credit_upfront_amount,
                        interest_amount=Decimal("0.00"),
                        payment_method=terms.upfront_payment_method,
                        paid_at=sale_paid_at
                    )
                    db.add(upfront_receipt)

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
                    installments=payment.installments,
                    fee_amount=fee,
                    net_amount=net_amount
                ))
                if net_amount > 0 and payment.payment_method != "Crediário":
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
