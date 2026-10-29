# Business Rules

Implemented as reusable Python service functions in `backend/app/services/` (Stage 3). This document is the specification they are tested against.

## BR-1 Inventory accounting
1. The ledger (`inventory_movement`) is the source of truth for **on_hand** and **in_transit**. It is insert-only.
2. **reserved** is derived from reservations with status PENDING/CONFIRMED; **blocked** from blocks with status ACTIVE.
3. `inventory_balance` is a cached projection. **Reconciliation:** for each (SKU, location), `on_hand = Σ on_hand_delta`, `in_transit = Σ in_transit_delta`, `reserved = Σ active reservation qty`, `blocked = Σ active block qty`. Any mismatch is a reconciliation failure.
4. Movement sign rules:

| Type | on_hand Δ | in_transit Δ | Where |
|---|---|---|---|
| RECEIPT | + | 0 | receiving location |
| SALE | − | 0 | shipping location |
| RETURN | + | 0 | returning location |
| TRANSFER_DISPATCH | − | 0 | source |
| TRANSFER_IN_TRANSIT | 0 | + | destination |
| TRANSFER_RECEIPT | + | − | destination |
| ADJUSTMENT / CORRECTION | ± | 0 | reason (+ audit_ref for CORRECTION) required |
| DAMAGE | − | 0 | reason required |

5. History is never edited. A mistake is fixed by a new movement whose `corrects_movement_id` points at the original.

## BR-2 Available-to-promise (ATP)

For one SKU at one location, for one channel:

```
base      = on_hand − reserved − blocked
buffered  = base − channel_buffer_pct/100 × max(base, 0)      (rounded down)
ATP       = max(0, floor(buffered) − safety_stock + eligible_inbound)
```

* `safety_stock` comes from the `replenishment_rule` effective at the calculation date (0 if none).
* `channel_buffer_pct` comes from the `channel_buffer` row effective at that date (0 if none). Physical store sales use the STORE row; online uses WEB / MARKETPLACE.
* **eligible_inbound** = Σ `inbound_supply.quantity` where `status = CONFIRMED`, `atp_eligible = true`, and `expected_at <= as_of + ATP_INBOUND_HORIZON_DAYS` (default 7).
* **Never counted:** PLANNED inbound; in-transit **transfers** (`in_transit_qty` is excluded until `TRANSFER_RECEIPT`); RECEIVED inbound (already in on_hand, so it would be double-counted).
* Network ATP is the sum of location ATPs for locations that may serve the channel.
* Every ATP result returns its components (on_hand, reserved, blocked, buffer, safety stock, inbound, source record IDs) so it is explainable.

## BR-3 Reservations
1. Created for an order line at a location; allowed only if `requested ≤ ATP` computed **after locking** the balance row (`FOR UPDATE`). Otherwise a REJECTED event is logged and no stock is held.
2. `expires_at = created_at + RESERVATION_TTL_MINUTES` (default 30).
3. Events: CREATED, CONFIRMED, CONSUMED, EXPIRED, CANCELLED, REJECTED; each stores from/to status and time.
4. Idempotency: the same `idempotency_key` returns the existing reservation, never a second hold.
5. Expiry job: every PENDING/CONFIRMED reservation with `expires_at <= now` becomes EXPIRED, `reserved_qty` is decremented, and an event + audit row are written. Reservations that are still active after `expires_at` are anomalies.

## BR-4 Orders & fulfilment
1. An order has ≥ 1 line. Lines are allocated independently.
2. **Eligible locations:** active, `ships_online` for online channels, ATP ≥ 1 for the SKU.
3. **Selection order:** (a) a single location that can fill the whole line; among those, highest ATP, tie → lowest location ID; (b) otherwise split across locations by descending ATP; (c) any shortfall becomes `quantity_backordered`.
4. The chosen location, the candidates considered with their ATP, and the rule applied are saved in `inventory_allocation.reason/candidates`.
5. Fulfilment (shipment) creates a SALE movement per shipment line and links it in `shipment_line.sale_movement_id`. It may only consume units that are on hand **and not blocked**; blocked units are never shippable.
6. Partial fulfilment is allowed; line and order statuses follow the lifecycle in schema.md. Cancelling releases active reservations/allocations.

## BR-5 Transfers
1. **Dispatch:** TRANSFER_DISPATCH (source on_hand −q) and TRANSFER_IN_TRANSIT (destination in_transit +q) in one transaction. Source must have `q ≤ on_hand − reserved − blocked`.
2. **Arrival:** status change only, no stock movement.
3. **Receipt:** TRANSFER_RECEIPT (destination in_transit −q, on_hand +q_received). Any shortfall `q − q_received` is written off by a separate DAMAGE/ADJUSTMENT movement with a reason.
4. At no point is a unit counted in both source on_hand and destination on_hand.

## BR-6 Replenishment
* `inventory_position = on_hand − blocked + eligible_inbound + in_transit(transfers) − reserved`.
* If `inventory_position <= reorder_point` → recommend `order_qty = target − inventory_position`, rounded up to ≥ 1.
* **Low-stock flag:** `on_hand − reserved − blocked < min_stock`.
* **Stockout risk:** `projected_stock = available − avg_daily_demand × lead_time_days`; if `< 0` → STOCKOUT_RISK. `avg_daily_demand` is the 28-day average of SALE movements.
* Each recommendation stores the numbers used and a sentence explaining the trigger.

## BR-7 Anomaly categories (detected in Stage 6)

| Code | Description | Detection |
|---|---|---|
| RECON_MISMATCH | Balance ≠ ledger | recompute from ledger |
| RESERVATION_EXCEEDS_ATP | Active reservation > available at creation | compare to ATP |
| BLOCKED_STOCK_FULFILMENT | Shipment consumed blocked units | shipment vs. active blocks |
| TRANSFER_DOUBLE_COUNT | Receipt posted at destination while still in transit at both ends | transfer ledger check |
| EXPIRED_RESERVATION_ACTIVE | Active after `expires_at` | status vs. time |
| DUPLICATE_MOVEMENT | Same business event posted twice | key / content match |
| OVERSELL | Fulfilled > available | on_hand would go negative |
| INVALID_STATE_TRANSITION | Transition not in lifecycle table | event/status history |

Ground truth lives in a separate `ground_truth.csv` and is **never** read by the detectors, only by the evaluator.
