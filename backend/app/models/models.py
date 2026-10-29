"""SQLAlchemy 2.0 schema for the Unified Inventory Management System.

Conventions
- Primary keys are deterministic business IDs (see app/core/ids.py).
- Enumerations are VARCHAR + CHECK constraints (portable, easy to migrate).
- Every column carries a `comment`; docs/data_dictionary.md is generated from them.
- Quantities are integers (units, 'each'). Money is NUMERIC(12,2) in USD.
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (JSON, BigInteger, Boolean, CheckConstraint, Date, DateTime,
                        ForeignKey, Index, Integer, MetaData, Numeric, String, Text,
                        UniqueConstraint, func)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.models import enums as E
from app.models.enums import values

NAMING = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING)


def in_enum(column: str, enum_cls) -> CheckConstraint:
    vals = ", ".join(f"'{v}'" for v in values(enum_cls))
    return CheckConstraint(f"{column} IN ({vals})", name=f"{column}_valid")


def c(sqltype, doc: str, *args, **kw):
    """mapped_column with a mandatory documentation comment."""
    return mapped_column(sqltype, *args, comment=doc, **kw)


def fk(target: str, doc: str, nullable: bool = False, length: int = 20, ondelete: str = "RESTRICT"):
    return c(String(length), doc, ForeignKey(target, ondelete=ondelete), nullable=nullable)


def created():
    return mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False,
                         comment="Row creation timestamp (UTC).")


def updated():
    return mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                         nullable=False, comment="Last update timestamp (UTC).")


# =========================================================================== master data
class Product(Base):
    __tablename__ = "product"
    product_id: Mapped[str] = c(String(10), "Product ID, format PRD-000001.", primary_key=True)
    name: Mapped[str] = c(String(200), "Product display name.")
    category: Mapped[str] = c(String(80), "Merchandise category.")
    brand: Mapped[str | None] = c(String(80), "Brand name (synthetic).", nullable=True)
    description: Mapped[str | None] = c(Text, "Free-text description.", nullable=True)
    is_active: Mapped[bool] = c(Boolean, "False when the product is retired.", default=True, server_default="1")
    created_at: Mapped[datetime] = created()
    updated_at: Mapped[datetime] = updated()
    skus: Mapped[list["Sku"]] = relationship(back_populates="product")  # 1 product : N SKUs
    __table_args__ = (Index("ix_product_category", "category"),)


class Sku(Base):
    __tablename__ = "sku"
    sku_id: Mapped[str] = c(String(10), "SKU ID, format SKU-000001.", primary_key=True)
    product_id: Mapped[str] = fk("product.product_id", "Parent product.", length=10)
    barcode: Mapped[str] = c(String(20), "Synthetic EAN-13-style barcode.", unique=True)
    variant: Mapped[str | None] = c(String(80), "Variant text, e.g. 'Blue / M'.", nullable=True)
    unit_cost: Mapped[float] = c(Numeric(12, 2), "Unit cost in USD (synthetic).")
    unit_price: Mapped[float] = c(Numeric(12, 2), "List price in USD (synthetic).")
    uom: Mapped[str] = c(String(10), "Unit of measure; always 'EA' (each).", default="EA", server_default="EA")
    status: Mapped[str] = c(String(15), "Lifecycle state: ACTIVE or DISCONTINUED.", default="ACTIVE", server_default="ACTIVE")
    active_from: Mapped[date] = c(Date, "Effective start date of the SKU.")
    discontinued_on: Mapped[date | None] = c(Date, "Effective end date; NULL while active.", nullable=True)
    created_at: Mapped[datetime] = created()
    updated_at: Mapped[datetime] = updated()
    product: Mapped[Product] = relationship(back_populates="skus")
    __table_args__ = (
        in_enum("status", E.SkuStatus),
        CheckConstraint("unit_cost >= 0 AND unit_price >= 0", name="money_non_negative"),
        CheckConstraint("discontinued_on IS NULL OR discontinued_on >= active_from", name="dates_ordered"),
        Index("ix_sku_product_id", "product_id"),
    )


class Location(Base):
    __tablename__ = "location"
    location_id: Mapped[str] = c(String(10), "Location ID, format LOC-000001.", primary_key=True)
    name: Mapped[str] = c(String(120), "Location display name.")
    location_type: Mapped[str] = c(String(15), "STORE, WAREHOUSE or REGION (REGION holds no stock).")
    parent_location_id: Mapped[str | None] = fk("location.location_id", "Parent in the location hierarchy (self-reference); NULL for roots.", nullable=True, length=10)
    region: Mapped[str | None] = c(String(60), "Geographic region label.", nullable=True)
    city: Mapped[str | None] = c(String(80), "City (synthetic).", nullable=True)
    ships_online: Mapped[bool] = c(Boolean, "True if the location may fulfil online orders.", default=False, server_default="0")
    is_active: Mapped[bool] = c(Boolean, "False when closed.", default=True, server_default="1")
    created_at: Mapped[datetime] = created()
    updated_at: Mapped[datetime] = updated()
    __table_args__ = (
        in_enum("location_type", E.LocationType),
        CheckConstraint("parent_location_id IS NULL OR parent_location_id <> location_id", name="no_self_parent"),
    )


# =========================================================================== inventory core
class InventoryBalance(Base):
    """Stored, derived snapshot per (SKU, location). Must reconcile with the ledger."""
    __tablename__ = "inventory_balance"
    sku_id: Mapped[str] = c(String(10), "SKU.", ForeignKey("sku.sku_id", ondelete="RESTRICT"), primary_key=True)
    location_id: Mapped[str] = c(String(10), "Location.", ForeignKey("location.location_id", ondelete="RESTRICT"), primary_key=True)
    on_hand_qty: Mapped[int] = c(Integer, "Physical units at the location (ledger-derived).", default=0, server_default="0")
    reserved_qty: Mapped[int] = c(Integer, "Units held by PENDING/CONFIRMED reservations.", default=0, server_default="0")
    blocked_qty: Mapped[int] = c(Integer, "Units held by ACTIVE inventory blocks (damaged/quality hold).", default=0, server_default="0")
    in_transit_qty: Mapped[int] = c(Integer, "Units dispatched TO this location, not yet received (ledger-derived).", default=0, server_default="0")
    last_movement_id: Mapped[str | None] = c(String(20), "Last ledger movement applied (traceability).", nullable=True)
    version: Mapped[int] = c(Integer, "Optimistic-lock counter.", default=1, server_default="1")
    updated_at: Mapped[datetime] = updated()
    __table_args__ = (
        CheckConstraint("on_hand_qty >= 0", name="on_hand_non_negative"),
        CheckConstraint("reserved_qty >= 0", name="reserved_non_negative"),
        CheckConstraint("blocked_qty >= 0", name="blocked_non_negative"),
        CheckConstraint("in_transit_qty >= 0", name="in_transit_non_negative"),
        CheckConstraint("reserved_qty + blocked_qty <= on_hand_qty", name="holds_within_on_hand"),
        Index("ix_inventory_balance_location_id", "location_id"),
    )


class InventoryMovement(Base):
    """Immutable ledger. Rows are only ever INSERTed (UPDATE/DELETE blocked by trigger in migration)."""
    __tablename__ = "inventory_movement"
    movement_id: Mapped[str] = c(String(20), "Movement ID, format MOV-2026-00000001.", primary_key=True)
    sku_id: Mapped[str] = fk("sku.sku_id", "SKU moved.", length=10)
    location_id: Mapped[str] = fk("location.location_id", "Location whose balance changes.", length=10)
    movement_type: Mapped[str] = c(String(25), "Event type (see MovementType).")
    on_hand_delta: Mapped[int] = c(Integer, "Signed change to on_hand.", default=0, server_default="0")
    in_transit_delta: Mapped[int] = c(Integer, "Signed change to in_transit.", default=0, server_default="0")
    channel: Mapped[str | None] = c(String(15), "Sales channel where relevant (SALE/RETURN).", nullable=True)
    occurred_at: Mapped[datetime] = c(DateTime(timezone=True), "Business time the event happened.")
    recorded_at: Mapped[datetime] = created()
    reference_type: Mapped[str | None] = c(String(20), "Source record type: SHIPMENT, TRANSFER, INBOUND, ADJUSTMENT, ...", nullable=True)
    reference_id: Mapped[str | None] = c(String(30), "Source record ID (e.g. SHP-2026-000001).", nullable=True)
    reason: Mapped[str | None] = c(String(200), "Mandatory for ADJUSTMENT/DAMAGE/CORRECTION.", nullable=True)
    audit_ref: Mapped[str | None] = c(String(30), "Audit reference; mandatory for CORRECTION.", nullable=True)
    corrects_movement_id: Mapped[str | None] = fk("inventory_movement.movement_id", "Earlier movement this event compensates (never edits).", nullable=True)
    idempotency_key: Mapped[str] = c(String(80), "Unique key; duplicate submissions are rejected.", unique=True)
    __table_args__ = (
        in_enum("movement_type", E.MovementType),
        CheckConstraint("on_hand_delta <> 0 OR in_transit_delta <> 0", name="non_zero"),
        CheckConstraint("channel IS NULL OR channel IN ('STORE','WEB','MARKETPLACE')", name="channel_valid"),
        CheckConstraint("movement_type NOT IN ('ADJUSTMENT','DAMAGE','CORRECTION') OR reason IS NOT NULL", name="reason_required"),
        CheckConstraint("movement_type <> 'CORRECTION' OR audit_ref IS NOT NULL", name="audit_required"),
        Index("ix_inventory_movement_sku_loc_time", "sku_id", "location_id", "occurred_at"),
        Index("ix_inventory_movement_reference", "reference_type", "reference_id"),
        Index("ix_inventory_movement_type_time", "movement_type", "occurred_at"),
    )


class InventoryBlock(Base):
    __tablename__ = "inventory_block"
    block_id: Mapped[str] = c(String(10), "Block ID, format BLK-000001.", primary_key=True)
    sku_id: Mapped[str] = fk("sku.sku_id", "Blocked SKU.", length=10)
    location_id: Mapped[str] = fk("location.location_id", "Where the units are blocked.", length=10)
    quantity: Mapped[int] = c(Integer, "Blocked units.")
    reason: Mapped[str] = c(String(25), "DAMAGED, QUALITY_HOLD, RECALL, COUNT_DISCREPANCY.")
    status: Mapped[str] = c(String(15), "ACTIVE, RELEASED, WRITTEN_OFF.", default="ACTIVE", server_default="ACTIVE")
    blocked_at: Mapped[datetime] = c(DateTime(timezone=True), "When the block started.")
    released_at: Mapped[datetime | None] = c(DateTime(timezone=True), "When the block ended.", nullable=True)
    write_off_movement_id: Mapped[str | None] = fk("inventory_movement.movement_id", "DAMAGE movement if written off.", nullable=True)
    __table_args__ = (
        in_enum("reason", E.BlockReason),
        in_enum("status", E.BlockStatus),
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("released_at IS NULL OR released_at >= blocked_at", name="dates_ordered"),
        Index("ix_inventory_block_sku_loc", "sku_id", "location_id", "status"),
    )


class InboundSupply(Base):
    """Expected supplier receipts. Only some are ATP-eligible (see business_rules.md)."""
    __tablename__ = "inbound_supply"
    inbound_id: Mapped[str] = c(String(20), "Inbound ID, format INB-2026-000001.", primary_key=True)
    sku_id: Mapped[str] = fk("sku.sku_id", "SKU expected.", length=10)
    location_id: Mapped[str] = fk("location.location_id", "Receiving location.", length=10)
    quantity: Mapped[int] = c(Integer, "Expected units.")
    expected_at: Mapped[datetime] = c(DateTime(timezone=True), "Promised arrival time.")
    status: Mapped[str] = c(String(15), "PLANNED, CONFIRMED, RECEIVED, CANCELLED.", default="PLANNED", server_default="PLANNED")
    atp_eligible: Mapped[bool] = c(Boolean, "Policy approval flag: True only for supplier-confirmed supply.", default=False, server_default="0")
    receipt_movement_id: Mapped[str | None] = fk("inventory_movement.movement_id", "RECEIPT movement created on receipt.", nullable=True)
    created_at: Mapped[datetime] = created()
    __table_args__ = (
        in_enum("status", E.InboundStatus),
        CheckConstraint("quantity > 0", name="quantity_positive"),
        Index("ix_inbound_supply_sku_loc", "sku_id", "location_id", "status"),
    )


class ChannelBuffer(Base):
    """Per-location, per-channel quantity withheld from ATP for that channel."""
    __tablename__ = "channel_buffer"
    location_id: Mapped[str] = c(String(10), "Location.", ForeignKey("location.location_id", ondelete="RESTRICT"), primary_key=True)
    channel: Mapped[str] = c(String(15), "Channel the buffer applies to.", primary_key=True)
    effective_from: Mapped[date] = c(Date, "Effective start date.", primary_key=True)
    effective_to: Mapped[date | None] = c(Date, "Effective end date; NULL = open-ended.", nullable=True)
    buffer_pct: Mapped[float] = c(Numeric(5, 2), "Percent of (on_hand - reserved - blocked) withheld from this channel.")
    __table_args__ = (
        CheckConstraint("channel IN ('STORE','WEB','MARKETPLACE')", name="channel_valid"),
        CheckConstraint("buffer_pct >= 0 AND buffer_pct <= 100", name="pct_range"),
        CheckConstraint("effective_to IS NULL OR effective_to >= effective_from", name="dates_ordered"),
    )


class ReplenishmentRule(Base):
    __tablename__ = "replenishment_rule"
    rule_id: Mapped[str] = c(String(10), "Rule ID, format RPR-000001.", primary_key=True)
    sku_id: Mapped[str] = fk("sku.sku_id", "SKU governed.", length=10)
    location_id: Mapped[str] = fk("location.location_id", "Location governed.", length=10)
    safety_stock_qty: Mapped[int] = c(Integer, "Safety-stock buffer subtracted in ATP.")
    min_stock_qty: Mapped[int] = c(Integer, "Minimum stock; below this => low-stock flag.")
    reorder_point_qty: Mapped[int] = c(Integer, "Inventory position at/below which to reorder.")
    target_stock_qty: Mapped[int] = c(Integer, "Order-up-to level.")
    supplier_lead_time_days: Mapped[int] = c(Integer, "Supplier lead time in days.")
    supplier_name: Mapped[str | None] = c(String(120), "Synthetic supplier name.", nullable=True)
    effective_from: Mapped[date] = c(Date, "Effective start date.")
    effective_to: Mapped[date | None] = c(Date, "Effective end date; NULL = current.", nullable=True)
    __table_args__ = (
        CheckConstraint("safety_stock_qty >= 0 AND min_stock_qty >= 0", name="non_negative"),
        CheckConstraint("min_stock_qty <= reorder_point_qty AND reorder_point_qty < target_stock_qty", name="levels_ordered"),
        CheckConstraint("supplier_lead_time_days > 0", name="lead_time_positive"),
        CheckConstraint("effective_to IS NULL OR effective_to >= effective_from", name="dates_ordered"),
        UniqueConstraint("sku_id", "location_id", "effective_from", name="uq_rule_effective"),
    )


# =========================================================================== orders
class Order(Base):
    __tablename__ = "orders"  # "order" is a reserved word
    order_id: Mapped[str] = c(String(20), "Order ID, format ORD-2026-000001.", primary_key=True)
    channel: Mapped[str] = c(String(15), "STORE, WEB or MARKETPLACE.")
    customer_ref: Mapped[str] = c(String(20), "Synthetic pseudonymous customer key (no real PII).")
    status: Mapped[str] = c(String(25), "Order lifecycle state.", default="NEW", server_default="NEW")
    placed_at: Mapped[datetime] = c(DateTime(timezone=True), "When the order was placed.")
    cancelled_at: Mapped[datetime | None] = c(DateTime(timezone=True), "Cancellation time.", nullable=True)
    created_at: Mapped[datetime] = created()
    updated_at: Mapped[datetime] = updated()
    lines: Mapped[list["OrderLine"]] = relationship(back_populates="order")
    __table_args__ = (
        in_enum("status", E.OrderStatus),
        CheckConstraint("channel IN ('STORE','WEB','MARKETPLACE')", name="channel_valid"),
        CheckConstraint("cancelled_at IS NULL OR cancelled_at >= placed_at", name="dates_ordered"),
        Index("ix_orders_status_placed", "status", "placed_at"),
    )


class OrderLine(Base):
    __tablename__ = "order_line"
    order_line_id: Mapped[str] = c(String(25), "Line ID, format ORD-2026-000001-L01.", primary_key=True)
    order_id: Mapped[str] = fk("orders.order_id", "Parent order.")
    line_no: Mapped[int] = c(Integer, "1-based line number within the order.")
    sku_id: Mapped[str] = fk("sku.sku_id", "SKU ordered.", length=10)
    quantity_ordered: Mapped[int] = c(Integer, "Units ordered.")
    quantity_allocated: Mapped[int] = c(Integer, "Units currently allocated.", default=0, server_default="0")
    quantity_fulfilled: Mapped[int] = c(Integer, "Units shipped.", default=0, server_default="0")
    quantity_backordered: Mapped[int] = c(Integer, "Units that could not be allocated.", default=0, server_default="0")
    unit_price: Mapped[float] = c(Numeric(12, 2), "Price per unit at order time.")
    status: Mapped[str] = c(String(25), "Line lifecycle state.", default="OPEN", server_default="OPEN")
    order: Mapped[Order] = relationship(back_populates="lines")
    __table_args__ = (
        in_enum("status", E.OrderLineStatus),
        UniqueConstraint("order_id", "line_no", name="uq_order_line_no"),
        CheckConstraint("quantity_ordered > 0", name="ordered_positive"),
        CheckConstraint("quantity_allocated >= 0 AND quantity_fulfilled >= 0 AND quantity_backordered >= 0", name="qty_non_negative"),
        CheckConstraint("quantity_fulfilled <= quantity_ordered", name="fulfilled_le_ordered"),
        CheckConstraint("quantity_fulfilled + quantity_backordered <= quantity_ordered", name="fulfilled_backordered_le_ordered"),
        Index("ix_order_line_sku_id", "sku_id"),
    )


class Reservation(Base):
    __tablename__ = "reservation"
    reservation_id: Mapped[str] = c(String(30), "Reservation ID, format RES-ORD-2026-000001-01.", primary_key=True)
    order_line_id: Mapped[str] = fk("order_line.order_line_id", "Line this reservation protects (1 line : 0..N reservations over time).", length=25)
    sku_id: Mapped[str] = fk("sku.sku_id", "Reserved SKU (denormalised for fast checks).", length=10)
    location_id: Mapped[str] = fk("location.location_id", "Location holding the reserved units.", length=10)
    quantity: Mapped[int] = c(Integer, "Reserved units.")
    status: Mapped[str] = c(String(15), "PENDING, CONFIRMED, CONSUMED, EXPIRED, CANCELLED.", default="PENDING", server_default="PENDING")
    expires_at: Mapped[datetime] = c(DateTime(timezone=True), "Expiration timestamp.")
    created_at: Mapped[datetime] = created()
    closed_at: Mapped[datetime | None] = c(DateTime(timezone=True), "When it left an active state.", nullable=True)
    idempotency_key: Mapped[str] = c(String(80), "Prevents duplicate reservation processing.", unique=True)
    events: Mapped[list["ReservationEvent"]] = relationship(back_populates="reservation")
    __table_args__ = (
        in_enum("status", E.ReservationStatus),
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("closed_at IS NULL OR status IN ('CONSUMED','EXPIRED','CANCELLED')", name="closed_only_when_terminal"),
        Index("ix_reservation_status_expires", "status", "expires_at"),
        Index("ix_reservation_sku_loc", "sku_id", "location_id", "status"),
    )


class ReservationEvent(Base):
    __tablename__ = "reservation_event"
    event_id: Mapped[int] = c(BigInteger().with_variant(Integer, "sqlite"), "Surrogate event key.", primary_key=True, autoincrement=True)
    reservation_id: Mapped[str] = fk("reservation.reservation_id", "Reservation.", length=30)
    event_type: Mapped[str] = c(String(15), "CREATED, CONFIRMED, CONSUMED, EXPIRED, CANCELLED, REJECTED.")
    from_status: Mapped[str | None] = c(String(15), "Status before (NULL on CREATED).", nullable=True)
    to_status: Mapped[str | None] = c(String(15), "Status after (NULL on REJECTED).", nullable=True)
    occurred_at: Mapped[datetime] = c(DateTime(timezone=True), "Event time.")
    detail: Mapped[str | None] = c(String(300), "Human-readable explanation.", nullable=True)
    reservation: Mapped[Reservation] = relationship(back_populates="events")
    __table_args__ = (
        in_enum("event_type", E.ReservationEventType),
        Index("ix_reservation_event_res_time", "reservation_id", "occurred_at"),
    )


class InventoryAllocation(Base):
    """Which location was chosen for an order line, and why."""
    __tablename__ = "inventory_allocation"
    allocation_id: Mapped[str] = c(String(20), "Allocation ID, format ALC-2026-00000001.", primary_key=True)
    order_line_id: Mapped[str] = fk("order_line.order_line_id", "Allocated line.", length=25)
    sku_id: Mapped[str] = fk("sku.sku_id", "SKU.", length=10)
    location_id: Mapped[str] = fk("location.location_id", "Selected fulfilment location.", length=10)
    reservation_id: Mapped[str | None] = fk("reservation.reservation_id", "Backing reservation, if any.", nullable=True, length=30)
    quantity: Mapped[int] = c(Integer, "Allocated units.")
    status: Mapped[str] = c(String(15), "ACTIVE, FULFILLED, RELEASED.", default="ACTIVE", server_default="ACTIVE")
    reason: Mapped[str] = c(String(300), "Why this location was chosen (rule applied).")
    candidates: Mapped[dict | None] = c(JSON, "Candidate locations considered with their ATP, for explainability.", nullable=True)
    allocated_at: Mapped[datetime] = c(DateTime(timezone=True), "Allocation time.")
    __table_args__ = (
        in_enum("status", E.AllocationStatus),
        CheckConstraint("quantity > 0", name="quantity_positive"),
        Index("ix_inventory_allocation_line", "order_line_id"),
    )


class Shipment(Base):
    __tablename__ = "shipment"
    shipment_id: Mapped[str] = c(String(20), "Shipment ID, format SHP-2026-000001.", primary_key=True)
    order_id: Mapped[str] = fk("orders.order_id", "Order shipped.", length=20)
    location_id: Mapped[str] = fk("location.location_id", "Shipping location.", length=10)
    status: Mapped[str] = c(String(15), "PENDING, SHIPPED, DELIVERED, CANCELLED.", default="PENDING", server_default="PENDING")
    carrier: Mapped[str | None] = c(String(40), "Carrier name (synthetic).", nullable=True)
    shipped_at: Mapped[datetime | None] = c(DateTime(timezone=True), "Ship time.", nullable=True)
    delivered_at: Mapped[datetime | None] = c(DateTime(timezone=True), "Delivery time.", nullable=True)
    created_at: Mapped[datetime] = created()
    lines: Mapped[list["ShipmentLine"]] = relationship(back_populates="shipment")
    __table_args__ = (
        in_enum("status", E.ShipmentStatus),
        CheckConstraint("delivered_at IS NULL OR shipped_at IS NOT NULL", name="delivered_after_shipped"),
        CheckConstraint("delivered_at IS NULL OR delivered_at >= shipped_at", name="dates_ordered"),
        Index("ix_shipment_order_id", "order_id"),
    )


class ShipmentLine(Base):
    __tablename__ = "shipment_line"
    shipment_id: Mapped[str] = c(String(20), "Shipment.", ForeignKey("shipment.shipment_id", ondelete="RESTRICT"), primary_key=True)
    allocation_id: Mapped[str] = c(String(20), "Allocation fulfilled (many-to-many link between shipments and allocations).", ForeignKey("inventory_allocation.allocation_id", ondelete="RESTRICT"), primary_key=True)
    sku_id: Mapped[str] = fk("sku.sku_id", "SKU shipped.", length=10)
    quantity: Mapped[int] = c(Integer, "Units shipped.")
    sale_movement_id: Mapped[str | None] = fk("inventory_movement.movement_id", "SALE movement that deducted stock.", nullable=True)
    shipment: Mapped[Shipment] = relationship(back_populates="lines")
    __table_args__ = (CheckConstraint("quantity > 0", name="quantity_positive"),)


# =========================================================================== transfers
class Transfer(Base):
    __tablename__ = "transfer"
    transfer_id: Mapped[str] = c(String(20), "Transfer ID, format TRF-2026-000001.", primary_key=True)
    source_location_id: Mapped[str] = fk("location.location_id", "Ships from.", length=10)
    destination_location_id: Mapped[str] = fk("location.location_id", "Ships to.", length=10)
    status: Mapped[str] = c(String(15), "DRAFT, DISPATCHED, IN_TRANSIT, ARRIVED, RECEIVED, CANCELLED.", default="DRAFT", server_default="DRAFT")
    created_at: Mapped[datetime] = created()
    dispatched_at: Mapped[datetime | None] = c(DateTime(timezone=True), "Dispatch time.", nullable=True)
    arrived_at: Mapped[datetime | None] = c(DateTime(timezone=True), "Arrival time at destination dock.", nullable=True)
    received_at: Mapped[datetime | None] = c(DateTime(timezone=True), "Receipt (stock counted) time.", nullable=True)
    lines: Mapped[list["TransferLine"]] = relationship(back_populates="transfer")
    __table_args__ = (
        in_enum("status", E.TransferStatus),
        CheckConstraint("source_location_id <> destination_location_id", name="distinct_ends"),
        CheckConstraint("arrived_at IS NULL OR dispatched_at IS NOT NULL", name="arrived_after_dispatch"),
        CheckConstraint("received_at IS NULL OR arrived_at IS NOT NULL", name="received_after_arrival"),
    )


class TransferLine(Base):
    __tablename__ = "transfer_line"
    transfer_id: Mapped[str] = c(String(20), "Transfer.", ForeignKey("transfer.transfer_id", ondelete="RESTRICT"), primary_key=True)
    line_no: Mapped[int] = c(Integer, "1-based line number.", primary_key=True)
    sku_id: Mapped[str] = fk("sku.sku_id", "SKU transferred.", length=10)
    quantity_dispatched: Mapped[int] = c(Integer, "Units sent.")
    quantity_received: Mapped[int] = c(Integer, "Units counted at receipt.", default=0, server_default="0")
    dispatch_movement_id: Mapped[str | None] = fk("inventory_movement.movement_id", "TRANSFER_DISPATCH movement (source).", nullable=True)
    in_transit_movement_id: Mapped[str | None] = fk("inventory_movement.movement_id", "TRANSFER_IN_TRANSIT movement (destination).", nullable=True)
    receipt_movement_id: Mapped[str | None] = fk("inventory_movement.movement_id", "TRANSFER_RECEIPT movement (destination).", nullable=True)
    transfer: Mapped[Transfer] = relationship(back_populates="lines")
    __table_args__ = (
        CheckConstraint("quantity_dispatched > 0", name="dispatched_positive"),
        CheckConstraint("quantity_received >= 0 AND quantity_received <= quantity_dispatched", name="received_range"),
    )


# =========================================================================== audit
class AuditLog(Base):
    __tablename__ = "audit_log"
    audit_id: Mapped[int] = c(BigInteger().with_variant(Integer, "sqlite"), "Surrogate audit key.", primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = c(String(30), "Table/entity affected.")
    entity_id: Mapped[str] = c(String(40), "Affected record ID.")
    action: Mapped[str] = c(String(40), "What happened (e.g. RESERVATION_EXPIRED, ALLOCATION_CHOSEN).")
    actor: Mapped[str] = c(String(60), "User, service or job responsible.")
    detail: Mapped[dict | None] = c(JSON, "Structured before/after or decision data.", nullable=True)
    created_at: Mapped[datetime] = created()
    __table_args__ = (Index("ix_audit_log_entity", "entity_type", "entity_id"),)
