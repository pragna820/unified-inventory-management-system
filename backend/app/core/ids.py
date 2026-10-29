"""Deterministic business-ID formatters. Same input -> same ID, in every export."""
from __future__ import annotations


def product_id(n: int) -> str:
    return f"PRD-{n:06d}"

def sku_id(n: int) -> str:
    return f"SKU-{n:06d}"

def location_id(n: int) -> str:
    return f"LOC-{n:06d}"

def order_id(year: int, n: int) -> str:
    return f"ORD-{year}-{n:06d}"

def order_line_id(order: str, line_no: int) -> str:
    return f"{order}-L{line_no:02d}"

def reservation_id(order: str, line_no: int) -> str:
    return f"RES-{order}-{line_no:02d}"

def movement_id(year: int, n: int) -> str:
    return f"MOV-{year}-{n:08d}"

def shipment_id(year: int, n: int) -> str:
    return f"SHP-{year}-{n:06d}"

def transfer_id(year: int, n: int) -> str:
    return f"TRF-{year}-{n:06d}"

def allocation_id(year: int, n: int) -> str:
    return f"ALC-{year}-{n:08d}"

def block_id(n: int) -> str:
    return f"BLK-{n:06d}"

def inbound_id(year: int, n: int) -> str:
    return f"INB-{year}-{n:06d}"

def rule_id(n: int) -> str:
    return f"RPR-{n:06d}"
