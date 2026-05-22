# Olist Brazilian E-Commerce Dataset — Schema Reference

This dataset contains information about ~100K orders placed on the [Olist](https://olist.com/) Brazilian e-commerce marketplace between 2016 and 2018.

---

## Entity Relationship Diagram

```
                    ┌──────────────┐
                    │  customers   │
                    │──────────────│
                    │ customer_id  │◄─────────┐
                    │ unique_id    │           │
                    │ zip_code     │           │
                    │ city, state  │           │
                    └──────────────┘           │
                                              │
┌──────────────┐    ┌──────────────┐          │
│   payments   │    │    orders    │          │
│──────────────│    │──────────────│          │
│ order_id     │───►│ order_id     │──────────┘
│ payment_type │    │ customer_id  │
│ value        │    │ status       │
│ installments │    │ purchase_ts  │
└──────────────┘    │ delivered_ts │
                    │ estimated_ts │
┌──────────────┐    └──────┬───────┘
│   reviews    │           │
│──────────────│           │
│ order_id     │───────────┘
│ score        │           │
│ comment      │           │
└──────────────┘           │
                           │
                    ┌──────▼───────┐    ┌──────────────┐
                    │ order_items  │    │   products   │
                    │──────────────│    │──────────────│
                    │ order_id     │    │ product_id   │◄──┐
                    │ product_id   │───►│ category     │   │
                    │ seller_id    │    │ weight, dims │   │
                    │ price        │    └──────────────┘   │
                    │ freight_value│                        │
                    └──────┬───────┘    ┌──────────────┐   │
                           │            │  category    │   │
                    ┌──────▼───────┐    │  translation │   │
                    │   sellers    │    │──────────────│   │
                    │──────────────│    │ pt_name ─────┼───┘
                    │ seller_id    │    │ en_name      │
                    │ zip_code     │    └──────────────┘
                    │ city, state  │
                    └──────────────┘

    ┌──────────────┐
    │ geolocation  │  (standalone — join via zip_code_prefix)
    │──────────────│
    │ zip_code     │
    │ lat, lng     │
    │ city, state  │
    └──────────────┘
```

---

## Tables

### `olist_orders_dataset.csv`

Each row is one order.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `order_id` | string | Unique order identifier | `e481f51cbdc54678b7cc49136f2d6af7` |
| `customer_id` | string | FK to customers table | `9ef432eb6251297304e76186b10a928d` |
| `order_status` | string | Order status | `delivered`, `shipped`, `canceled` |
| `order_purchase_timestamp` | datetime | When the order was placed | `2017-10-02 10:56:33` |
| `order_approved_at` | datetime | When payment was approved | `2017-10-02 11:07:15` |
| `order_delivered_carrier_date` | datetime | When handed to carrier | `2017-10-04 19:55:00` |
| `order_delivered_customer_date` | datetime | Actual delivery date | `2017-10-10 21:25:13` |
| `order_estimated_delivery_date` | datetime | Estimated delivery date | `2017-10-18 00:00:00` |

**Notes:** `order_status` values include: `delivered`, `shipped`, `processing`, `canceled`, `unavailable`, `invoiced`, `created`, `approved`. Most orders (~97%) are `delivered`.

---

### `olist_order_items_dataset.csv`

Each row is one item within an order. An order can have multiple items.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `order_id` | string | FK to orders | `e481f51cbdc54678b7cc49136f2d6af7` |
| `order_item_id` | int | Sequential item number within order | `1` |
| `product_id` | string | FK to products | `87285b34884572647811a353c7ac498a` |
| `seller_id` | string | FK to sellers | `1025f0e2d44d7041d6cf58b6550e40de` |
| `shipping_limit_date` | datetime | Seller shipping deadline | `2017-10-06 11:07:15` |
| `price` | float | Item price (BRL) | `29.99` |
| `freight_value` | float | Freight cost (BRL) | `8.72` |

---

### `olist_products_dataset.csv`

Each row is one product.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `product_id` | string | Unique product identifier | `87285b34884572647811a353c7ac498a` |
| `product_category_name` | string | Category in Portuguese | `informatica_acessorios` |
| `product_name_length` | int | Characters in product name | `40` |
| `product_description_length` | int | Characters in description | `287` |
| `product_photos_qty` | int | Number of photos | `1` |
| `product_weight_g` | int | Weight in grams | `225` |
| `product_length_cm` | int | Length in cm | `16` |
| `product_height_cm` | int | Height in cm | `10` |
| `product_width_cm` | int | Width in cm | `14` |

**Notes:** `product_category_name` is in Portuguese. Use the translation table to get English names. Some products have null category.

---

### `olist_sellers_dataset.csv`

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `seller_id` | string | Unique seller identifier | `1025f0e2d44d7041d6cf58b6550e40de` |
| `seller_zip_code_prefix` | string | First 5 digits of zip | `13023` |
| `seller_city` | string | Seller city | `campinas` |
| `seller_state` | string | 2-letter state code | `SP` |

---

### `olist_customers_dataset.csv`

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `customer_id` | string | FK used in orders table | `9ef432eb6251297304e76186b10a928d` |
| `customer_unique_id` | string | Unique customer (may have multiple customer_ids) | `7c396fd4830fd04220f754e42b4e5bff` |
| `customer_zip_code_prefix` | string | First 5 digits of zip | `01151` |
| `customer_city` | string | Customer city | `sao paulo` |
| `customer_state` | string | 2-letter state code | `SP` |

**Notes:** A single `customer_unique_id` can have multiple `customer_id` values (one per order). Use `customer_unique_id` for customer-level analysis.

---

### `olist_order_reviews_dataset.csv`

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `review_id` | string | Unique review identifier | `7bc2406110b926393aa56f80a40eba40` |
| `order_id` | string | FK to orders | `73fc7af87114b39712e6da79b0a377eb` |
| `review_score` | int | Rating from 1 to 5 | `4` |
| `review_comment_title` | string | Review title (nullable) | `null` |
| `review_comment_message` | string | Review text (nullable) | `Recebi bem antes do prazo` |
| `review_creation_date` | datetime | When review was submitted | `2018-01-18 00:00:00` |
| `review_answer_timestamp` | datetime | When review was posted | `2018-01-18 21:46:59` |

**Notes:** Review comments are in Portuguese. Not all orders have reviews. Score 1 = worst, 5 = best.

---

### `olist_order_payments_dataset.csv`

Each row is one payment for an order. An order can have multiple payments (e.g., credit card + voucher).

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `order_id` | string | FK to orders | `b81ef226f3fe1789b1e8b2acac839d17` |
| `payment_sequential` | int | Payment sequence number | `1` |
| `payment_type` | string | Payment method | `credit_card`, `boleto`, `voucher`, `debit_card` |
| `payment_installments` | int | Number of installments | `8` |
| `payment_value` | float | Transaction value (BRL) | `99.33` |

---

### `olist_geolocation_dataset.csv`

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `geolocation_zip_code_prefix` | string | First 5 digits of zip | `01037` |
| `geolocation_lat` | float | Latitude | `-23.54562` |
| `geolocation_lng` | float | Longitude | `-46.63929` |
| `geolocation_city` | string | City name | `sao paulo` |
| `geolocation_state` | string | 2-letter state code | `SP` |

**Notes:** Multiple lat/lng entries per zip code (one per delivery in that area). Has duplicates — deduplicate before use.

---

### `product_category_name_translation.csv`

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `product_category_name` | string | Category in Portuguese | `informatica_acessorios` |
| `product_category_name_english` | string | Category in English | `computers_accessories` |

---

## Key Join Paths

| From | To | Join Key |
|------|----|----------|
| `orders` | `order_items` | `order_id` |
| `orders` | `customers` | `customer_id` |
| `orders` | `reviews` | `order_id` |
| `orders` | `payments` | `order_id` |
| `order_items` | `products` | `product_id` |
| `order_items` | `sellers` | `seller_id` |
| `products` | `category_translation` | `product_category_name` |
| `customers` / `sellers` | `geolocation` | `zip_code_prefix` |

## Data Quirks

- **Currency**: All monetary values are in BRL (Brazilian Real).
- **Dates**: Timestamps are in UTC-3 (Brasilia time).
- **Date range**: Orders span roughly September 2016 to August 2018.
- **Nulls**: `product_category_name`, review comments, and some delivery dates can be null.
- **Multiple payments**: One order can have multiple payment rows (split payments).
- **Geolocation duplicates**: Multiple lat/lng per zip code — aggregate or deduplicate.
