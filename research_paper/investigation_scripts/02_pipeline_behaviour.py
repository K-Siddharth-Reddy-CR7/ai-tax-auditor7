import importlib.util, sys, collections, json
spec=importlib.util.spec_from_file_location('server','/home/user/ai-tax-auditor7/backend/server.py'); S=importlib.util.module_from_spec(spec); spec.loader.exec_module(S)
TX=S.SAMPLE_TRANSACTIONS
# 1. run agentic + normal on all 400 tx
risk=collections.Counter(); costdiff=[]; hsmatch=0; hsmatch_n=0; topcountry=0; topcat=0; ret_scores=[]
for t in TX:
    a=S.run_agentic_auditor_pipeline(t['Product'],t['Destination_Country'],t['Unit_Price_USD'],t['Quantity'],t['Shipping_USD'],t['Origin_Country'])
    n=S.run_normal_auditor_pipeline(t['Product'],t['Destination_Country'],t['Unit_Price_USD'],t['Quantity'],t['Shipping_USD'])
    risk[a['risk_level']]+=1; costdiff.append(round(a['landing_cost']-n['landing_cost'],6))
    hsmatch+= str(a['hs_code'])==str(t['HS_Code']); hsmatch_n+= str(n['hs_code'])==str(t['HS_Code'])
    rp=a['retrieved_policies'][0]; topcountry+= rp['Country']==t['Destination_Country']; topcat+= rp['Category']==a['category']
    ret_scores.append([p['relevance_score'] for p in a['retrieved_policies']])
print('risk levels',risk); print('cost diffs',collections.Counter(costdiff))
print('HS agree w/ tx label agentic',hsmatch,'normal',hsmatch_n)
print('top policy country match',topcountry,'cat match',topcat)
print('distinct score triples',collections.Counter(tuple(s) for s in ret_scores).most_common(6))
# transactions endpoint flags
c=S.app.test_client(); r=c.get('/api/transactions?limit=1000').get_json(); print('tx endpoint total',r['total'], collections.Counter(i['Audit_Status'] for i in r['items']), 'max duty',max(i['Duty_USD'] for i in r['items']))
# 2. edge cases
def A(p,d,pr=100,q=1,s=10):
    try: x=S.run_agentic_auditor_pipeline(p,d,pr,q,s); return (x['product'],x['hs_code'],x['category'],x['matched_country'],x['duty_rate'],x['gst_rate'],x['currency'],x['exchange_rate'],x['risk_level'],x['landing_cost'])
    except Exception as e: return 'ERR '+str(e)
def N(p,d,pr=100,q=1,s=10):
    x=S.run_normal_auditor_pipeline(p,d,pr,q,s); return (x.get('product'),x.get('hs_code'),x.get('destination'),x.get('landing_cost')) if 'error' not in x else x
for p,d in [('Laptop','India'),('laptop','india'),('Gaming Laptop','India'),('notebook computer','India'),('Smartphone','India'),('Mobile Phone','US'),('Laptop','USA'),('Laptop','Niger'),('Laptop','Denmark'),('Laptop','Argentina'),('Cotton T-Shirt','India'),('Car','Germany'),('insulin','India'),('   ','India'),('Laptop','Atlantis'),('Phone','UK'),('Television','Korea'),('Wireless Headphones','China')]:
    print(repr(p),repr(d),'\n   AG',A(p,d),'\n   NO',N(p,d))
print('neg price',A('Laptop','India',-100,1,0)); print('qty 0',A('Laptop','India',100,0,0)); print('qty 2.7',A('Laptop','India',100,2.7,0)); print('qty "2.7"',A('Laptop','India',100,"2.7",0))
# currency coverage
print('missing FX', [t['Currency'] for t in S.TAXES if t['Currency'] not in S.EXCHANGE_RATES])
# compare endpoint
r=c.post('/api/audit/compare',json={'product_name':'Laptop','destination':'India','price':800,'quantity':2,'shipping':100}).get_json(); print('compare cost diff',r['data']['cost_difference'])
# README sample body
r=c.post('/api/audit/agentic',json={"product_name":"Laptop","source_country":"United States","destination":"India","declared_value":850.0,"declared_duty":50.0,"declared_vat":120.0}).get_json(); d=r['data']; print('README body ->',d['price'],d['quantity'],d['shipping'],d['landing_cost'], 'declared keys present?', [k for k in d if 'declared' in k])
print('keys', sorted(d.keys()))
# risk keyword check on every policy
kw=["prohibited","banned","embargo","sanction","license","certificate","bis","ce mark","fda","permit","inspection"]
print('policies triggering any kw', sum(any(k in (p['Compliance_Note']+' '+p['Policy_Summary']).lower() for k in kw) for p in S.TRADE_POLICIES))
