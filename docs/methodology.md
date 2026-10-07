# Methodology and limitations


1. Seed 41 generates 2,200 customer profiles and stochastic orders over 18 months. Purchase probability decays with tenure; category returns differ by design. These relationships are intentional simulation assumptions.
2. Money is rounded at input recognition; contribution is recomputed from the rounded components. Refunds eliminate revenue and recognized COGS while retaining fulfillment and return costs.
3. Cohort size is the number of customers whose first observed purchase is in that month. Activity counts distinct customer-months; observed inactive cells are zero, future cells are excluded. Data before the observation window is unavailable.
4. RFM uses observed recency, transaction count, and net monetary value. Thresholds are illustrative business rules, not statistically learned segments.
5. Expanding-window one-step linear forecasts and last-month forecasts are evaluated over the same held-out months. WAPE = sum absolute error / sum actual revenue. Nine test months do not establish robust seasonality or longer-run accuracy.
6. Category profitability and returns are descriptive. Promotions are not randomized; any apparent discount effect is not causal. Proposed retention interventions require control groups and incremental profit measurement.
