# Data Dictionary

_Generated from `backend/app/models/models.py` by `python -m app.tools.gen_data_dictionary`. Do not edit by hand._

All data is **synthetic**. No real customer or confidential inventory information is used.

## `audit_log`

| Field | Type | Required | Allowed values | Units | Unique | Foreign key | Validation rules | Description |
|---|---|---|---|---|---|---|---|---|
| `audit_id` | BIGINT | yes | — | — | PK | — | — | Surrogate audit key. |
| `entity_type` | VARCHAR(30) | yes | — | — | — | — | — | Table/entity affected. |
| `entity_id` | VARCHAR(40) | yes | — | — | — | — | — | Affected record ID. |
| `action` | VARCHAR(40) | yes | — | — | — | — | — | What happened (e.g. RESERVATION_EXPIRED, ALLOCATION_CHOSEN). |
| `actor` | VARCHAR(60) | yes | — | — | — | — | — | User, service or job responsible. |
| `detail` | JSON | no | — | — | — | — | — | Structured before/after or decision data. |
| `created_at` | DATETIME | default | — | UTC timestamp | — | — | — | Row creation timestamp (UTC). |

## `location`

| Field | Type | Required | Allowed values | Units | Unique | Foreign key | Validation rules | Description |
|---|---|---|---|---|---|---|---|---|
| `location_id` | VARCHAR(10) | yes | — | — | PK | — | `parent_location_id IS NULL OR parent_location_id <> location_id` | Location ID, format LOC-000001. |
| `name` | VARCHAR(120) | yes | — | — | — | — | — | Location display name. |
| `location_type` | VARCHAR(15) | yes | STORE \| WAREHOUSE \| REGION | — | — | — | — | STORE, WAREHOUSE or REGION (REGION holds no stock). |
| `parent_location_id` | VARCHAR(10) | no | — | — | — | `location.location_id` | `parent_location_id IS NULL OR parent_location_id <> location_id` | Parent in the location hierarchy (self-reference); NULL for roots. |
| `region` | VARCHAR(60) | no | — | — | — | — | — | Geographic region label. |
| `city` | VARCHAR(80) | no | — | — | — | — | — | City (synthetic). |
| `ships_online` | BOOLEAN | default | — | date | — | — | — | True if the location may fulfil online orders. |
| `is_active` | BOOLEAN | default | — | — | — | — | — | False when closed. |
| `created_at` | DATETIME | default | — | UTC timestamp | — | — | — | Row creation timestamp (UTC). |
| `updated_at` | DATETIME | default | — | UTC timestamp | — | — | — | Last update timestamp (UTC). |

## `orders`

| Field | Type | Required | Allowed values | Units | Unique | Foreign key | Validation rules | Description |
|---|---|---|---|---|---|---|---|---|
| `order_id` | VARCHAR(20) | yes | — | — | PK | — | — | Order ID, format ORD-2026-000001. |
| `channel` | VARCHAR(15) | yes | STORE,WEB,MARKETPLACE | — | — | — | — | STORE, WEB or MARKETPLACE. |
| `customer_ref` | VARCHAR(20) | yes | — | — | — | — | — | Synthetic pseudonymous customer key (no real PII). |
| `status` | VARCHAR(25) | default | NEW \| RESERVED \| ALLOCATED \| PARTIALLY_FULFILLED \| FULFILLED \| BACKORDERED \| CANCELLED | — | — | — | — | Order lifecycle state. |
| `placed_at` | DATETIME | yes | — | UTC timestamp | — | — | `cancelled_at IS NULL OR cancelled_at >= placed_at` | When the order was placed. |
| `cancelled_at` | DATETIME | no | — | UTC timestamp | — | — | `cancelled_at IS NULL OR cancelled_at >= placed_at` | Cancellation time. |
| `created_at` | DATETIME | default | — | UTC timestamp | — | — | — | Row creation timestamp (UTC). |
| `updated_at` | DATETIME | default | — | UTC timestamp | — | — | — | Last update timestamp (UTC). |

## `product`

