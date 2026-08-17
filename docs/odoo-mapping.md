# TradeCore — Odoo Field Mapping

> **Status**: PLACEHOLDER — finalize once Odoo CSV/XML export files are provided.

This document maps every Odoo model field to the corresponding TradeCore database field.

## Conventions

| Symbol | Meaning |
|---|---|
| ✅ | Mapped directly |
| 🔄 | Transformed before import |
| ⚠️ | Requires confirmation |
| ❌ | Not migrated (Odoo-internal / irrelevant) |
| 🆕 | New field with no Odoo equivalent |

---

## Products — `product.template` + `product.product`

| Odoo Field | TradeCore Table.Column | Transform | Validation | Status |
|---|---|---|---|---|
| `default_code` | `products.code` | Trim, uppercase | Must not be empty; unique | ✅ |
| `name` | `products.name` | Keep original | Must not be empty | ✅ |
| `categ_id.name` | `product_categories.name` | Lookup or create | | ✅ |
| `uom_id.name` | `units_of_measure.name` | Lookup or create | | ✅ |
| `uom_po_id.name` | `products.purchase_uom_id` | Lookup or create | | ✅ |
| `list_price` | `price_list_items.price` (standard) | Numeric | Must be ≥ 0 | ✅ |
| `standard_price` | `products.cost_price` | Numeric | Must be ≥ 0 | ✅ |
| `active` | `products.is_active` | Boolean | | ✅ |
| `description` | `products.description` | Text | | ✅ |
| `type` | `products.product_type` | `product`→`product`, `consu`→`consumable`, `service`→`service` | | 🔄 |
| `barcode` | `products.barcode` | String | | ✅ |
| `weight` | `products.weight_kg` | Numeric | Must be ≥ 0 | ✅ |
| `volume` | `products.volume_m3` | Numeric | Must be ≥ 0 | ✅ |
| `id` | `products.odoo_id` | Integer | Migration audit only | ✅ |
| `sale_ok` | — | Ignored | Not needed | ❌ |
| `purchase_ok` | — | Ignored | Not needed | ❌ |
| `tracking` | — | ⚠️ Confirm if serial/lot tracking needed | | ⚠️ |

---

## Partners — `res.partner` (Customers — customer_rank > 0)

| Odoo Field | TradeCore Table.Column | Transform | Validation | Status |
|---|---|---|---|---|
| `ref` | `customers.code` | Use as upsert key | Must match KH-XXXX or create mapping | ✅ |
| `name` | `customers.name` | Keep original | Must not be empty | ✅ |
| `vat` | `customers.tax_code` | String | Validate MST format (10 or 13 digits) | 🔄 |
| `phone` | `customers.phone` | String | | ✅ |
| `mobile` | `customers.phone` | Fallback if phone empty | | 🔄 |
| `email` | `customers.email` | Lowercase | Validate email format | 🔄 |
| `street` | `customers.address` | | | ✅ |
| `city` | `customers.city` | | | ✅ |
| `state_id.name` | `customers.province` | String | | ✅ |
| `country_id.code` | `customers.country` | ISO alpha-2 | Default VN | ✅ |
| `property_payment_term_id.name` | `customers.payment_term_id` | Lookup by name | | 🔄 |
| `credit_limit` | `customers.credit_limit` | Numeric | Must be ≥ 0 | ✅ |
| `active` | `customers.is_active` | Boolean | | ✅ |
| `id` | `customers.odoo_id` | Integer | Migration audit only | ✅ |
| `customer_rank` | — | Filter condition only | Must be > 0 | ❌ |

---

## Partners — `res.partner` (Suppliers — supplier_rank > 0)

| Odoo Field | TradeCore Table.Column | Transform | Validation | Status |
|---|---|---|---|---|
| `ref` | `suppliers.code` | NCC-XXXX | Must not be empty | ✅ |
| `name` | `suppliers.name` | Keep original | | ✅ |
| `country_id.code` | `suppliers.country` | ISO alpha-2 | | ✅ |
| `vat` | `suppliers.tax_code` | String | May be foreign VAT | ✅ |
| `phone` | `suppliers.phone` | | | ✅ |
| `email` | `suppliers.email` | Lowercase | | 🔄 |
| `street` | `suppliers.address` | | | ✅ |
| `child_ids[type=contact].name` | `suppliers.contact_name` | First contact | | 🔄 |
| `active` | `suppliers.is_active` | Boolean | | ✅ |
| `id` | `suppliers.odoo_id` | Integer | Migration audit only | ✅ |

---

## Units of Measure — `uom.uom`

| Odoo Field | TradeCore Table.Column | Transform | Status |
|---|---|---|---|
| `name` | `units_of_measure.name` | Trim | ✅ |
| `category_id.name` | `units_of_measure.category` | Map to UoMCategory enum | 🔄 |
| `factor` | `units_of_measure.factor` | Numeric | ✅ |
| `uom_type` | `units_of_measure.uom_type` | Map to UoMType enum | 🔄 |
| `active` | `units_of_measure.is_active` | Boolean | ✅ |

