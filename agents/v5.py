"""Kaggriculture agent v5 - goose engine fed by home-grown fertilized wheat.

Economics (derived from the engine source):
  * EGG price is a log curve: 5,000 eggs sold still fetch ~$35 -> unlimited sink.
  * Fed + cared goose = 2 eggs/day, 1 fertilizer/day. Needs 1 wheat/day.
  * Buying wheat pushes its price up fast (sqrt curve) and the town eats wheat too,
    so feed must be home-grown: fertilized wheat = 5 units per 3-day cycle.
  * Fertilizer is a shared, never-replenished pool (~$25k): sell early, then
    spend it on wheat once the price has collapsed.
  * Labour (fibonacci hire cost) is the binding constraint.
"""

GOOSE_COST = 300
LAND_PRICES = [1000, 2000, 4000]
LAST_STEP = 718

P = {
    "w_goose": 4.3,          # turns/day a goose costs (ops + walking)
    "w_wheat": 3.0,          # turns/day a wheat tile costs
    "turns_per_unit": 18.0,
    "max_units": 14,
    "last_goose_day": 21,
    "last_land_day": 19,
    "last_plant_day": 26,
    "fert_sell_min": 30,     # below this price, keep fertilizer for wheat
    "feed_cash_days": 1.2,
    "wheat_ring": 1,         # outer rings of each quadrant used for wheat
}

MEM = {"day": -1, "owner": {}, "planned": 1}


def g(d, k, default=None):
    if isinstance(d, dict):
        return d.get(k, default)
    return getattr(d, k, default)


def shed_tiles(n):
    h = n // 2
    return [(h - 1, h - 1), (h, h - 1), (h - 1, h), (h, h)]


def dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def step_toward(pos, tgt):
    x, y = pos
    tx, ty = tgt
    if tx > x:
        return "EAST"
    if tx < x:
        return "WEST"
    if ty > y:
        return "SOUTH"
    if ty < y:
        return "NORTH"
    return "PASS"


_ORDER = {}


def tile_order(n):
    """Serpentine order per quadrant starting at the shed corner."""
    if n in _ORDER:
        return _ORDER[n]
    h = n // 2
    order = []
    for q in ["NW", "NE", "SW", "SE"]:
        xs = list(range(h - 1, -1, -1)) if q[1] == "W" else list(range(h, n))
        ys = list(range(h - 1, -1, -1)) if q[0] == "N" else list(range(h, n))
        for i, y in enumerate(ys):
            row = xs if i % 2 == 0 else xs[::-1]
            for x in row:
                order.append((x, y))
    _ORDER[n] = order
    return order


def role(x, y, n):
    h = n // 2
    qx = x if x < h else n - 1 - x
    qy = y if y < h else n - 1 - y
    return "WHEAT" if min(qx, qy) < P["wheat_ring"] else "GOOSE"


