
from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_session
from app.models.models import (
    Product,
    Sku,
    Location,
    InventoryBalance,
    InventoryMovement,
)

app = FastAPI(
    title="Unified Inventory Management System",
    description="APIs for products, SKUs, locations, and inventory movements.",
    version="1.0.0",
)

# Allow the React frontend to communicate with FastAPI.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------
# Request schemas
# -------------------------

class ProductCreate(BaseModel):
    product_id: str
    name: str
    description: str | None = None
    category: str | None = None
    brand: str | None = None


class SkuCreate(BaseModel):
    sku_id: str
    product_id: str
    barcode: str | None = None
    variant: str | None = None
    unit_cost: Decimal = Field(default=Decimal("0"), ge=0)
    unit_price: Decimal = Field(default=Decimal("0"), ge=0)
    active_from: date | None = None
    status: str = "ACTIVE"


class LocationCreate(BaseModel):
    location_id: str
    name: str
    location_type: str
    city: str | None = None
    region: str | None = None
    ships_online: bool = False


class MovementCreate(BaseModel):
    sku_id: str
    location_id: str
    movement_type: str
    quantity: int = Field(gt=0)
    idempotency_key: str


# -------------------------
# Helpers
# -------------------------

def model_dict(obj):
    """Convert a SQLAlchemy object to a dictionary."""
    return {
        column.name: getattr(obj, column.name)
        for column in obj.__table__.columns
    }


def get_inventory_balance(
    db: Session,
    sku_id: str,
    location_id: str,
):
    return (
        db.query(InventoryBalance)
        .filter(
            InventoryBalance.sku_id == sku_id,
            InventoryBalance.location_id == location_id,
        )
        .with_for_update()
        .first()
    )


# -------------------------
# Health endpoints
# -------------------------

@app.get("/")
def root():
    return {
        "message": "Unified Inventory Management System API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


# -------------------------
# Products
# -------------------------

@app.get("/products")
def list_products(db: Session = Depends(get_session)):
    products = db.query(Product).all()
    return [model_dict(product) for product in products]


@app.post("/products", status_code=201)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_session),
):
    product = Product(**payload.model_dump())
    db.add(product)

    try:
        db.commit()
        db.refresh(product)
        return {
            "message": "Product created",
            "product_id": product.product_id,
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Product could not be created. Check for duplicate IDs or invalid references.",
        )


# -------------------------
# SKUs
# -------------------------

@app.get("/skus")
def list_skus(db: Session = Depends(get_session)):
    skus = db.query(Sku).all()
    return [model_dict(sku) for sku in skus]


@app.post("/skus", status_code=201)
def create_sku(
    payload: SkuCreate,
    db: Session = Depends(get_session),
):
    sku = Sku(**payload.model_dump())
    db.add(sku)

    try:
        db.commit()
        db.refresh(sku)
        return {
            "message": "SKU created",
            "sku_id": sku.sku_id,
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="SKU could not be created. Check its IDs and product reference.",
        )


# -------------------------
# Locations
# -------------------------

@app.get("/locations")
def list_locations(db: Session = Depends(get_session)):
    locations = db.query(Location).all()
    return [model_dict(location) for location in locations]


@app.post("/locations", status_code=201)
def create_location(
    payload: LocationCreate,
    db: Session = Depends(get_session),
):
    location = Location(**payload.model_dump())
    db.add(location)

    try:
        db.commit()
        db.refresh(location)
        return {
            "message": "Location created",
            "location_id": location.location_id,
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Location could not be created. Check for duplicate IDs or invalid fields.",
        )


# -------------------------
# Inventory
# -------------------------

@app.get("/inventory")
def list_inventory(db: Session = Depends(get_session)):
    balances = db.query(InventoryBalance).all()
    result = []

    for balance in balances:
        sku = (
            db.query(Sku)
            .filter(Sku.sku_id == balance.sku_id)
            .first()
        )

        product = None
        if sku:
            product = (
                db.query(Product)
                .filter(Product.product_id == sku.product_id)
                .first()
            )

        location = (
            db.query(Location)
            .filter(Location.location_id == balance.location_id)
            .first()
        )

        on_hand = int(balance.on_hand_qty or 0)
        reserved = int(balance.reserved_qty or 0)
        blocked = int(balance.blocked_qty or 0)
        in_transit = int(balance.in_transit_qty or 0)

        result.append({
            "sku_id": balance.sku_id,
            "product_name": (
                getattr(product, "name", None)
                or getattr(product, "product_name", None)
                or balance.sku_id
            ),
            "location_id": balance.location_id,
            "location_name": (
                getattr(location, "name", None)
                if location else balance.location_id
            ),
            "on_hand_qty": on_hand,
            "reserved_qty": reserved,
            "blocked_qty": blocked,
            "available_qty": max(0, on_hand - reserved - blocked),
            "in_transit_qty": in_transit,
        })

    return result


# -------------------------
# Inventory movements
# -------------------------

@app.post("/inventory/movements", status_code=201)
def create_inventory_movement(
    payload: MovementCreate,
    db: Session = Depends(get_session),
):
    movement_type = payload.movement_type.upper()

    allowed_types = {
        "RECEIPT",
        "SALE",
        "ADJUSTMENT",
    }

    if movement_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Supported movement types: RECEIPT, SALE, ADJUSTMENT.",
        )

    # Prevent duplicate submissions with the same idempotency key.
    existing = (
        db.query(InventoryMovement)
        .filter(
            InventoryMovement.idempotency_key
            == payload.idempotency_key
        )
        .first()
    )

    if existing:
        return {
            "message": "Movement already recorded",
            "movement_id": existing.movement_id,
            "movement_type": existing.movement_type,
            "quantity_change": existing.quantity_change,
        }

    sku = (
        db.query(Sku)
        .filter(Sku.sku_id == payload.sku_id)
        .first()
    )
    if not sku:
        raise HTTPException(status_code=404, detail="SKU not found")

    location = (
        db.query(Location)
        .filter(Location.location_id == payload.location_id)
        .first()
    )
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    balance = get_inventory_balance(
        db,
        payload.sku_id,
        payload.location_id,
    )

    if balance is None:
        balance = InventoryBalance(
            sku_id=payload.sku_id,
            location_id=payload.location_id,
            on_hand_qty=0,
            reserved_qty=0,
            blocked_qty=0,
            in_transit_qty=0,
        )
        db.add(balance)
        db.flush()

    if movement_type == "RECEIPT":
        quantity_change = payload.quantity
    elif movement_type == "SALE":
        quantity_change = -payload.quantity
    else:
        # Adjustment adds the submitted quantity.
        quantity_change = payload.quantity

    current_qty = int(balance.on_hand_qty or 0)

    if movement_type == "SALE" and current_qty < payload.quantity:
        raise HTTPException(
            status_code=400,
            detail="Insufficient stock for this sale.",
        )

    balance.on_hand_qty = current_qty + quantity_change

    movement = InventoryMovement(
        sku_id=payload.sku_id,
        location_id=payload.location_id,
        movement_type=movement_type,
        quantity_change=quantity_change,
        idempotency_key=payload.idempotency_key,
    )

    db.add(movement)

    try:
        db.commit()
        db.refresh(movement)

        return {
            "message": "Stock movement recorded",
            "movement_id": movement.movement_id,
            "movement_type": movement_type,
            "quantity_change": quantity_change,
            "on_hand_qty": balance.on_hand_qty,
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Movement could not be saved. Check the request and idempotency key.",
        )
