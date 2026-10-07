import unittest, json
from pathlib import Path
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
class SharedChecks(unittest.TestCase):
    def test_dashboard_weighted_kpis_reconcile(self):
        payload=json.loads((ROOT/'outputs/dashboard_data.json').read_text())
        raw=pd.read_csv(ROOT/'outputs/monthly_kpis.csv')
        embedded=pd.DataFrame(payload['rows'])
        pd.testing.assert_frame_equal(raw,embedded,check_dtype=False,atol=1e-5,rtol=1e-5)
        for segment in ['All']+list(raw.segment.unique()):
            rows=embedded if segment=='All' else embedded[embedded.segment==segment]
            self.assertGreater(len(rows),0)
            for m in payload['metrics']:
                value=rows[m['numerator']].sum()
                if 'denominator' in m: value/=rows[m['denominator']].sum()
                self.assertTrue(np.isfinite(value))
        html=(ROOT/'dashboard/index.html').read_text()
        self.assertNotIn('__PAYLOAD__',html)
        self.assertNotIn('<script src=',html)
    def test_inputs_primary_keys(self):
        for filename,key in KEYS.items():
            df=pd.read_csv(ROOT/'data'/filename)
            self.assertFalse(df[key].isna().any())
            self.assertFalse(df[key].duplicated().any())

KEYS={'customers.csv':'customer_id','orders.csv':'order_id'}
class RetailChecks(unittest.TestCase):
    def test_accounting_and_foreign_keys(self):
        o=pd.read_csv(ROOT/'data/orders.csv');c=pd.read_csv(ROOT/'data/customers.csv')
        self.assertTrue(o.customer_id.isin(c.customer_id).all())
        np.testing.assert_allclose(o.contribution_profit,o.net_revenue-o.cogs-o.fulfillment_cost,atol=1e-8)
        self.assertEqual(o.loc[o.returned==1,'net_revenue'].sum(),0)
    def test_sql_python_reconciliation(self):
        py=pd.read_csv(ROOT/'outputs/monthly_kpis.csv').sort_values(['month','segment'])
        sql=pd.read_csv(ROOT/'outputs/sql_result_1.csv').sort_values(['month','region'])
        np.testing.assert_allclose(py.revenue,sql.revenue,atol=1e-5)
        np.testing.assert_allclose(py.profit,sql.profit,atol=1e-5)
        np.testing.assert_array_equal(py.orders,sql.orders)
    def test_cohort_observation_window(self):
        cohort=pd.read_csv(ROOT/'outputs/cohort_retention.csv');orders=pd.read_csv(ROOT/'data/orders.csv')
        self.assertTrue(cohort.retention.between(0,1).all())
        self.assertTrue((cohort.loc[cohort.age==0,'retention']==1).all())
        end=pd.to_datetime(orders.order_date).max()
        for row in cohort.itertuples():
            observed=pd.Timestamp(row.cohort)+pd.DateOffset(months=row.age)
            self.assertLessEqual(observed.to_period('M'),end.to_period('M'))
    def test_forecast_uses_past_only(self):
        rows=pd.read_csv(ROOT/'outputs/monthly_kpis.csv').groupby('month').revenue.sum()
        forecast=pd.read_csv(ROOT/'outputs/forecast_backtest.csv')
        for r in forecast.itertuples():
            hist=rows[rows.index<r.month]
            self.assertAlmostEqual(r.naive_forecast,hist.iloc[-1],places=4)
            expected=max(0,np.polyval(np.polyfit(np.arange(len(hist)),hist,1),len(hist)))
            self.assertAlmostEqual(r.trend_forecast,expected,places=3)

if __name__=='__main__': unittest.main()