| Field | Type | Required | Allowed values | Units | Unique | Foreign key | Validation rules | Description |
|---|---|---|---|---|---|---|---|---|
| `product_id` | VARCHAR(10) | yes | — | — | PK | — | — | Product ID, format PRD-000001. |
| `name` | VARCHAR(200) | yes | — | — | — | — | — | Product display name. |
| `category` | VARCHAR(80) | yes | — | — | — | — | — | Merchandise category. |
| `brand` | VARCHAR(80) | no | — | — | — | — | — | Brand name (synthetic). |
| `description` | TEXT | no | — | — | — | — | — | Free-text description. |
| `is_active` | BOOLEAN | default | — | — | — | — | — | False when the product is retired. |
| `created_at` | DATETIME | default | — | UTC timestamp | — | — | — | Row creation timestamp (UTC). |
| `updated_at` | DATETIME | default | — | UTC timestamp | — | — | — | Last update timestamp (UTC). |

## `channel_buffer`

| Field | Type | Required | Allowed values | Units | Unique | Foreign key | Validation rules | Description |
|---|---|---|---|---|---|---|---|---|
| `location_id` | VARCHAR(10) | yes | — | — | PK | `location.location_id` | — | Location. |
| `channel` | VARCHAR(15) | yes | STORE,WEB,MARKETPLACE | — | PK | — | — | Channel the buffer applies to. |
| `effective_from` | DATE | yes | — | date | PK | — | `effective_to IS NULL OR effective_to >= effective_from` | Effective start date. |
| `effective_to` | DATE | no | — | date | — | — | `effective_to IS NULL OR effective_to >= effective_from` | Effective end date; NULL = open-ended. |
| `buffer_pct` | NUMERIC(5, 2) | yes | — | percent | — | — | `buffer_pct >= 0 AND buffer_pct <= 100` | Percent of (on_hand - reserved - blocked) withheld from this channel. |

## `shipment`

| Field | Type | Required | Allowed values | Units | Unique | Foreign key | Validation rules | Description |
|---|---|---|---|---|---|---|---|---|
| `shipment_id` | VARCHAR(20) | yes | — | — | PK | — | — | Shipment ID, format SHP-2026-000001. |
| `order_id` | VARCHAR(20) | yes | — | — | — | `orders.order_id` | — | Order shipped. |
| `location_id` | VARCHAR(10) | yes | — | — | — | `location.location_id` | — | Shipping location. |
| `status` | VARCHAR(15) | default | PENDING \| SHIPPED \| DELIVERED \| CANCELLED | — | — | — | — | PENDING, SHIPPED, DELIVERED, CANCELLED. |
| `carrier` | VARCHAR(40) | no | — | — | — | — | — | Carrier name (synthetic). |
| `shipped_at` | DATETIME | no | — | UTC timestamp | — | — | `delivered_at IS NULL OR delivered_at >= shipped_at`<br>`delivered_at IS NULL OR shipped_at IS NOT NULL` | Ship time. |
| `delivered_at` | DATETIME | no | — | UTC timestamp | — | — | `delivered_at IS NULL OR delivered_at >= shipped_at`<br>`delivered_at IS NULL OR shipped_at IS NOT NULL` | Delivery time. |
| `created_at` | DATETIME | default | — | UTC timestamp | — | — | — | Row creation timestamp (UTC). |

## `sku`

