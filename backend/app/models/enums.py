import enum


class LocationType(str, enum.Enum):
    STORE = "STORE"
    WAREHOUSE = "WAREHOUSE"
    REGION = "REGION"  # hierarchy node, holds no stock


class Channel(str, enum.Enum):
    STORE = "STORE"
    WEB = "WEB"
    MARKETPLACE = "MARKETPLACE"


class MovementType(str, enum.Enum):
    RECEIPT = "RECEIPT"                          # on_hand +
    SALE = "SALE"                                # on_hand -  (created by shipment)
    RETURN = "RETURN"                            # on_hand +
    TRANSFER_DISPATCH = "TRANSFER_DISPATCH"      # source on_hand -
    TRANSFER_IN_TRANSIT = "TRANSFER_IN_TRANSIT"  # destination in_transit +
    TRANSFER_RECEIPT = "TRANSFER_RECEIPT"        # destination in_transit -, on_hand +
    ADJUSTMENT = "ADJUSTMENT"                    # signed; needs reason + audit ref
    DAMAGE = "DAMAGE"                            # on_hand - (write-off)
    CORRECTION = "CORRECTION"                    # reconciliation fix; needs audit ref


class ReservationStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CONSUMED = "CONSUMED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class ReservationEventType(str, enum.Enum):
    CREATED = "CREATED"
    CONFIRMED = "CONFIRMED"
    CONSUMED = "CONSUMED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class OrderStatus(str, enum.Enum):
    NEW = "NEW"
    RESERVED = "RESERVED"
    ALLOCATED = "ALLOCATED"
    PARTIALLY_FULFILLED = "PARTIALLY_FULFILLED"
    FULFILLED = "FULFILLED"
    BACKORDERED = "BACKORDERED"
    CANCELLED = "CANCELLED"


class OrderLineStatus(str, enum.Enum):
    OPEN = "OPEN"
    ALLOCATED = "ALLOCATED"
    PARTIALLY_FULFILLED = "PARTIALLY_FULFILLED"
    FULFILLED = "FULFILLED"
    BACKORDERED = "BACKORDERED"
    CANCELLED = "CANCELLED"


class AllocationStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    FULFILLED = "FULFILLED"
    RELEASED = "RELEASED"


class ShipmentStatus(str, enum.Enum):
    PENDING = "PENDING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class TransferStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    DISPATCHED = "DISPATCHED"
    IN_TRANSIT = "IN_TRANSIT"
    ARRIVED = "ARRIVED"
    RECEIVED = "RECEIVED"
    CANCELLED = "CANCELLED"


class BlockReason(str, enum.Enum):
    DAMAGED = "DAMAGED"
    QUALITY_HOLD = "QUALITY_HOLD"
    RECALL = "RECALL"
    COUNT_DISCREPANCY = "COUNT_DISCREPANCY"


class BlockStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    WRITTEN_OFF = "WRITTEN_OFF"


class InboundStatus(str, enum.Enum):
    PLANNED = "PLANNED"
    CONFIRMED = "CONFIRMED"
    RECEIVED = "RECEIVED"
    CANCELLED = "CANCELLED"


class SkuStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    DISCONTINUED = "DISCONTINUED"


def values(e: type[enum.Enum]) -> list[str]:
    return [m.value for m in e]
