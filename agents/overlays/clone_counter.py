# ---------------------------------------------------------------------------
# Clone counter overlay (Kaggriculture), appended to a tetsutani-chassis agent.
#
# Most top public agents play the same farm (same route family), so matches between
# them are decided by who sells premium goods first into the shared market. When the
# opponent's public farm matches ours, this overlay sells now the premium units our
# route tape plans to sell within the next CC["lead"] turns, from shed stock that is
# not already being sold. Every unit moved forward is recorded as a debt and removed
# from our later SELL orders, so total sales are conserved and only happen earlier.
# The overlay only edits market orders; it never touches unit actions. Any failure
# returns the parent's action unchanged.
#
# Idea credit: Rayk Kretzschmar (debt-tracked sale advance, C45/C94) and
# AlekseiProvorov (mirror-gated lead, T4), both public on Kaggle.
# ---------------------------------------------------------------------------
_CC_PARENT = [v for v in list(globals().values()) if callable(v)][-1]
_CC_DEFAULT = {
    "lead": 1,                   # turns of planned sales pulled forward
    "items": ("MILK", "WOOL", "STRAWBERRY", "MELON"),
    "start": 192,                # day 8
    "stop_new": 672,             # no new advances from day 28
    "stop_debt": 696,            # drop all debts before terminal liquidation
    "min_qty": 1,
    "min_price": 2,
    "gate": 0.9,                 # tile similarity needed; 0 = always on
    "skip_tick": False,          # True: never advance across a town-consumption tick
}
try:
    CC  # allow a builder to pre-set overrides
except NameError:
    CC = {}
_CC = dict(_CC_DEFAULT, **CC)
_CC_BOUNDARIES = (144, 648)      # router switches routes at these steps
_CC_STATE = {"debt": {}, "last": -1}
_CC_REPORT = {"turns": 0, "units": 0, "repaid": 0, "gated_off": 0, "errors": 0}


def _cc_sig(tile):
    if tile is None or isinstance(tile, str):
        return tile
    kind = tile.get("kind")
    return "WEED" if kind == "WEED" else (kind, tile.get("crop") or tile.get("animal"))


def _cc_similarity(observation, player):
    farms = observation["farms"]
    mine, theirs = farms[player]["tiles"], farms[1 - player]["tiles"]
    same = total = 0
    for y in range(len(mine)):
        for x in range(len(mine[y])):
            a, b = _cc_sig(mine[y][x]), _cc_sig(theirs[y][x])
            if a == "WEED" or b == "WEED":
                continue
            total += 1
            same += a == b
    return same / total if total else 0.0


def _cc_market(action):
    return [list(o) if isinstance(o, (list, tuple)) else o for o in (action.get("market") or [])]


def _cc_repay(market, debt):
    for order in market:
        if order and order[0] == "SELL" and len(order) >= 3 and debt.get(order[1], 0) > 0:
            cut = min(max(0, int(order[2])), debt[order[1]])
            order[2] = int(order[2]) - cut
            debt[order[1]] -= cut
            _CC_REPORT["repaid"] += cut
    for item in [k for k, v in debt.items() if v <= 0]:
        debt.pop(item)


def _cc_add_sell(market, item, qty, max_orders):
    for order in market:
        if order and order[0] == "SELL" and len(order) >= 3 and order[1] == item:
            order[2] = int(order[2]) + qty
            return True
    for i, order in enumerate(market):
        if not order:
            market[i] = ["SELL", item, qty]
            return True
    if len(market) < max_orders:
        market.append(["SELL", item, qty])
        return True
    return False


def _cc_advance(observation, action, market, step, player):
    chassis = _IMPL.chassis
    route = chassis.players.get(player, {}).get("route")
    if route not in chassis.routes:
        return
    lead = int(_CC["lead"])
    if any(step < b <= step + lead for b in _CC_BOUNDARIES):
        return
    if _CC["skip_tick"] and any(s % 4 == 0 for s in range(step + 1, step + lead + 1)):
        return
    if _CC["gate"] > 0 and _cc_similarity(observation, player) < _CC["gate"]:
        _CC_REPORT["gated_off"] += 1
        return
    view = _View(observation, player, chassis.cfg)
    stock = chassis._projected_shed(dict(action, market=market), view)
    for order in market:
        if order and order[0] == "SELL" and len(order) >= 3 and order[1] in stock:
            stock[order[1]] -= max(0, int(order[2]))
    prices = (observation.get("market") or {}).get("prices") or {}
    max_orders = chassis.cfg.get("max_orders", 10)
    moved = False
    for item in _CC["items"]:
        planned = chassis.future_sells(route, item, step + 1) - chassis.future_sells(route, item, step + 1 + lead)
        qty = min(max(0, stock.get(item, 0)), max(0, planned))
        if qty < _CC["min_qty"] or prices.get(item, 0) < _CC["min_price"]:
            continue
        if _cc_add_sell(market, item, qty, max_orders):
            _CC_STATE["debt"][item] = _CC_STATE["debt"].get(item, 0) + qty
            _CC_REPORT["units"] += qty
            moved = True
    if moved:
        _CC_REPORT["turns"] += 1


def cc_agent(observation, configuration=None):
    action = _CC_PARENT(observation, configuration)
    try:
        player = int(observation["player"])
        step = _step_of(observation)
        if step <= _CC_STATE["last"]:
            _CC_STATE["debt"] = {}
            for key in _CC_REPORT:
                _CC_REPORT[key] = 0
        _CC_STATE["last"] = step
        if step >= _CC["stop_debt"]:
            _CC_STATE["debt"] = {}
            return action
        market = _cc_market(action)
        if _CC_STATE["debt"]:
            _cc_repay(market, _CC_STATE["debt"])
        if _CC["start"] <= step < _CC["stop_new"]:
            _cc_advance(observation, action, market, step, player)
        return dict(action, market=market)
    except Exception:
        _CC_REPORT["errors"] += 1
        return action


cc_agent.telemetry = _CC_REPORT