| Field | Type | Required | Allowed values | Units | Unique | Foreign key | Validation rules | Description |
|---|---|---|---|---|---|---|---|---|
| `sku_id` | VARCHAR(10) | yes | — | — | PK | — | — | SKU ID, format SKU-000001. |
| `product_id` | VARCHAR(10) | yes | — | — | — | `product.product_id` | — | Parent product. |
| `barcode` | VARCHAR(20) | yes | — | — | yes | — | — | Synthetic EAN-13-style barcode. |
| `variant` | VARCHAR(80) | no | — | — | — | — | — | Variant text, e.g. 'Blue / M'. |
| `unit_cost` | NUMERIC(12, 2) | yes | — | USD | — | — | `unit_cost >= 0 AND unit_price >= 0` | Unit cost in USD (synthetic). |
| `unit_price` | NUMERIC(12, 2) | yes | — | USD | — | — | `unit_cost >= 0 AND unit_price >= 0` | List price in USD (synthetic). |
| `uom` | VARCHAR(10) | default | — | — | — | — | — | Unit of measure; always 'EA' (each). |
| `status` | VARCHAR(15) | default | ACTIVE \| DISCONTINUED | — | — | — | — | Lifecycle state: ACTIVE or DISCONTINUED. |
| `active_from` | DATE | yes | — | date | — | — | `discontinued_on IS NULL OR discontinued_on >= active_from` | Effective start date of the SKU. |
| `discontinued_on` | DATE | no | — | date | — | — | `discontinued_on IS NULL OR discontinued_on >= active_from` | Effective end date; NULL while active. |
| `created_at` | DATETIME | default | — | UTC timestamp | — | — | — | Row creation timestamp (UTC). |
| `updated_at` | DATETIME | default | — | UTC timestamp | — | — | — | Last update timestamp (UTC). |

## `transfer`

| Field | Type | Required | Allowed values | Units | Unique | Foreign key | Validation rules | Description |
|---|---|---|---|---|---|---|---|---|
| `transfer_id` | VARCHAR(20) | yes | — | — | PK | — | — | Transfer ID, format TRF-2026-000001. |
| `source_location_id` | VARCHAR(10) | yes | — | — | — | `location.location_id` | `source_location_id <> destination_location_id` | Ships from. |
| `destination_location_id` | VARCHAR(10) | yes | — | — | — | `location.location_id` | `source_location_id <> destination_location_id` | Ships to. |
| `status` | VARCHAR(15) | default | DRAFT \| DISPATCHED \| IN_TRANSIT \| ARRIVED \| RECEIVED \| CANCELLED | — | — | — | — | DRAFT, DISPATCHED, IN_TRANSIT, ARRIVED, RECEIVED, CANCELLED. |
| `created_at` | DATETIME | default | — | UTC timestamp | — | — | — | Row creation timestamp (UTC). |
| `dispatched_at` | DATETIME | no | — | UTC timestamp | — | — | `arrived_at IS NULL OR dispatched_at IS NOT NULL` | Dispatch time. |
| `arrived_at` | DATETIME | no | — | UTC timestamp | — | — | `arrived_at IS NULL OR dispatched_at IS NOT NULL`<br>`received_at IS NULL OR arrived_at IS NOT NULL` | Arrival time at destination dock. |
| `received_at` | DATETIME | no | — | UTC timestamp | — | — | `received_at IS NULL OR arrived_at IS NOT NULL` | Receipt (stock counted) time. |

## `inventory_balance`

| Field | Type | Required | Allowed values | Units | Unique | Foreign key | Validation rules | Description |
|---|---|---|---|---|---|---|---|---|
| `sku_id` | VARCHAR(10) | yes | — | — | PK | `sku.sku_id` | — | SKU. |
| `location_id` | VARCHAR(10) | yes | — | — | PK | `location.location_id` | — | Location. |
| `on_hand_qty` | INTEGER | default | — | units (each) | — | — | `on_hand_qty >= 0`<br>`reserved_qty + blocked_qty <= on_hand_qty` | Physical units at the location (ledger-derived). |
| `reserved_qty` | INTEGER | default | — | units (each) | — | — | `reserved_qty + blocked_qty <= on_hand_qty`<br>`reserved_qty >= 0` | Units held by PENDING/CONFIRMED reservations. |
| `blocked_qty` | INTEGER | default | — | units (each) | — | — | `blocked_qty >= 0`<br>`reserved_qty + blocked_qty <= on_hand_qty` | Units held by ACTIVE inventory blocks (damaged/quality hold). |
| `in_transit_qty` | INTEGER | default | — | units (each) | — | — | `in_transit_qty >= 0` | Units dispatched TO this location, not yet received (ledger-derived). |
| `last_movement_id` | VARCHAR(20) | no | — | — | — | — | — | Last ledger movement applied (traceability). |
| `version` | INTEGER | default | — | — | — | — | — | Optimistic-lock counter. |
| `updated_at` | DATETIME | default | — | UTC timestamp | — | — | — | Last update timestamp (UTC). |

