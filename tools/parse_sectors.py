import re, os, json, base64, csv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEC_DIR = os.path.join(ROOT, "sectors")
OUT_DIR = os.path.join(ROOT, "data")

def dec(code):
    return int(base64.b64decode(code + "=" * (-len(code) % 4)).decode())

def txt(s):
    s = re.sub(r"<[^>]+>", "", s)
    return s.replace("&nbsp;", " ").strip()

universe = {}
for fn in sorted(os.listdir(SEC_DIR)):
    if not fn.endswith(".html"):
        continue
    code = fn[:-5]
    h = open(os.path.join(SEC_DIR, fn), encoding="cp1251", errors="replace").read()
    rec = {"code": code, "id": dec(code)}

    m = re.search(r'<b>Сектор "([^"]+)"</b>', h)
    rec["name"] = m.group(1) if m else None

    def field(label):
        mm = re.search(r'>' + label + r':</td>\s*<td[^>]*>(.*?)</td>', h, re.S)
        return txt(mm.group(1)) if mm else None

    rec["race"] = field("Раса")
    rec["status"] = field("Статус")
    rec["planets"] = int(field("Планет") or 0)
    rec["n_stations"] = int(field("Станций") or 0)
    rec["n_asteroids"] = int(field("Астероидов") or 0)

    gates = {}
    for g, key in [("Северные врата", "N"), ("Южные врата", "S"),
                   ("Восточные врата", "E"), ("Западные врата", "W")]:
        mm = re.search(r'>' + g + r':</td>\s*<td[^>]*>(.*?)</td>', h, re.S)
        cell = mm.group(1) if mm else ""
        lm = re.search(r'sector\.php\?c=([^"]+)', cell)
        gates[key] = dec(lm.group(1)) if lm else None
    rec["gates"] = gates

    mm = re.search(r'Координаты сектора на карте \(X, Y\):</td>\s*<td[^>]*>(.*?)</td>', h, re.S)
    if mm:
        xy = txt(mm.group(1))
        parts = [p.strip() for p in xy.split(",")]
        rec["x"], rec["y"] = int(parts[0]), int(parts[1])
    else:
        rec["x"] = rec["y"] = None

    # stations
    stations = []
    sm = re.search(r'<b>Станции:</b>(.*?)</table>', h, re.S)
    if sm:
        for row in re.findall(r'<tr[^>]*>(.*?)</tr>', sm.group(1), re.S)[1:]:
            # rows are malformed: <td ...>name<td ...>race</td><td ...>[подробнее]</td>
            nm_m = re.search(r'<td align=left class=y>(.*?)(?:<td\b|$)', row, re.S)
            rc_m = re.search(r'<td class=h>(.*?)(?:</td>|$)', row, re.S)
            fm = re.search(r'factory\.php\?c=([^"]+)', row)
            nm = txt(nm_m.group(1)) if nm_m else ""
            if not nm:
                continue
            race = txt(rc_m.group(1)) if rc_m else ""
            stations.append({"name": nm, "race": race, "code": fm.group(1) if fm else None})
    rec["stations"] = stations

    # asteroids
    asteroids = []
    am = re.search(r'<b>Астероиды:</b>(.*?)</table>', h, re.S)
    if am:
        for row in re.findall(r'<tr[^>]*>(.*?)</tr>', am.group(1), re.S)[1:]:
            cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
            if len(cells) < 5:
                continue
            try:
                asteroids.append({
                    "res": txt(cells[0]),
                    "content": int(txt(cells[1])),
                    "x": float(txt(cells[2]).replace(",", ".")),
                    "y": float(txt(cells[3]).replace(",", ".")),
                    "z": float(txt(cells[4]).replace(",", ".")),
                })
            except ValueError:
                pass
    rec["asteroids"] = asteroids
    universe[rec["id"]] = rec

json.dump(universe, open(os.path.join(OUT_DIR, "universe.json"), "w", encoding="utf-8", newline="\n"),
          ensure_ascii=False, indent=1)
print("sectors parsed:", len(universe))
print("with gates:", sum(1 for r in universe.values() if any(r["gates"].values())))
print("with stations:", sum(1 for r in universe.values() if r["stations"]))
print("with asteroids:", sum(1 for r in universe.values() if r["asteroids"]))
tot_st = sum(len(r["stations"]) for r in universe.values())
tot_as = sum(len(r["asteroids"]) for r in universe.values())
print("total stations:", tot_st, "total asteroids:", tot_as)
