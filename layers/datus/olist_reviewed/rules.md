# Business Rules for olist

1. Customer (a person) = customers.customer_unique_id. customer_id is created per order, so counting customer_id counts orders, not people.
2. Sales / sold = order items on orders whose status is not 'canceled' or 'unavailable'. This applies to anything described as sales, sold or revenue, and order_items.price is the sales amount (freight is NOT sales). Questions about who ordered, or how many orders there were, count every order regardless of status unless specified.
3. Order payment value = SUM of that order's rows in order_payments (one order can have several payment rows). Never join payments to items directly; it multiplies rows.
4. Delivered = order_status = 'delivered'. Late = order_delivered_customer_date is after order_estimated_delivery_date.
5. Delivery time = days from order_purchase_timestamp to order_delivered_customer_date.
6. Category = English name from product_category_name_translation. If a category has no translation, use Portuguese name. Products with no category are ignored.
7. If an order has several reviews, use the most recent one (review_creation_date).
8. Date columns are stored as text; cast them to timestamps first.