## `inventory_movement`

| Field | Type | Required | Allowed values | Units | Unique | Foreign key | Validation rules | Description |
|---|---|---|---|---|---|---|---|---|
| `movement_id` | VARCHAR(20) | yes | — | — | PK | — | — | Movement ID, format MOV-2026-00000001. |
| `sku_id` | VARCHAR(10) | yes | — | — | — | `sku.sku_id` | — | SKU moved. |
| `location_id` | VARCHAR(10) | yes | — | — | — | `location.location_id` | — | Location whose balance changes. |
| `movement_type` | VARCHAR(25) | yes | RECEIPT \| SALE \| RETURN \| TRANSFER_DISPATCH \| TRANSFER_IN_TRANSIT \| TRANSFER_RECEIPT \| ADJUSTMENT \| DAMAGE \| CORRECTION | — | — | — | `movement_type <> 'CORRECTION' OR audit_ref IS NOT NULL` | Event type (see MovementType). |
| `on_hand_delta` | INTEGER | default | — | units (each) | — | — | `on_hand_delta <> 0 OR in_transit_delta <> 0` | Signed change to on_hand. |
| `in_transit_delta` | INTEGER | default | — | units (each) | — | — | `on_hand_delta <> 0 OR in_transit_delta <> 0` | Signed change to in_transit. |
| `channel` | VARCHAR(15) | no | — | — | — | — | — | Sales channel where relevant (SALE/RETURN). |
| `occurred_at` | DATETIME | yes | — | UTC timestamp | — | — | — | Business time the event happened. |
| `recorded_at` | DATETIME | default | — | UTC timestamp | — | — | — | Row creation timestamp (UTC). |
| `reference_type` | VARCHAR(20) | no | — | — | — | — | — | Source record type: SHIPMENT, TRANSFER, INBOUND, ADJUSTMENT, ... |
| `reference_id` | VARCHAR(30) | no | — | — | — | — | — | Source record ID (e.g. SHP-2026-000001). |
| `reason` | VARCHAR(200) | no | — | — | — | — | — | Mandatory for ADJUSTMENT/DAMAGE/CORRECTION. |
| `audit_ref` | VARCHAR(30) | no | — | — | — | — | `movement_type <> 'CORRECTION' OR audit_ref IS NOT NULL` | Audit reference; mandatory for CORRECTION. |
| `corrects_movement_id` | VARCHAR(20) | no | — | — | — | `inventory_movement.movement_id` | — | Earlier movement this event compensates (never edits). |
| `idempotency_key` | VARCHAR(80) | yes | — | — | yes | — | — | Unique key; duplicate submissions are rejected. |

## `order_line`

| Field | Type | Required | Allowed values | Units | Unique | Foreign key | Validation rules | Description |
|---|---|---|---|---|---|---|---|---|
| `order_line_id` | VARCHAR(25) | yes | — | — | PK | — | — | Line ID, format ORD-2026-000001-L01. |
| `order_id` | VARCHAR(20) | yes | — | — | — | `orders.order_id` | — | Parent order. |
| `line_no` | INTEGER | yes | — | — | — | — | — | 1-based line number within the order. |
| `sku_id` | VARCHAR(10) | yes | — | — | — | `sku.sku_id` | — | SKU ordered. |
| `quantity_ordered` | INTEGER | yes | — | units (each) | — | — | `quantity_fulfilled + quantity_backordered <= quantity_ordered`<br>`quantity_ordered > 0`<br>`quantity_fulfilled <= quantity_ordered` | Units ordered. |
| `quantity_allocated` | INTEGER | default | — | units (each) | — | — | `quantity_allocated >= 0 AND quantity_fulfilled >= 0 AND quantity_backordered >= 0` | Units currently allocated. |
| `quantity_fulfilled` | INTEGER | default | — | units (each) | — | — | `quantity_fulfilled + quantity_backordered <= quantity_ordered`<br>`quantity_allocated >= 0 AND quantity_fulfilled >= 0 AND quantity_backordered >= 0`<br>`quantity_fulfilled <= quantity_ordered` | Units shipped. |
| `quantity_backordered` | INTEGER | default | — | units (each) | — | — | `quantity_fulfilled + quantity_backordered <= quantity_ordered`<br>`quantity_allocated >= 0 AND quantity_fulfilled >= 0 AND quantity_backordered >= 0` | Units that could not be allocated. |
| `unit_price` | NUMERIC(12, 2) | yes | — | USD | — | — | — | Price per unit at order time. |
| `status` | VARCHAR(25) | default | OPEN \| ALLOCATED \| PARTIALLY_FULFILLED \| FULFILLED \| BACKORDERED \| CANCELLED | — | — | — | — | Line lifecycle state. |

