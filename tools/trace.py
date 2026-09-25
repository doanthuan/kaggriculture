import sys, importlib.util
from kaggle_environments import make
spec = importlib.util.spec_from_file_location("m", sys.argv[1]); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
env = make("kaggriculture", configuration={"seed": 100}, debug=True)
env.run([m.agent, "starter"])
for st in env.steps[::24]:
    o = st[0].observation; f = o.farms[0]
    geese = sum(1 for r in f["tiles"] for t in r if isinstance(t,dict) and "animal" in t)
    fed = sum(1 for r in f["tiles"] for t in r if isinstance(t,dict) and "animal" in t and t["consecutive_unfed"]>0)
    coops = sum(1 for r in f["tiles"] for t in r if isinstance(t,dict) and t.get("kind")=="COOP")
    wheat = sum(1 for r in f["tiles"] for t in r if isinstance(t,dict) and t.get("kind")=="PLANT")
    weeds = sum(1 for r in f["tiles"] for t in r if isinstance(t,dict) and t.get("kind")=="WEED")
    print(f"d{o.day:2d} ${f['money']:8.0f} geese={geese:2d} unfedYday={fed} coops={coops} wheat={wheat} weeds={weeds} quads={len(f['unlocked_quadrants'])} shed={dict(o.private['shed'])} P={o.market['prices']['EGG']},{o.market['prices']['WHEAT']},{o.market['prices']['FERTILIZER']}")
