import json, csv, os, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data")
u = json.load(open(os.path.join(D, "universe.json"), encoding="utf-8"))
u = {int(k): v for k, v in u.items()}

# ---------- CSV exports ----------
with open(os.path.join(D, "sectors.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "code", "name", "x", "y", "race", "status", "planets",
                "n_stations", "n_asteroids", "gate_N", "gate_S", "gate_E", "gate_W"])
    for sid, r in sorted(u.items()):
        g = r["gates"]
        w.writerow([sid, r["code"], r["name"], r["x"], r["y"], r["race"], r["status"],
                    r["planets"], r["n_stations"], r["n_asteroids"],
                    g.get("N"), g.get("S"), g.get("E"), g.get("W")])

with open(os.path.join(D, "stations.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["sector_id", "sector_name", "sector_x", "sector_y", "station_name", "race", "code"])
    for sid, r in sorted(u.items()):
        for s in r["stations"]:
            w.writerow([sid, r["name"], r["x"], r["y"], s["name"], s["race"], s["code"]])

with open(os.path.join(D, "asteroids.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["sector_id", "sector_name", "resource", "content", "x", "y", "z"])
    for sid, r in sorted(u.items()):
        for a in r["asteroids"]:
            w.writerow([sid, r["name"], a["res"], a["content"], a["x"], a["y"], a["z"]])

with open(os.path.join(D, "gates.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["from_id", "from_name", "direction", "to_id", "to_name"])
    for sid, r in sorted(u.items()):
        for d, t in r["gates"].items():
            if t:
                w.writerow([sid, r["name"], d, t, u.get(t, {}).get("name", "?")])

# ---------- offline HTML map ----------
RACE_COLORS = {
    "Земляне": "#2f5d8a", "Аргон": "#2f7a3f", "Борон": "#2f7a7a",
    "Сплит": "#a55a3f", "Паранид": "#7a4a9a", "Телади": "#8a8a2f",
    "Пират": "#5a5a5a", "Ксенон": "#a03030", "Хаак": "#5a2a5a",
    "Яки": "#6a4a8a", "Гонер": "#6a6a6a", "": "#333333",
}

data_js = json.dumps({str(k): v for k, v in u.items()}, ensure_ascii=False)
colors_js = json.dumps(RACE_COLORS, ensure_ascii=False)

html_doc = """<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8">
<title>X3:TC — карта вселенной (offline)</title>
<style>
body{background:#0C101D;color:#dfe6f0;font-family:Tahoma,Arial,sans-serif;font-size:13px;margin:0;padding:10px}
h1{font-size:16px;margin:0 0 6px}
.sub{color:#8fa3c0;font-size:11px;margin-bottom:10px}
.wrap{display:flex;gap:14px;align-items:flex-start}
#grid{border-collapse:collapse;table-layout:fixed}
#grid td{width:86px;height:60px;border:1px solid #1c2a44;vertical-align:top;padding:2px;overflow:hidden;cursor:pointer}
#grid td.empty{background:#0C101D;cursor:default}
#grid .nm{font-size:10px;line-height:1.15;display:block;color:#fff;text-decoration:none}
#grid .inf{font-size:9px;color:#b8c6dd;margin-top:1px}
#detail{width:430px;flex:0 0 430px;background:#151F2D;border:1px solid #2a3a55;padding:8px;min-height:200px}
#detail h2{font-size:14px;margin:0 0 4px;color:#fff}
#detail table{border-collapse:collapse;width:100%;font-size:11px;margin-top:6px}
#detail td,#detail th{border:1px solid #2a3a55;padding:2px 4px;text-align:left;vertical-align:top}
#detail th{background:#1d2a40;color:#9fb4d4}
.tag{display:inline-block;padding:1px 6px;border-radius:3px;font-size:10px;color:#fff}
.gate{display:inline-block;margin:1px 3px 1px 0;padding:1px 5px;background:#1d2a40;border:1px solid #33476a;font-size:10px}
.gate a{color:#7BA0D9;text-decoration:none}
.legend span{display:inline-block;margin-right:10px;font-size:11px}
.sw{display:inline-block;width:10px;height:10px;margin-right:3px;vertical-align:middle}
#search{width:250px;background:#0C101D;color:#dfe6f0;border:1px solid #33476a;padding:3px 6px;font-size:12px}
details{margin-top:6px}
summary{cursor:pointer;color:#9fb4d4;font-size:11px}
.hl{outline:2px solid #FFCC55}
</style></head><body>
<h1>X3:TC — карта вселенной (offline копия)</h1>
<div class="sub">Источник: <a style="color:#7BA0D9" href="https://x3tc.net/x3_tc_map/">x3tc.net/x3_tc_map</a>
· секторов: __NSEC__ · станций: __NST__ · астероидов: __NAST__ · врата: __NGATE__</div>
<div class="legend" id="legend"></div>
<div style="margin:8px 0">
 <input id="search" placeholder="поиск сектора...">
 <span id="count" style="color:#8fa3c0;font-size:11px;margin-left:8px"></span>
</div>
<div class="wrap">
<div><table id="grid"></table></div>
<div id="detail"><h2>Сектор не выбран</h2><div style="color:#8fa3c0;font-size:11px">Кликните по ячейке на карте или найдите сектор в поиске.</div></div>
</div>
<script>
const U = __DATA__;
const COL = __COLORS__;
const W=24, H=20;
const grid=document.getElementById('grid');
const det=document.getElementById('detail');
const nameById={};
for(const id in U){ nameById[id]=U[id].name; }
function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function draw(filter){
  let html='';
  for(let y=0;y<H;y++){
    html+='<tr>';
    for(let x=0;x<W;x++){
      let found=null;
      for(const id in U){ if(U[id].x===x && U[id].y===y){ found=id; break; } }
      if(!found){ html+='<td class="empty"></td>'; continue; }
      const r=U[found];
      if(filter && r.name.toLowerCase().indexOf(filter)<0){ html+='<td class="empty"></td>'; continue; }
      const c=COL[r.race]||'#333';
      let inf=[];
      if(r.n_stations) inf.push('ст:'+r.n_stations);
      if(r.n_asteroids) inf.push('аст:'+r.n_asteroids);
      html+='<td style="background:'+c+'" data-id="'+found+'">'
          + '<span class="nm">'+esc(r.name)+'</span>'
          + '<div class="inf">'+inf.join(' ')+'</div></td>';
    }
    html+='</tr>';
  }
  grid.innerHTML=html;
  grid.querySelectorAll('td[data-id]').forEach(td=>{
    td.onclick=()=>show(td.getAttribute('data-id'));
  });
}
function show(id){
  const r=U[id]; if(!r) return;
  grid.querySelectorAll('td.hl').forEach(t=>t.classList.remove('hl'));
  const td=grid.querySelector('td[data-id="'+id+'"]'); if(td) td.classList.add('hl');
  const c=COL[r.race]||'#333';
  let gates='';
  for(const d of ['N','S','E','W']){
    const t=r.gates[d];
    if(t) gates+='<span class="gate">'+d+': <a href="#" onclick="show(\\''+t+'\\');return false">'+esc(nameById[t]||'?')+'</a></span>';
    else gates+='<span class="gate" style="opacity:.45">'+d+': —</span>';
  }
  let st='<details><summary>Станции ('+r.stations.length+')</summary><table><tr><th>Станция</th><th>Раса</th></tr>';
  for(const s of r.stations){ st+='<tr><td>'+esc(s.name)+'</td><td>'+esc(s.race)+'</td></tr>'; }
  st+='</table></details>';
  let as='<details><summary>Астероиды ('+r.asteroids.length+')</summary><table><tr><th>Ресурс</th><th>Содерж.</th><th>X</th><th>Y</th><th>Z</th></tr>';
  for(const a of r.asteroids){ as+='<tr><td>'+esc(a.res)+'</td><td>'+a.content+'</td><td>'+a.x+'</td><td>'+a.y+'</td><td>'+a.z+'</td></tr>'; }
  as+='</table></details>';
  det.innerHTML='<h2><span class="tag" style="background:'+c+'">'+esc(r.race||'?')+'</span> '+esc(r.name)+'</h2>'
    + '<div style="color:#8fa3c0;font-size:11px">ID '+id+' · координаты ('+r.x+', '+r.y+') · статус: '+esc(r.status||'?')+' · планет: '+r.planets+'</div>'
    + '<div style="margin-top:6px">'+gates+'</div>'+st+as;
}
// legend
let lg='';
for(const race in COL){ if(!race) continue; lg+='<span><span class="sw" style="background:'+COL[race]+'"></span>'+esc(race)+'</span>'; }
document.getElementById('legend').innerHTML=lg;
const inp=document.getElementById('search'), cnt=document.getElementById('count');
inp.oninput=()=>{
  const f=inp.value.trim().toLowerCase();
  if(!f){ draw(null); cnt.textContent=''; return; }
  let n=0; for(const id in U){ if(U[id].name.toLowerCase().indexOf(f)>=0) n++; }
  cnt.textContent='найдено: '+n;
  draw(f);
};
draw(null);
</script></body></html>
"""

nsec = len(u)
nst = sum(len(r["stations"]) for r in u.values())
nast = sum(len(r["asteroids"]) for r in u.values())
ngate = sum(1 for r in u.values() for g in r["gates"].values() if g)

html_doc = (html_doc
            .replace("__DATA__", data_js)
            .replace("__COLORS__", colors_js)
            .replace("__NSEC__", str(nsec))
            .replace("__NST__", str(nst))
            .replace("__NAST__", str(nast))
            .replace("__NGATE__", str(ngate)))

with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8", newline="\n") as _f:
    _f.write(html_doc)
print("written:", os.path.join(ROOT, "index.html"), len(html_doc), "bytes")