## `replenishment_rule`

| Field | Type | Required | Allowed values | Units | Unique | Foreign key | Validation rules | Description |
|---|---|---|---|---|---|---|---|---|
| `rule_id` | VARCHAR(10) | yes | — | — | PK | — | — | Rule ID, format RPR-000001. |
| `sku_id` | VARCHAR(10) | yes | — | — | — | `sku.sku_id` | — | SKU governed. |
| `location_id` | VARCHAR(10) | yes | — | — | — | `location.location_id` | — | Location governed. |
| `safety_stock_qty` | INTEGER | yes | — | units (each) | — | — | `safety_stock_qty >= 0 AND min_stock_qty >= 0` | Safety-stock buffer subtracted in ATP. |
| `min_stock_qty` | INTEGER | yes | — | units (each) | — | — | `safety_stock_qty >= 0 AND min_stock_qty >= 0`<br>`min_stock_qty <= reorder_point_qty AND reorder_point_qty < target_stock_qty` | Minimum stock; below this => low-stock flag. |
| `reorder_point_qty` | INTEGER | yes | — | units (each) | — | — | `min_stock_qty <= reorder_point_qty AND reorder_point_qty < target_stock_qty` | Inventory position at/below which to reorder. |
| `target_stock_qty` | INTEGER | yes | — | units (each) | — | — | `min_stock_qty <= reorder_point_qty AND reorder_point_qty < target_stock_qty` | Order-up-to level. |
| `supplier_lead_time_days` | INTEGER | yes | — | days | — | — | `supplier_lead_time_days > 0` | Supplier lead time in days. |
| `supplier_name` | VARCHAR(120) | no | — | — | — | — | — | Synthetic supplier name. |
| `effective_from` | DATE | yes | — | date | — | — | `effective_to IS NULL OR effective_to >= effective_from` | Effective start date. |
| `effective_to` | DATE | no | — | date | — | — | `effective_to IS NULL OR effective_to >= effective_from` | Effective end date; NULL = current. |

## `inbound_supply`

| Field | Type | Required | Allowed values | Units | Unique | Foreign key | Validation rules | Description |
|---|---|---|---|---|---|---|---|---|
| `inbound_id` | VARCHAR(20) | yes | — | — | PK | — | — | Inbound ID, format INB-2026-000001. |
| `sku_id` | VARCHAR(10) | yes | — | — | — | `sku.sku_id` | — | SKU expected. |
| `location_id` | VARCHAR(10) | yes | — | — | — | `location.location_id` | — | Receiving location. |
| `quantity` | INTEGER | yes | — | units (each) | — | — | `quantity > 0` | Expected units. |
| `expected_at` | DATETIME | yes | — | UTC timestamp | — | — | — | Promised arrival time. |
| `status` | VARCHAR(15) | default | PLANNED \| CONFIRMED \| RECEIVED \| CANCELLED | — | — | — | — | PLANNED, CONFIRMED, RECEIVED, CANCELLED. |
| `atp_eligible` | BOOLEAN | default | — | — | — | — | — | Policy approval flag: True only for supplier-confirmed supply. |
| `receipt_movement_id` | VARCHAR(20) | no | — | — | — | `inventory_movement.movement_id` | — | RECEIPT movement created on receipt. |
| `created_at` | DATETIME | default | — | UTC timestamp | — | — | — | Row creation timestamp (UTC). |

