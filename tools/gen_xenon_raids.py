"""Генератор слоя ксенонских рейдов для ветки military.

Читает data/universe.json и строит data/xenon_raids.json:
  - xenon_sectors: все сектора расы «Ксенон» (источники рейдов);
  - raids: одна запись на каждый выход из ксенонского сектора в сектор другой
    расы (то есть куда ксенонцы реально могут напасть за 1 прыжок через врата);
  - frontier: сектора в 1-2 прыжках от ксенонских (зона проникновения), с
    расстоянием BFS.

Ничего не рисует сам: результат подхватывает tools/gen_map.py и встраивает
его в index.html как XENON_RAIDS.
"""
import json, os, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data")

u = json.load(open(os.path.join(D, "universe.json"), encoding="utf-8"))
u = {int(k): v for k, v in u.items()}


def race(sid):
    return u.get(sid, {}).get("race", "")


xenon = sorted(sid for sid, r in u.items() if r.get("race") == "Ксенон")

# --- рейды: ксенонский сектор -> сосед другой расы (1 прыжок) ---
raids = []
for sid in xenon:
    for direction in ("N", "S", "E", "W"):
        t = u[sid]["gates"].get(direction)
        if not t or t not in u:
            continue
        if race(t) == "Ксенон":
            continue
        raids.append({
            "from": sid,
            "to": t,
            "direction": direction,
            "from_name": u[sid]["name"],
            "to_name": u[t]["name"],
            "to_race": race(t),
        })

# --- фронт вторжения: BFS от ксенонских секторов (граф неориентированный) ---
dist = {sid: 0 for sid in xenon}
q = collections.deque(xenon)
while q:
    cur = q.popleft()
    for d, t in u[cur]["gates"].items():
        if t and t in u and t not in dist:
            dist[t] = dist[cur] + 1
            q.append(t)

frontier = [
    {"id": sid, "dist": d, "name": u[sid]["name"], "race": race(sid)}
    for sid, d in sorted(dist.items()) if 0 < d <= 2
]

out = {
    "generated_from": "data/universe.json",
    "xenon_sectors": [
        {"id": sid, "name": u[sid]["name"], "x": u[sid]["x"], "y": u[sid]["y"]}
        for sid in xenon
    ],
    "raids": raids,
    "frontier": frontier,
}

path = os.path.join(D, "xenon_raids.json")
with open(path, "w", encoding="utf-8", newline="\n") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
    f.write("\n")

print("written:", path)
print("xenon sectors:", len(xenon), "| raids:", len(raids), "| frontier(1-2 hops):", len(frontier))
