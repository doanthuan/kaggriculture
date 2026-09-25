import sys, importlib.util
from kaggle_environments import make
spec = importlib.util.spec_from_file_location("m", sys.argv[1]); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
D=int(sys.argv[2])
env = make("kaggriculture", configuration={"seed": 100}, debug=True)
env.run([m.agent, "starter"])
for st in env.steps[D*24:D*24+24]:
    o=st[0].observation; f=o.farms[0]
    unfed=[(x,y) for y,r in enumerate(f["tiles"]) for x,t in enumerate(r) if isinstance(t,dict) and "animal" in t and not t["fed_today"]]
    print(f"h{o.hour:2d} units={[tuple(f['farmer'])]+[tuple(h) for h in f['hands']]} inv={[dict(i) for i in o.private['inventories']]} shedW={o.private['shed'].get('WHEAT')} shedG={o.private['shed'].get('GOOSE')} unfed={len(unfed)} act={st[0].action}")
