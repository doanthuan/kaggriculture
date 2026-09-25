import sys, time, importlib.util
from kaggle_environments import make
def load(path):
    spec = importlib.util.spec_from_file_location("m"+str(hash(path)), path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m.agent
a = sys.argv[1]; b = sys.argv[2] if len(sys.argv)>2 else "starter"
seeds = int(sys.argv[3]) if len(sys.argv)>3 else 3
A = load(a); B = load(b) if b.endswith(".py") else b
res=[]
for s in range(seeds):
    env = make("kaggriculture", configuration={"seed": 100+s}, debug=True)
    t=time.time(); env.run([A,B]); dt=time.time()-t
    r=[st.reward for st in env.steps[-1]]
    res.append(r); print(s, r, f"{dt:.1f}s", [st.status for st in env.steps[-1]])
import statistics
print("mean", statistics.mean(x[0] for x in res), statistics.mean(x[1] for x in res))