---

## Sales Orders — `sale.order`

| Odoo Field | TradeCore Table.Column | Transform | Status |
|---|---|---|---|
| `name` | `sales_orders.order_number` | Keep | ✅ |
| `partner_id.ref` | `sales_orders.customer_id` | Lookup by customer.code | 🔄 |
| `date_order` | `sales_orders.date` | Date | ✅ |
| `validity_date` | `sales_orders.due_date` | Date | ✅ |
| `currency_id.name` | `sales_orders.currency_id` | Lookup by currency.code | 🔄 |
| `payment_term_id.name` | `sales_orders.payment_term_id` | Lookup by name | 🔄 |
| `amount_untaxed` | `sales_orders.subtotal` | Numeric | ✅ |
| `amount_tax` | `sales_orders.tax_amount` | Numeric | ✅ |
| `amount_total` | `sales_orders.total` | Numeric | ✅ |
| `state` | `sales_orders.status` | `draft`→`draft`, `sent`→`pending`, `sale`→`confirmed`, `done`→`completed`, `cancel`→`cancelled` | 🔄 |
| `note` | `sales_orders.notes` | Text | ✅ |
| `id` | `sales_orders.odoo_id` | Integer | ✅ |

### Sales Order Lines — `sale.order.line`

| Odoo Field | TradeCore Table.Column | Transform | Status |
|---|---|---|---|
| `sequence` | `sales_order_items.line_no` | Integer | ✅ |
| `product_id.default_code` | `sales_order_items.product_id` | Lookup by product.code | 🔄 |
| `name` | `sales_order_items.description` | Text | ✅ |
| `product_uom_qty` | `sales_order_items.qty` | Numeric | ✅ |
| `product_uom.name` | `sales_order_items.uom_id` | Lookup | 🔄 |
| `price_unit` | `sales_order_items.unit_price` | Numeric | ✅ |
| `discount` | `sales_order_items.discount_percent` | Numeric (0–100) | ✅ |
| `price_subtotal` | `sales_order_items.subtotal` | Numeric | ✅ |

---

## Purchase Orders — `purchase.order`

| Odoo Field | TradeCore Table.Column | Transform | Status |
|---|---|---|---|
| `name` | `purchase_orders.order_number` | Keep | ✅ |
| `partner_id.ref` | `purchase_orders.supplier_id` | Lookup by supplier.code | 🔄 |
| `date_order` | `purchase_orders.date` | Date | ✅ |
| `date_planned` | `purchase_orders.expected_date` | Date | ✅ |
| `currency_id.name` | `purchase_orders.currency_id` | Lookup | 🔄 |
| `payment_term_id.name` | `purchase_orders.payment_term_id` | Lookup | 🔄 |
| `amount_untaxed` | `purchase_orders.subtotal` | Numeric | ✅ |
| `amount_tax` | `purchase_orders.tax_amount` | Numeric | ✅ |
| `amount_total` | `purchase_orders.total` | Numeric | ✅ |
| `state` | `purchase_orders.status` | `draft`→`draft`, `sent`→`pending`, `purchase`→`confirmed`, `done`→`completed`, `cancel`→`cancelled` | 🔄 |
| `id` | `purchase_orders.odoo_id` | Integer | ✅ |

---

## Stock Movements — `stock.move` / `stock.move.line`

| Odoo Field | TradeCore Table.Column | Notes | Status |
|---|---|---|---|
| `product_id.default_code` | `stock_movements.product_id` | Lookup by product.code | 🔄 |
| `product_uom_qty` | `stock_movements.qty` | Numeric | ✅ |
| `product_uom.name` | `stock_movements.uom_id` | Lookup | 🔄 |
| `location_id.complete_name` | `stock_movements.from_location_id` | Map to WH location | 🔄 |
| `location_dest_id.complete_name` | `stock_movements.to_location_id` | Map to WH location | 🔄 |
| `date` | `stock_movements.moved_at` | Datetime | ✅ |
| `origin` | `stock_movements.reference` | Order number string | ✅ |
| `picking_type_id.code` | `stock_movements.movement_type` | `incoming`→`receive`, `outgoing`→`issue`, `internal`→`transfer` | 🔄 |

---

## Open Questions (Field Mapping)

⚠️ These require actual Odoo export data to confirm:

1. How are customer codes (`ref` field) formatted in Odoo? Do they already follow KH-XXXX?
2. How are supplier codes formatted? Do they already follow NCC-XXXX?
3. Are pricelists used in Odoo? What currency and structure?
4. Are stock locations in Odoo already cleaned up, or do they have legacy data?
5. Is `product.default_code` always populated, or are some products code-less?
6. How are payment terms named in Odoo (exact strings needed for lookup)?
