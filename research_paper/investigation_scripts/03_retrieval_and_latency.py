import importlib.util, time, statistics, collections
spec=importlib.util.spec_from_file_location('server','/home/user/ai-tax-auditor7/backend/server.py'); S=importlib.util.module_from_spec(spec); spec.loader.exec_module(S)
R=S.RETRIEVER; TX=S.SAMPLE_TRANSACTIONS
# retrieval without bonus: does cosine alone rank the country/category doc first?
agree=0; cos_top_country=0; cos_top_both=0; exact_avail=0
for t in TX:
    d=S.product_agent({'product_name':t['Product']})
    q=f"{t['Destination_Country']} {d['category']} import policy and compliance requirements"
    nob=R.retrieve(q,top_k=1); wb=R.retrieve(q,top_k=1,country_filter=t['Destination_Country'],category_filter=d['category'])
    agree+= nob[0]['Policy_ID']==wb[0]['Policy_ID']
    cos_top_country+= nob[0]['Country']==t['Destination_Country']
    cos_top_both+= nob[0]['Country']==t['Destination_Country'] and nob[0]['Category']==d['category']
    exact_avail+= any(p['Country']==t['Destination_Country'] and p['Category']==d['category'] for p in S.TRADE_POLICIES)
print('top1 agree with/without bonus',agree,'cosine-only country correct',cos_top_country,'cosine-only country+cat',cos_top_both,'exact (country,cat) policy exists',exact_avail)
cats=collections.Counter(S.product_agent({'product_name':t['Product']})['category'] for t in TX); print('tx categories',cats)
print('vocab size',len(R.idf))
# latency micro-benchmark (investigation only)
def bench(fn,reps=5):
    ts=[]
    for _ in range(reps):
        for t in TX:
            a=time.perf_counter(); fn(t['Product'],t['Destination_Country'],t['Unit_Price_USD'],t['Quantity'],t['Shipping_USD']); ts.append((time.perf_counter()-a)*1000)
    ts.sort(); return statistics.mean(ts), statistics.median(ts), ts[int(.95*len(ts))]
print('agentic mean/median/p95 ms',bench(S.run_agentic_auditor_pipeline)); print('normal  mean/median/p95 ms',bench(S.run_normal_auditor_pipeline))
