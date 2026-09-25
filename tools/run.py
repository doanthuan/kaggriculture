import sys, time
from kaggle_environments import make
from kaggle_environments.agent import get_last_callable
def load(path):  # Kaggle's rule: the last callable in the file, fresh namespace each call
    return get_last_callable(open(path).read(), path=path) if path.endswith(".py") else path
a = sys.argv[1]; b = sys.argv[2] if len(sys.argv)>2 else "starter"
seeds = int(sys.argv[3]) if len(sys.argv)>3 else 3
res=[]
for s in range(seeds):
    env = make("kaggriculture", configuration={"seed": 100+s}, debug=True)
    A, B = load(a), load(b)
    t=time.time(); env.run([A,B]); dt=time.time()-t
    r=[st.reward for st in env.steps[-1]]
    res.append(r); print(s, r, f"{dt:.1f}s", [st.status for st in env.steps[-1]])
import statistics
print("mean", statistics.mean(x[0] for x in res), statistics.mean(x[1] for x in res))
