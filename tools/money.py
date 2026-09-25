import sys, importlib.util, collections, copy
from kaggle_environments import make
import kaggle_environments.envs.kaggriculture.kaggriculture as K
spec = importlib.util.spec_from_file_location("m", sys.argv[1]); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
led=collections.defaultdict(collections.Counter)
orig=K._commit_unit
cur={'day':0}
def commit(op,item,price,farm,private,market,cap=100):
    ok=orig(op,item,price,farm,private,market,cap)
    if ok and farm is FARM0[0]:
        sign = 1 if op=='SELL' else -1
        led[cur['day']][op+'_'+item]+=sign*price
        led[cur['day']]['n_'+op+'_'+item]+=1
    return ok
K._commit_unit=commit
oh=K._do_hire
def hire(farm,private,bs,mult=1):
    before=farm['money']; oh(farm,private,bs,mult)
    if farm is FARM0[0]: led[cur['day']]['HIRE']-= before-farm['money']
K._do_hire=hire
ol=K._do_buy_land
def land(farm,bs):
    before=farm['money']; ol(farm,bs)
    if farm is FARM0[0]: led[cur['day']]['LAND']-= before-farm['money']
K._do_buy_land=land
FARM0=[None]
oi=K.interpreter
def interp(state,env):
    if hasattr(state[0].observation,'farms') and state[0].observation.farms:
        FARM0[0]=state[0].observation.farms[0]; cur['day']=state[0].observation.get('step',0)//24
    return oi(state,env)
env = make("kaggriculture", configuration={"seed": 100}, debug=True)
env.interpreter=interp
env.run([m.agent,"starter"])
keys=['SELL_EGG','SELL_FERTILIZER','BUY_PRODUCT_WHEAT','n_BUY_PRODUCT_WHEAT','SELL_WHEAT','BUY_ANIMAL_GOOSE','HIRE','LAND']
print('day', *keys)
T=collections.Counter()
for d in range(30):
    print(d, *[led[d][k] for k in keys]); T.update(led[d])
print('TOTAL', *[T[k] for k in keys], 'final', env.steps[-1][0].reward)
