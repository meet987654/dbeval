# Business Rules for Olist E-commerce

1. **Customer (a person)**: Always use `customers.customer_unique_id`. The column `customer_id` is created per order, so counting it counts orders, not unique people.
2. **Sales / sold**: Apply to order items on orders whose status is NOT in ('canceled', 'unavailable'). `order_items.price` is the sales amount (freight is NOT sales). Questions about who ordered or order counts count every order unless specified.
3. **Order payment value**: SUM of that order's rows in `order_payments` (orders can have multiple payment rows). Never join `order_payments` directly to `order_items` as that multiplies rows.
4. **Delivered**: `order_status = 'delivered'`.
   **Late**: `order_delivered_customer_date::timestamp > order_estimated_delivery_date::timestamp`.
5. **Delivery time**: Days from `order_purchase_timestamp::timestamp` to `order_delivered_customer_date::timestamp`.
6. **Category**: English name from `product_category_name_translation`. If no translation exists, use Portuguese name. Products with NULL category are ignored for category questions.
7. **Multiple reviews**: If an order has multiple reviews, use the most recent one (`review_creation_date::timestamp`).
8. **Date casting**: Date columns are stored as text; always cast to timestamps (e.g. `::timestamp`) before date comparisons or operations.