## `inventory_block`

| Field | Type | Required | Allowed values | Units | Unique | Foreign key | Validation rules | Description |
|---|---|---|---|---|---|---|---|---|
| `block_id` | VARCHAR(10) | yes | — | — | PK | — | — | Block ID, format BLK-000001. |
| `sku_id` | VARCHAR(10) | yes | — | — | — | `sku.sku_id` | — | Blocked SKU. |
| `location_id` | VARCHAR(10) | yes | — | — | — | `location.location_id` | — | Where the units are blocked. |
| `quantity` | INTEGER | yes | — | units (each) | — | — | `quantity > 0` | Blocked units. |
| `reason` | VARCHAR(25) | yes | DAMAGED \| QUALITY_HOLD \| RECALL \| COUNT_DISCREPANCY | — | — | — | — | DAMAGED, QUALITY_HOLD, RECALL, COUNT_DISCREPANCY. |
| `status` | VARCHAR(15) | default | ACTIVE \| RELEASED \| WRITTEN_OFF | — | — | — | — | ACTIVE, RELEASED, WRITTEN_OFF. |
| `blocked_at` | DATETIME | yes | — | UTC timestamp | — | — | `released_at IS NULL OR released_at >= blocked_at` | When the block started. |
| `released_at` | DATETIME | no | — | UTC timestamp | — | — | `released_at IS NULL OR released_at >= blocked_at` | When the block ended. |
| `write_off_movement_id` | VARCHAR(20) | no | — | — | — | `inventory_movement.movement_id` | — | DAMAGE movement if written off. |

## `reservation`

| Field | Type | Required | Allowed values | Units | Unique | Foreign key | Validation rules | Description |
|---|---|---|---|---|---|---|---|---|
| `reservation_id` | VARCHAR(30) | yes | — | — | PK | — | — | Reservation ID, format RES-ORD-2026-000001-01. |
| `order_line_id` | VARCHAR(25) | yes | — | — | — | `order_line.order_line_id` | — | Line this reservation protects (1 line : 0..N reservations over time). |
| `sku_id` | VARCHAR(10) | yes | — | — | — | `sku.sku_id` | — | Reserved SKU (denormalised for fast checks). |
| `location_id` | VARCHAR(10) | yes | — | — | — | `location.location_id` | — | Location holding the reserved units. |
| `quantity` | INTEGER | yes | — | units (each) | — | — | `quantity > 0` | Reserved units. |
| `status` | VARCHAR(15) | default | PENDING \| CONFIRMED \| CONSUMED \| EXPIRED \| CANCELLED | — | — | — | — | PENDING, CONFIRMED, CONSUMED, EXPIRED, CANCELLED. |
| `expires_at` | DATETIME | yes | — | UTC timestamp | — | — | — | Expiration timestamp. |
| `created_at` | DATETIME | default | — | UTC timestamp | — | — | — | Row creation timestamp (UTC). |
| `closed_at` | DATETIME | no | — | UTC timestamp | — | — | — | When it left an active state. |
| `idempotency_key` | VARCHAR(80) | yes | — | — | yes | — | — | Prevents duplicate reservation processing. |

## `transfer_line`

| Field | Type | Required | Allowed values | Units | Unique | Foreign key | Validation rules | Description |
|---|---|---|---|---|---|---|---|---|
| `transfer_id` | VARCHAR(20) | yes | — | — | PK | `transfer.transfer_id` | — | Transfer. |
| `line_no` | INTEGER | yes | — | — | PK | — | — | 1-based line number. |
| `sku_id` | VARCHAR(10) | yes | — | — | — | `sku.sku_id` | — | SKU transferred. |
| `quantity_dispatched` | INTEGER | yes | — | units (each) | — | — | `quantity_received >= 0 AND quantity_received <= quantity_dispatched`<br>`quantity_dispatched > 0` | Units sent. |
| `quantity_received` | INTEGER | default | — | units (each) | — | — | `quantity_received >= 0 AND quantity_received <= quantity_dispatched` | Units counted at receipt. |
| `dispatch_movement_id` | VARCHAR(20) | no | — | — | — | `inventory_movement.movement_id` | — | TRANSFER_DISPATCH movement (source). |
| `in_transit_movement_id` | VARCHAR(20) | no | — | — | — | `inventory_movement.movement_id` | — | TRANSFER_IN_TRANSIT movement (destination). |
| `receipt_movement_id` | VARCHAR(20) | no | — | — | — | `inventory_movement.movement_id` | — | TRANSFER_RECEIPT movement (destination). |

