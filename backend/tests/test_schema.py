"""Schema-level tests on in-memory SQLite (constraints are portable CHECK/FK/UNIQUE)."""
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (Base, InventoryBalance, InventoryMovement, Location, Product,
                        ReplenishmentRule, Sku, Transfer)

NOW = datetime(2026, 1, 5, tzinfo=timezone.utc)


@pytest.fixture()
def session():
    engine = create_engine("sqlite://")
    event.listen(engine, "connect", lambda conn, _: conn.execute("PRAGMA foreign_keys=ON"))
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        s.add_all([
            Product(product_id="PRD-000001", name="Tee", category="Apparel"),
            Sku(sku_id="SKU-000001", product_id="PRD-000001", barcode="1", unit_cost=5,
                unit_price=10, active_from=date(2026, 1, 1)),
            Location(location_id="LOC-000001", name="WH1", location_type="WAREHOUSE"),
            Location(location_id="LOC-000002", name="S1", location_type="STORE"),
        ])
        s.commit()
        yield s


def mv(**kw):
    base = dict(movement_id="MOV-2026-00000001", sku_id="SKU-000001", location_id="LOC-000001",
                movement_type="RECEIPT", on_hand_delta=10, occurred_at=NOW, idempotency_key="k1")
    base.update(kw)
    return InventoryMovement(**base)


def fails(session, obj):
    session.add(obj)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_valid_movement_ok(session):
    session.add(mv()); session.commit()


def test_duplicate_idempotency_key_rejected(session):
    session.add(mv()); session.commit()
    fails(session, mv(movement_id="MOV-2026-00000002"))


def test_adjustment_requires_reason(session):
    fails(session, mv(movement_type="ADJUSTMENT"))


def test_correction_requires_audit_ref(session):
    fails(session, mv(movement_type="CORRECTION", reason="fix"))


def test_zero_movement_rejected(session):
    fails(session, mv(on_hand_delta=0))


def test_invalid_movement_type_rejected(session):
    fails(session, mv(movement_type="MAGIC"))


def test_unknown_sku_rejected(session):
    fails(session, mv(sku_id="SKU-999999"))


def test_balance_holds_cannot_exceed_on_hand(session):
    fails(session, InventoryBalance(sku_id="SKU-000001", location_id="LOC-000001",
                                    on_hand_qty=5, reserved_qty=4, blocked_qty=3))


def test_transfer_ends_must_differ(session):
    fails(session, Transfer(transfer_id="TRF-2026-000001", source_location_id="LOC-000001",
                            destination_location_id="LOC-000001"))


def test_replenishment_levels_ordered(session):
    fails(session, ReplenishmentRule(rule_id="RPR-000001", sku_id="SKU-000001",
          location_id="LOC-000001", safety_stock_qty=2, min_stock_qty=10, reorder_point_qty=5,
          target_stock_qty=50, supplier_lead_time_days=7, effective_from=date(2026, 1, 1)))


def test_every_column_is_documented():
    missing = [f"{t.name}.{col.name}" for t in Base.metadata.sorted_tables
               for col in t.columns if not col.comment]
    assert not missing, missing
