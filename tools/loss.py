import sys, importlib.util, collections
from kaggle_environments import make
spec = importlib.util.spec_from_file_location("m", sys.argv[1]); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
seed=int(sys.argv[2]) if len(sys.argv)>2 else 100
env = make("kaggriculture", configuration={"seed": seed}, debug=True)
env.run([m.agent, "starter"])
S=env.steps
tot=collections.Counter()
for d in range(29):
    o=S[d*24+23][0].observation  # state before last action of day... use obs at hour 23
    f=o.farms[0]; T=f['tiles']
    G=[t for r in T for t in r if isinstance(t,dict) and 'animal' in t]
    capped=sum(1 for t in G if t['yield_units']>=3)   # would lose eggs at EOD (yield 3->4 loses 1, 4 loses 2)
    unfed=sum(1 for t in G if not t['fed_today'])
    uncared=sum(1 for t in G if not t['cared_today'])
    nocoll=sum(1 for t in G if t['fertilizer_available'])
    esc=sum(1 for t in G if not t['fed_today'] and t['consecutive_unfed']>=1)
    tot['capped']+=capped; tot['esc']+=esc; tot['unfed']+=unfed
    if d%3==0 or esc: print(f"d{d} geese={len(G)} unharvested>=3:{capped} unfed:{unfed} (escaping:{esc}) uncared:{uncared} uncollected:{nocoll} shedG={o.private['shed'].get('GOOSE')} hands={len(f['hands'])} money={f['money']:.0f}")
print(tot, 'final', S[-1][0].reward)
