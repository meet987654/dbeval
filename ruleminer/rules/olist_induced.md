## olist (Discovered Business Rules & Schema Invariants)

> Automatically extracted by RuleMiner from database schema signals and historical query logs.

### 3. Discovered Join Paths & Foreign Keys
1. **Join relationship: `order_items.order_id = orders.order_id`.**
2. **Join relationship: `customers.customer_id = orders.customer_id`.**
3. **Join relationship: `order_payments.order_id = orders.order_id`.**
4. **Join relationship: `order_items.product_id = products.product_id`.**
5. **Join relationship: `product_category_name_translation.product_category_name = products.product_category_name`.**
6. **Join relationship: `order_items.seller_id = sellers.seller_id`.**

### 4. Lifecycle States & Status Semantics
7. **Observed lifecycle states for `orders.status`: ['canceled', 'delivered', 'unavailable']. Filter according to question semantics (e.g. active vs canceled/paid).**