-- SQLite; run with python scripts/run_sql.py
-- Monthly profitability by region. One customer per customer_id prevents join inflation.
SELECT substr(o.order_date,1,7) AS month, c.region, COUNT(*) AS orders,
       SUM(o.net_revenue) AS revenue, SUM(o.contribution_profit) AS profit,
       SUM(o.contribution_profit)/NULLIF(SUM(o.net_revenue),0) AS margin
FROM orders o JOIN customers c USING(customer_id)
GROUP BY 1,2 ORDER BY 1,2;

-- Cohort retention uses first observed order; future ages are not asserted to be zero.
WITH activity AS (SELECT DISTINCT customer_id, substr(order_date,1,7) AS month FROM orders),
firsts AS (SELECT customer_id, MIN(month) AS cohort FROM activity GROUP BY 1),
sizes AS (SELECT cohort, COUNT(*) AS size FROM firsts GROUP BY 1)
SELECT f.cohort,
       (CAST(substr(a.month,1,4) AS INTEGER)-CAST(substr(f.cohort,1,4) AS INTEGER))*12
       +CAST(substr(a.month,6,2) AS INTEGER)-CAST(substr(f.cohort,6,2) AS INTEGER) AS age,
       COUNT(*) AS active_customers, s.size AS cohort_size, 1.0*COUNT(*)/s.size AS retention
FROM activity a JOIN firsts f USING(customer_id) JOIN sizes s USING(cohort)
GROUP BY 1,2 ORDER BY 1,2;

-- Within-region category revenue rank with a window function.
WITH category AS (
 SELECT c.region,o.category,SUM(o.net_revenue) AS revenue
 FROM orders o JOIN customers c USING(customer_id) GROUP BY 1,2)
SELECT *,DENSE_RANK() OVER(PARTITION BY region ORDER BY revenue DESC) AS revenue_rank FROM category;
