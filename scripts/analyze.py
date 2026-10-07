from common import *

def generate(seed=41):
    rng = np.random.default_rng(seed)
    n=2200
    customers=pd.DataFrame({'customer_id':np.arange(1,n+1), 'region':rng.choice(['North','South','East','West'],n), 'channel':rng.choice(['Organic','Paid Search','Referral'],n,p=[.40,.40,.20]), 'signup_month':rng.integers(0,10,n)})
    records=[]
    categories=['Electronics','Home','Apparel','Accessories']
    for c in customers.itertuples():
        affinity=rng.beta(2,3)
        for month in range(c.signup_month,18):
            age=month-c.signup_month
            p=.86 if age==0 else affinity*np.exp(-age/28)
            if rng.random()>p: continue
            for _ in range(1+rng.poisson(.35)):
                cat=rng.choice(categories)
                list_price=rng.lognormal({'Electronics':5.3,'Home':4.5,'Apparel':4.1,'Accessories':3.8}[cat],.4)
                discount=rng.choice([0,.05,.10,.20],p=[.35,.25,.25,.15])
                sale=list_price*(1-discount)
                returned=int(rng.random()<({'Electronics':.06,'Home':.04,'Apparel':.17,'Accessories':.07}[cat]+discount*.12))
                revenue=sale*(1-returned)
                cogs=list_price*{'Electronics':.72,'Home':.48,'Apparel':.35,'Accessories':.30}[cat]*(1-returned)
                fulfillment=5+sale*.015+returned*7
                dt=pd.Timestamp('2024-01-01')+pd.DateOffset(months=month,days=int(rng.integers(0,28)))
                records.append([len(records)+1,c.customer_id,dt.strftime('%Y-%m-%d'),cat,list_price,discount,returned,revenue,cogs,fulfillment,revenue-cogs-fulfillment])
    orders=pd.DataFrame(records,columns=['order_id','customer_id','order_date','category','list_price','discount_rate','returned','net_revenue','cogs','fulfillment_cost','contribution_profit'])
    # Monetary values are rounded once, before all persisted calculations.
    for col in ['list_price','net_revenue','cogs','fulfillment_cost']: orders[col]=orders[col].round(2)
    orders['contribution_profit']=(orders.net_revenue-orders.cogs-orders.fulfillment_cost).round(2)
    customers.to_csv(DATA/'customers.csv',index=False);orders.to_csv(DATA/'orders.csv',index=False)
    return customers,orders

