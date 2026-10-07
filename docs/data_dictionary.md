# Source data dictionary

All datasets are synthetic; blank values mean missing, not zero.

## customers.csv

| Field | Meaning |
|---|---|
| `customer_id` | Customer identifier; foreign key in orders. |
| `region` | Simulated customer region. |
| `channel` | Simulated acquisition channel. |
| `signup_month` | Zero-based month offset from January 2024; not the retention cohort. |

## orders.csv

| Field | Meaning |
|---|---|
| `order_id` | Unique order identifier. |
| `customer_id` | Customer identifier; foreign key in orders. |
| `order_date` | ISO date of purchase. |
| `category` | Product category. |
| `list_price` | Pre-discount USD price. |
| `discount_rate` | Fractional discount. |
| `returned` | 1 = returned, 0 = retained. |
| `net_revenue` | USD after discount/refund. |
| `cogs` | Recognized USD product cost; refunded orders have zero recognized COGS. |
| `fulfillment_cost` | USD fulfillment and return cost. |
| `contribution_profit` | Net revenue minus COGS and fulfillment. |