## `inventory_allocation`

| Field | Type | Required | Allowed values | Units | Unique | Foreign key | Validation rules | Description |
|---|---|---|---|---|---|---|---|---|
| `allocation_id` | VARCHAR(20) | yes | — | — | PK | — | — | Allocation ID, format ALC-2026-00000001. |
| `order_line_id` | VARCHAR(25) | yes | — | — | — | `order_line.order_line_id` | — | Allocated line. |
| `sku_id` | VARCHAR(10) | yes | — | — | — | `sku.sku_id` | — | SKU. |
| `location_id` | VARCHAR(10) | yes | — | — | — | `location.location_id` | — | Selected fulfilment location. |
| `reservation_id` | VARCHAR(30) | no | — | — | — | `reservation.reservation_id` | — | Backing reservation, if any. |
| `quantity` | INTEGER | yes | — | units (each) | — | — | `quantity > 0` | Allocated units. |
| `status` | VARCHAR(15) | default | ACTIVE \| FULFILLED \| RELEASED | — | — | — | — | ACTIVE, FULFILLED, RELEASED. |
| `reason` | VARCHAR(300) | yes | — | — | — | — | — | Why this location was chosen (rule applied). |
| `candidates` | JSON | no | — | — | — | — | — | Candidate locations considered with their ATP, for explainability. |
| `allocated_at` | DATETIME | yes | — | UTC timestamp | — | — | — | Allocation time. |

## `reservation_event`

| Field | Type | Required | Allowed values | Units | Unique | Foreign key | Validation rules | Description |
|---|---|---|---|---|---|---|---|---|
| `event_id` | BIGINT | yes | — | — | PK | — | — | Surrogate event key. |
| `reservation_id` | VARCHAR(30) | yes | — | — | — | `reservation.reservation_id` | — | Reservation. |
| `event_type` | VARCHAR(15) | yes | CREATED \| CONFIRMED \| CONSUMED \| EXPIRED \| CANCELLED \| REJECTED | — | — | — | — | CREATED, CONFIRMED, CONSUMED, EXPIRED, CANCELLED, REJECTED. |
| `from_status` | VARCHAR(15) | no | — | — | — | — | — | Status before (NULL on CREATED). |
| `to_status` | VARCHAR(15) | no | — | — | — | — | — | Status after (NULL on REJECTED). |
| `occurred_at` | DATETIME | yes | — | UTC timestamp | — | — | — | Event time. |
| `detail` | VARCHAR(300) | no | — | — | — | — | — | Human-readable explanation. |

## `shipment_line`

| Field | Type | Required | Allowed values | Units | Unique | Foreign key | Validation rules | Description |
|---|---|---|---|---|---|---|---|---|
| `shipment_id` | VARCHAR(20) | yes | — | — | PK | `shipment.shipment_id` | — | Shipment. |
| `allocation_id` | VARCHAR(20) | yes | — | — | PK | `inventory_allocation.allocation_id` | — | Allocation fulfilled (many-to-many link between shipments and allocations). |
| `sku_id` | VARCHAR(10) | yes | — | — | — | `sku.sku_id` | — | SKU shipped. |
| `quantity` | INTEGER | yes | — | units (each) | — | — | `quantity > 0` | Units shipped. |
| `sale_movement_id` | VARCHAR(20) | no | — | — | — | `inventory_movement.movement_id` | — | SALE movement that deducted stock. |