def agent(obs, config=None):
    me = g(obs, "farms")[g(obs, "player", 0)]
    priv = g(obs, "private")
    prices = g(g(obs, "market"), "prices")
    day = g(obs, "day", 0)
    hour = g(obs, "hour", 0)
    step = g(obs, "step", day * 24 + hour)
    tiles = me["tiles"]
    n = len(tiles)
    money = me["money"]
    shed = dict(g(priv, "shed") or {})
    seeds = dict(g(priv, "seeds") or {})
    units = [tuple(me["farmer"])] + [tuple(h) for h in me["hands"]]
    invs = [dict(i) for i in (g(priv, "inventories") or [{}])]
    while len(invs) < len(units):
        invs.append({})
    steps_left = LAST_STEP - step
    SH = shed_tiles(n)
    feed_on = day <= 28
    care_on = day <= 27
    fert_price = prices["FERTILIZER"]

    def home(p):
        return min(SH, key=lambda s: dist(p, s))

    # ---------------- survey ----------------
    geese, ecoops, eg, ew, wheat, weeds = [], [], [], [], [], []
    for (x, y) in tile_order(n):
        t = tiles[y][x]
        if t == "LOCKED":
            continue
        r = role(x, y, n)
        if t is None:
            (eg if r == "GOOSE" else ew).append((x, y))
        elif t["kind"] == "WEED":
            weeds.append((x, y))
        elif t["kind"] == "PLANT":
            wheat.append((x, y))
        elif "animal" in t:
            geese.append((x, y))
        else:
            ecoops.append((x, y))
    g_wait = shed.get("GOOSE", 0) + sum(i.get("GOOSE", 0) for i in invs)
    n_geese = len(geese) + g_wait

    # ---------------- tasks per tile ----------------
    def goose_ops(p):
        t = tiles[p[1]][p[0]]
        L = []
        if feed_on and not t["fed_today"]:
            L.append("FEED")
        if care_on and not t["cared_today"]:
            L.append("CARE")
        y = t["yield_units"]
        if y >= 3 or (y > 0 and (day >= 29 or (day == 28 and hour >= 18))):
            L.append("HARVEST")
        if t["fertilizer_available"] and steps_left > 6:
            L.append("COLLECT_FERTILIZER")
        return L

    def wheat_ops(p):
        t = tiles[p[1]][p[0]]
        age = day - t["planted_day"]
        L = []
        fert_active = t["fertilized_until_day"] >= day
        if age == 2 and not fert_active and not t["watered_today"]:
            L.append("FERTILIZE")
        if not t["watered_today"] and day < 29:
            L.append("WATER")
        ready = (age >= 3 and t["fertilized_until_day"] >= 0) or age >= 4
        if ready and (t["watered_today"] or "WATER" not in L):
            L.append("HARVEST")
        elif ready:
            L.append("HARVEST")  # after WATER in same visit
        if day >= 29 and age >= 2:
            L = ["HARVEST"]
        return L

    work = {}  # tile -> ops
    for p in geese:
        work[p] = ("G", goose_ops(p))
    for p in wheat:
        work[p] = ("W", wheat_ops(p))
    plantable = day <= P["last_plant_day"]
    n_seed = seeds.get("WHEAT", 0)
    for p in ew[:n_seed if plantable else 0]:
        work[p] = ("W", ["PLANT"])

    # ---------------- ownership: planned once per day ----------------
    if MEM["day"] != day:
        MEM["day"] = day
        MEM["owner"] = {}
    planned = max(MEM.get("planned", 1), len(units))
    if not MEM["owner"] or MEM.get("nwork") != len(work) or MEM.get("np") != planned:
        items = [p for p in tile_order(n) if p in work]
        wts = [P["w_goose"] if work[p][0] == "G" else P["w_wheat"] for p in items]
        tot = sum(wts) or 1.0
        # farmer does flex jobs (coops, placing, weeds) -> smaller share
        shares = [0.35 if planned > 3 else 1.0] + [1.0] * (planned - 1)
        st = sum(shares)
        bounds, acc = [], 0.0
        for s in shares:
            acc += s
            bounds.append(acc / st * tot)
        owner, acc, u = {}, 0.0, 0
        for p, w in zip(items, wts):
            while u < planned - 1 and acc + w / 2 > bounds[u]:
                u += 1
            owner[p] = u
            acc += w
        MEM.update(owner=owner, nwork=len(work), np=planned)
    owner = MEM["owner"]

    # flex jobs (farmer first, anyone idle later)
    coops_needed = max(0, g_wait + 2 - len(ecoops)) if day <= P["last_goose_day"] else 0
    flex = {}
    for p in eg[:coops_needed]:
        flex[p] = "BUILD_COOP"
    for p in weeds:
        flex[p] = "DIG"

    # ---------------- unit actions ----------------
    acts = []
    claimed = set()
    shed_av = dict(shed)
    for ui, pos in enumerate(units):
        inv = invs[ui]
        mine = [(p, work[p]) for p in work if owner.get(p) == ui and work[p][1]]
        need_w = sum(1 for p, (k, L) in mine if "FEED" in L)
        need_f = sum(1 for p, (k, L) in mine if "FERTILIZE" in L)
        cw, cf = inv.get("WHEAT", 0), inv.get("FERTILIZER", 0)
        eggs = inv.get("EGG", 0)
        act = None

        if pos in SH:
            spare_f = cf - need_f
            spare_w = cw - need_w
            if eggs and (eggs >= 3 or not mine or steps_left < 24):
                act = ["PLACE", "EGG", eggs]
            elif cw < need_w and shed_av.get("WHEAT", 0) > 0:
                k = min(need_w - cw, shed_av["WHEAT"])
                shed_av["WHEAT"] -= k
                act = ["PICKUP", "WHEAT", k]
            elif cf < need_f and shed_av.get("FERTILIZER", 0) > 0:
                k = min(need_f - cf, shed_av["FERTILIZER"])
                shed_av["FERTILIZER"] -= k
                act = ["PICKUP", "FERTILIZER", k]
            elif spare_f >= 3 or (spare_f > 0 and not mine):
                act = ["PLACE", "FERTILIZER", spare_f]
            elif spare_w >= 4 or (spare_w > 0 and not mine and hour >= 20):
                act = ["PLACE", "WHEAT", spare_w]
            elif ui == 0 and shed_av.get("GOOSE", 0) > 0 and not inv.get("GOOSE") and (ecoops or eg):
                k = shed_av["GOOSE"]
                shed_av["GOOSE"] -= k
                act = ["PICKUP", "GOOSE", k]
        if act:
            acts.append(act)
            continue

        def doable(L):
            out = []
            for o in L:
                if o == "FEED" and inv.get("WHEAT", 0) <= 0:
                    continue
                if o == "FERTILIZE" and inv.get("FERTILIZER", 0) <= 0:
                    continue
                if o == "PLANT" and n_seed <= 0:
                    continue
                out.append(o)
            return out

        target, ops = None, None
        if ui == 0 and inv.get("GOOSE", 0) > 0:
            spots = [(dist(pos, p), p, ["PLACE_GOOSE"]) for p in ecoops if p not in claimed] + \
                    [(dist(pos, p) + 1, p, ["BUILD_COOP"]) for p in eg if p not in claimed]
            if spots:
                spots.sort()
                _, tp, o = spots[0]
                claimed.add(tp)
                acts.append([step_toward(pos, tp)] if tp != pos else (["PLACE", "GOOSE", 1] if o == ["PLACE_GOOSE"] else ["BUILD_COOP"]))
                continue
        if ui == 0 and not inv.get("GOOSE") and shed.get("GOOSE", 0) > 0:
            acts.append([step_toward(pos, home(pos))] if pos not in SH else ["PASS"])
            continue
        cands = []
        for p, (k, L) in mine:
            if p in claimed:
                continue
            D = doable(L)
            if not D:
                continue
            if D == ["FERTILIZE"]:
                continue
            urgent = ("FEED" in D or "WATER" in D) and hour >= 16
            cands.append((dist(pos, p) - (3 if urgent else 0), p, D))
        # waiting on items -> go to shed
        blocked = (need_w > cw and shed.get("WHEAT", 0) + 0 >= 0) or (need_f > cf and shed.get("FERTILIZER", 0) > 0)
        if cands:
            cands.sort()
            _, target, ops = cands[0]
            if blocked and dist(pos, home(pos)) < cands[0][0] and need_w > cw:
                target, ops = home(pos), None
        elif blocked:
            target = home(pos)
        else:
            # flex / help
            fc = []
            if ui == 0 and inv.get("GOOSE", 0):
                for p in ecoops:
                    if p not in claimed:
                        fc.append((dist(pos, p), p, ["PLACE_GOOSE"]))
            if ui == 0 and not inv.get("GOOSE") and shed_av.get("GOOSE", 0) > 0 and ecoops:
                fc.append((dist(pos, home(pos)), home(pos), None))
            for p, op in flex.items():
                if p not in claimed:
                    fc.append((dist(pos, p) + (0 if ui == 0 else 3), p, [op]))
            spare_w = inv.get("WHEAT", 0)
            for p, (k, L) in work.items():
                if owner.get(p) == ui or p in claimed or not L:
                    continue
                D = [o for o in doable(L) if o != "FERTILIZE"]
                if "FEED" in D and spare_w > 0:
                    fc.append((dist(pos, p), p, D))
                elif D and hour >= 10:
                    fc.append((dist(pos, p) + 4, p, [o for o in D if o != "FEED"] or D))
            if fc:
                fc.sort(key=lambda z: z[0])
                _, target, ops = fc[0]
        carry = inv.get("EGG", 0) + max(0, inv.get("FERTILIZER", 0) - need_f)
        if carry and steps_left <= dist(pos, home(pos)) + 3:
            target, ops = home(pos), None
        if target is None:
            if carry and (hour >= 18 or carry >= 8):
                target = home(pos)
            else:
                acts.append(["PASS"])
                continue
        claimed.add(target)
        if pos != target:
            acts.append([step_toward(pos, target)])
            continue
        if ops is None:
            if inv.get("EGG"):
                acts.append(["PLACE", "EGG", inv["EGG"]])
            elif inv.get("FERTILIZER", 0) > need_f:
                acts.append(["PLACE", "FERTILIZER", inv["FERTILIZER"] - need_f])
            else:
                acts.append(["PASS"])
            continue
        op = ops[0]
        if op == "PLACE_GOOSE":
            acts.append(["PLACE", "GOOSE", 1])
        elif op == "PLANT":
            n_seed -= 1
            acts.append(["PLANT", "WHEAT"])
        else:
            acts.append([op])

    # ---------------- market ----------------
    orders = []
    wp = max(prices["WHEAT"], 20)
    unfed_all = sum(1 for p in geese if not tiles[p[1]][p[0]]["fed_today"]) + g_wait
    wheat_have = shed.get("WHEAT", 0) + sum(i.get("WHEAT", 0) for i in invs)
    # sells (skip at hour 0 to leave order slots for purchases; hour-0 shed sells at hour 1)
    if hour != 0 or day >= 29:
        orders.append(["SELL", "EGG", 10000])
        fert_keep = 0 if day >= 28 else max(0, sum(1 for p in wheat if tiles[p[1]][p[0]]["fertilized_until_day"] < 0) + len(ew) // 2)
        fs = shed.get("FERTILIZER", 0) - (fert_keep if fert_price < P["fert_sell_min"] else min(fert_keep, 6))
        if fs > 0:
            orders.append(["SELL", "FERTILIZER", fs])
        reserve_w = 0 if day >= 29 else (n_geese + 2 if hour >= 20 else unfed_all)
        ws = shed.get("WHEAT", 0) - reserve_w
        if ws > 0 and (hour >= 20 or day >= 29):
            orders.append(["SELL", "WHEAT", ws])
    cash = money
    if feed_on and hour <= 21:
        need = (n_geese if hour == 0 else unfed_all) - wheat_have
        if hour >= 1:
            deficit = 0
            for ui in range(len(units)):
                mu = sum(1 for p in geese if owner.get(p) == ui and not tiles[p[1]][p[0]]["fed_today"])
                deficit += max(0, mu - invs[ui].get("WHEAT", 0))
            need = max(need, deficit - shed.get("WHEAT", 0))
        if need > 0:
            orders.append(["BUY_PRODUCT", "WHEAT", need])
            cash -= need * wp * 1.1
    if hour == 0:
        # wheat seeds for empty wheat tiles
        if day <= P["last_plant_day"]:
            k = min(max(0, len(ew) - seeds.get("WHEAT", 0)), int(max(0, cash) // 12))
            if k > 0:
                orders.append(["BUY_SEED", "WHEAT", k])
                cash -= 10 * k
    if hour <= 1 and day <= 29:
        if hour == 0:
            wl = len(geese) * P["w_goose"] + (len(wheat) + len(ew)) * P["w_wheat"] \
                + g_wait * (P["w_goose"] + 3) + 8
            MEM["want"] = min(P["max_units"], int(wl / P["turns_per_unit"] + 0.999))
        want = MEM.get("want", 1)
        have_h = me["hires_today"]
        a, b = 1, 1
        for _ in range(have_h):
            a, b = b, a + b
        spend, k = 0, 0
        slots = 10 - len(orders) - (2 if hour == 0 else 0)
        while have_h + k < want - 1 and k < slots and spend + a <= max(60 if a <= 21 else 0, cash - n_geese * wp * 0.7):
            spend += a
            a, b = b, a + b
            k += 1
        orders += [["HIRE"]] * k
        cash -= spend
        if hour == 0:
            MEM["planned"] = want
            MEM["owner"] = {}
    if hour <= 12 and day <= P["last_goose_day"]:
        wl = len(geese) * P["w_goose"] + (len(wheat) + len(ew)) * P["w_wheat"]
        cap = P["max_units"] * P["turns_per_unit"]
        free = len(eg) + len(ecoops) - g_wait
        reserve = n_geese * wp * P["feed_cash_days"] + 50
        nq = len(me["unlocked_quadrants"])
        if free < 3 and nq < 4 and day <= P["last_land_day"] and wl + 16 * P["w_goose"] < cap:
            price = LAND_PRICES[nq - 1]
            if cash - reserve >= price + 2 * GOOSE_COST:
                orders.append(["BUY_LAND"])
                cash -= price
                free += 16
        k = int((cash - reserve) // (GOOSE_COST + wp))
        k = min(k, free, int(max(0, cap - wl) / P["w_goose"]))
        if hour > 0:
            k = min(k, 4)
        if k > 0:
            orders.append(["BUY_ANIMAL", "GOOSE", k])
            orders.append(["BUY_PRODUCT", "WHEAT", k])
            cash -= k * (GOOSE_COST + wp)
    return {"farmer": acts[0], "hands": acts[1:], "market": orders[:10]}
