import importlib.util, collections
spec=importlib.util.spec_from_file_location('server','/home/user/ai-tax-auditor7/backend/server.py'); S=importlib.util.module_from_spec(spec); spec.loader.exec_module(S)
P=S.PRODUCTS
selfA=sum(S.product_agent({'product_name':p['Product']})['product']==p['Product'] for p in P)
selfN=sum(S.run_normal_auditor_pipeline(p['Product'],'India',1,1,0)['product']==p['Product'] for p in P)
print('catalog self-match agentic',selfA,'/1200  normal',selfN,'/1200')
bad=[(p['Product'],S.product_agent({'product_name':p['Product']})['product']) for p in P if S.product_agent({'product_name':p['Product']})['product']!=p['Product']]
print(bad[:10])
# base types
import re
print('base types', len({re.sub(r' (Standard|Basic|Premium|Pro|Advanced|Lite|Plus|Max|Mini|Ultra|Gen \d|Series [ABC]|Model [XYZ]|2026)$','',p['Product']) for p in P}))
EU=['Germany','France','Italy','Spain','Netherlands','Belgium','Ireland','Portugal','Poland','Austria','Greece','Sweden','Denmark']
print('EU duty rates',{t['Country']:t['Default_Import_Duty_Percent'] for t in S.TAXES if t['Country'] in EU})
