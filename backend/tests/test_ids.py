from app.core import ids


def test_formats():
    assert ids.sku_id(1) == "SKU-000001"
    assert ids.location_id(1) == "LOC-000001"
    assert ids.order_id(2026, 1) == "ORD-2026-000001"
    assert ids.reservation_id(ids.order_id(2026, 1), 1) == "RES-ORD-2026-000001-01"
    assert ids.movement_id(2026, 1) == "MOV-2026-00000001"
    assert ids.shipment_id(2026, 1) == "SHP-2026-000001"


def test_deterministic_and_wide_enough_for_full_dataset():
    assert ids.sku_id(5000) == ids.sku_id(5000)
    assert ids.movement_id(2026, 1_000_000) == "MOV-2026-01000000"
    assert ids.order_id(2026, 50_000) == "ORD-2026-050000"