def analyze():
    customers,orders=generate()
    store_db({'customers':customers,'orders':orders})
    df=orders.merge(customers,on='customer_id',validate='many_to_one')
    df['month']=df.order_date.str[:7]
    monthly=df.groupby(['month','region']).agg(orders=('order_id','size'),returns=('returned','sum'),revenue=('net_revenue','sum'),profit=('contribution_profit','sum')).reset_index().rename(columns={'region':'segment'})
    monthly['margin']=monthly.profit/monthly.revenue
    category=df.groupby('category').agg(orders=('order_id','size'),revenue=('net_revenue','sum'),profit=('contribution_profit','sum'),return_rate=('returned','mean')).reset_index()
    category['margin']=category.profit/category.revenue
    save_table(monthly,'monthly_kpis');save_table(category,'category_economics')
    activity=df[['customer_id','month']].drop_duplicates()
    activity['date']=pd.to_datetime(activity.month)
    activity['cohort']=activity.groupby('customer_id').month.transform('min')
    start=pd.to_datetime(activity.cohort)
    activity['age']=(activity.date.dt.year-start.dt.year)*12+activity.date.dt.month-start.dt.month
    cohort=activity.groupby(['cohort','age']).customer_id.nunique().rename('active_customers').reset_index()
    size=cohort[cohort.age==0].set_index('cohort').active_customers
    cohort['cohort_size']=cohort.cohort.map(size);cohort['retention']=cohort.active_customers/cohort.cohort_size
    # Explicitly materialize zero-activity cells; omit future, unobservable months.
    max_month=pd.to_datetime(df.month.max());cells=[]
    for co in sorted(cohort.cohort.unique()):
        d=pd.Timestamp(co);last=(max_month.year-d.year)*12+max_month.month-d.month
        for age in range(last+1): cells.append((co,age))
    cohort=pd.DataFrame(cells,columns=['cohort','age']).merge(cohort,on=['cohort','age'],how='left')
    cohort['cohort_size']=cohort.cohort.map(size);cohort['active_customers']=cohort.active_customers.fillna(0).astype(int);cohort['retention']=cohort.active_customers/cohort.cohort_size
    save_table(cohort,'cohort_retention')
    asof=pd.to_datetime(df.order_date).max()+pd.Timedelta(days=1)
    rfm=df.groupby('customer_id').agg(last_order=('order_date','max'),frequency=('order_id','size'),monetary=('net_revenue','sum'))
    rfm['recency_days']=(asof-pd.to_datetime(rfm.last_order)).dt.days
    rfm['segment']=np.select([(rfm.recency_days<=60)&(rfm.frequency>=8),rfm.recency_days>120],['Champions','At risk'],default='Developing')
    save_table(rfm.reset_index(),'customer_rfm')
    # Rolling one-step forecasts fit only observations before each test month.
    total=monthly.groupby('month',as_index=False)[['orders','revenue','profit']].sum()
    forecasts=[]
    for i in range(9,len(total)):
        hist=total.revenue.iloc[:i].to_numpy();coeff=np.polyfit(np.arange(len(hist)),hist,1)
        forecasts.append([total.month.iloc[i],total.revenue.iloc[i],max(0,float(np.polyval(coeff,i))),float(hist[-1])])
    backtest=pd.DataFrame(forecasts,columns=['month','actual','trend_forecast','naive_forecast']);save_table(backtest,'forecast_backtest')
    wape=lambda col:float(abs(backtest.actual-backtest[col]).sum()/backtest.actual.sum())
    summary={'orders':len(df),'net_revenue':round(df.net_revenue.sum(),2),'contribution_profit':round(df.contribution_profit.sum(),2),'contribution_margin':float(df.contribution_profit.sum()/df.net_revenue.sum()),'return_rate':float(df.returned.mean()),'trend_wape':wape('trend_forecast'),'naive_wape':wape('naive_forecast'),'active_customers':int(df.customer_id.nunique())}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2))
    chart(total,'month','revenue','Net revenue · rolling monthly performance','revenue_trend.png')
    pivot=cohort.pivot(index='cohort',columns='age',values='retention')
    fig,ax=plt.subplots(figsize=(11,5),layout='constrained');im=ax.imshow(pivot,cmap='YlGnBu',vmin=0,vmax=1,aspect='auto');ax.set_yticks(range(len(pivot)),pivot.index);ax.set_xticks(range(len(pivot.columns)),pivot.columns);ax.set_xlabel('Months since first purchase');ax.set_title('Observed cohort retention (blank = future month)');fig.colorbar(im,ax=ax);fig.savefig(OUT/'retention_heatmap.png',dpi=140);plt.close(fig)
    metrics=[dict(label='Net revenue',numerator='revenue',unit='usd'),dict(label='Contribution profit',numerator='profit',unit='usd'),dict(label='Contribution margin',numerator='profit',denominator='revenue',unit='percent'),dict(label='Return rate',numerator='returns',denominator='orders',unit='percent')]
    save_dashboard(monthly.to_dict('records'),metrics,metrics[0],'Retail Growth & Profitability','Connect customer retention, returns, and contribution economics to commercial decisions. January 2024–June 2025. Monetary values are simulated USD.',{},[dict(key='month',label='Month'),dict(key='segment',label='Region'),dict(key='orders',label='Orders',unit='number'),dict(key='revenue',label='Net revenue',unit='usd'),dict(key='profit',label='Profit',unit='usd'),dict(key='margin',label='Margin',unit='percent')])
    worst=category.sort_values('return_rate',ascending=False).iloc[0]
    (OUT/'executive_brief.md').write_text(f'''# Retail decision brief\n\nSynthetic case study — descriptive findings, not real company performance.\n\n- Net revenue: ${summary['net_revenue']:,.2f}; contribution margin: {summary['contribution_margin']:.1%}.\n- {worst['category']} has the highest return rate ({worst['return_rate']:.1%}). Audit sizing, product descriptions, and return reasons before a controlled intervention.\n- Trend forecast WAPE: {summary['trend_wape']:.1%}; last-month baseline: {summary['naive_wape']:.1%}. Select the lower-error approach; this short backtest does not establish long-run accuracy.\n- Use the at-risk RFM export for a randomized retention campaign; historical repeat purchase is not evidence that outreach causes retention.\n\nContribution profit deducts recognized COGS and fulfillment/return costs but excludes acquisition, fixed overhead, and tax. Cohorts start at first observed purchase; customers without a purchase do not enter retention denominators. RFM uses only the observed period.\n''')
    return summary

if __name__=='__main__': print(json.dumps(analyze(),indent=2))
