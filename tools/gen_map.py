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
# Цвета рас — по описанию внешности (Documents/Расы.txt):
# люди (Земляне/Аргон/Гонер) — телесные оттенки; Сплит — желтовато-коричневый;
# Паранид — бронзово-золотистый; Телади — зелёный/болотный; Борон — бирюзовый;
# Ксенон — красный: их сектора крайне опасны; Хаак — кристаллический фиолетовый.
RACE_COLORS = {
    "Земляне": "#ac8350", "Аргон": "#a06f42", "Гонер": "#7d7468",
    "Сплит": "#94874f", "Паранид": "#a3762f", "Телади": "#4f7d3d",
    "Борон": "#3a9a8f", "Ксенон": "#c62828", "Хаак": "#7a4a8c",
    "Яки": "#4f4f4f", "Пират": "#333333", "": "#ffffff",
}

data_js = json.dumps({str(k): v for k, v in u.items()}, ensure_ascii=False)
colors_js = json.dumps(RACE_COLORS, ensure_ascii=False)

# ---------- raid routes (military layer) ----------
routes = []
_rf = os.path.join(D, "routes.json")
if os.path.exists(_rf):
    routes = json.load(open(_rf, encoding="utf-8")).get("routes", [])
routes_js = json.dumps(routes, ensure_ascii=False)

html_doc = """<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8">
<title>X3:TC — карта вселенной (offline)</title>
<style>
body{background:#0C101D;color:#dfe6f0;font-family:Tahoma,Arial,sans-serif;font-size:13px;margin:0;padding:10px}
h1{font-size:16px;margin:0 0 6px}
.sub{color:#8fa3c0;font-size:11px;margin-bottom:10px}
.wrap{max-width:100%}
#scroller{overflow-x:auto;max-width:100%;transform:scaleY(-1)}
#flip{transform:scaleY(-1)}
#routes{position:absolute;left:0;top:0;pointer-events:none;z-index:5}
#routeList label{display:inline-block;margin:0 12px 2px 0;cursor:pointer;font-size:11px;color:#dfe6f0}
#routeList input{vertical-align:middle}
#grid{border-collapse:collapse;table-layout:fixed;width:1920px}
#grid td{width:80px;height:80px;border:1px solid #1c2a44;vertical-align:top;padding:2px;overflow:hidden;cursor:pointer}
#grid td.empty{background:#0C101D;cursor:default}
#grid .nm{font-size:10px;line-height:1.15;display:block;color:#fff;text-decoration:none;text-shadow:0 1px 2px rgba(0,0,0,.85)}
#grid .inf{font-size:9px;color:#d5deea;margin-top:1px;text-shadow:0 1px 2px rgba(0,0,0,.85)}
#grid td.lt .nm{color:#111;text-shadow:none}
#grid td.lt .inf{color:#222;text-shadow:none}
#detail{position:fixed;display:none;z-index:1000;width:430px;max-width:calc(100vw - 20px);background:#151F2D;border:1px solid #3a4f70;border-radius:8px;box-shadow:0 12px 36px rgba(0,0,0,.65),0 2px 8px rgba(0,0,0,.5);padding:8px;max-height:calc(100vh - 20px);overflow:auto}
#detail .x{float:right;cursor:pointer;color:#8fa3c0;font-size:16px;line-height:1;padding:0 4px;border:1px solid #33476a;border-radius:4px}
#detail .x:hover{color:#fff;background:#24344d}
#detail h2{font-size:14px;margin:0 0 4px;color:#fff}
#detail table{border-collapse:collapse;width:100%;font-size:11px;margin-top:6px}
#detail td,#detail th{border:1px solid #2a3a55;padding:2px 4px;text-align:left;vertical-align:top}
#detail th{background:#1d2a40;color:#9fb4d4}
.tag{display:inline-block;padding:1px 6px;border-radius:3px;font-size:10px;color:#fff;text-shadow:0 1px 2px rgba(0,0,0,.85)}
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
<div id="routeList"></div>
<div class="wrap">
<div id="scroller"><div id="flip"><table id="grid"></table><svg id="routes"></svg></div></div>
</div>
<div id="detail"></div>
<script>
const U = __DATA__;
const COL = __COLORS__;
const ROUTES = __ROUTES__;
const W=24, H=20;
const grid=document.getElementById('grid');
const det=document.getElementById('detail');
const nameById={};
for(const id in U){ nameById[id]=U[id].name; }
function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function isLight(hex){
  const m=/^#?([0-9a-f]{6})$/i.exec(hex||''); if(!m) return false;
  const v=parseInt(m[1],16); const r=(v>>16)&255, g=(v>>8)&255, b=v&255;
  return (0.2126*r+0.7152*g+0.0722*b)/255 > 0.6;
}
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
      html+='<td style="background:'+c+'"'+(isLight(c)?' class="lt"':'')+' data-id="'+found+'">'
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
  const tc=isLight(c)?'#111':'#fff';
  const tsh=isLight(c)?'none':'0 1px 2px rgba(0,0,0,.85)';
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
  det.innerHTML='<span class="x" onclick="closeDet()" title="Закрыть">&times;</span>'
    + '<h2><span class="tag" style="background:'+c+';color:'+tc+';text-shadow:'+tsh+'">'+esc(r.race||'?')+'</span> '+esc(r.name)+'</h2>'
    + '<div style="color:#8fa3c0;font-size:11px">ID '+id+' · координаты ('+r.x+', '+r.y+') · статус: '+esc(r.status||'?')+' · планет: '+r.planets+'</div>'
    + '<div style="margin-top:6px">'+gates+'</div>'+st+as;
  det.style.display='block';
  window._curId=id;
  place(id);
}
// Позиционирование всплывающего окна с учетом границ экрана
function place(id){
  const td=grid.querySelector('td[data-id="'+id+'"]');
  if(!td) return;
  const r=td.getBoundingClientRect();
  const pw=det.offsetWidth, ph=det.offsetHeight;
  const m=10;
  let left=r.right+m;
  if(left+pw>window.innerWidth-m) left=r.left-pw-m;
  left=Math.max(m, Math.min(window.innerWidth-pw-m, left));
  let top=r.top;
  if(top+ph>window.innerHeight-m) top=window.innerHeight-ph-m;
  top=Math.max(m, Math.min(window.innerHeight-ph-m, top));
  det.style.left=left+'px';
  det.style.top=top+'px';
}
function closeDet(){ det.style.display='none'; window._curId=null; }
document.addEventListener('click',function(e){
  if(window._curId==null) return;
  if(det.contains(e.target)) return;
  if(e.target.closest && e.target.closest('td[data-id]')) return;
  closeDet();
});
document.addEventListener('keydown',function(e){ if(e.key==='Escape') closeDet(); });
window.addEventListener('resize',function(){ if(window._curId!=null) place(window._curId); });
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
// --- raid routes layer (military) ---
const routesSvg=document.getElementById('routes');
function drawRoutes(){
  if(!routesSvg) return;
  const tr=grid.getBoundingClientRect(), sr=routesSvg.getBoundingClientRect();
  const cw=grid.offsetWidth/W, ch=grid.offsetHeight/H;
  routesSvg.setAttribute('width',grid.offsetWidth);
  routesSvg.setAttribute('height',grid.offsetHeight);
  let defs='', body='';
  ROUTES.forEach((rt,i)=>{
    if(!rt.on) return;
    defs+='<marker id="ah'+i+'" markerWidth="9" markerHeight="9" refX="7" refY="3.2" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L7,3.2 L0,6.4 z" fill="'+rt.color+'"/></marker>';
    let prev=null;
    for(const id of rt.sectors){
      const r=U[id]; if(!r) continue;
      const cx=tr.left-sr.left+(r.x+0.5)*cw, cy=tr.top-sr.top+(r.y+0.5)*ch;
      if(prev){
        const dx=cx-prev[0], dy=cy-prev[1], len=Math.hypot(dx,dy)||1;
        const sx=prev[0]+dx/len*24, sy=prev[1]+dy/len*24;
        const ex=cx-dx/len*30, ey=cy-dy/len*30;
        body+='<line x1="'+sx+'" y1="'+sy+'" x2="'+ex+'" y2="'+ey+'" stroke="rgba(0,0,0,.55)" stroke-width="6" stroke-linecap="round"/>';
        body+='<line x1="'+sx+'" y1="'+sy+'" x2="'+ex+'" y2="'+ey+'" stroke="'+rt.color+'" stroke-width="3" stroke-linecap="round" marker-end="url(#ah'+i+')"/>';
      }
      prev=[cx,cy];
    }
  });
  routesSvg.innerHTML='<defs>'+defs+'</defs>'+body;
}
let rhtml='';
ROUTES.forEach((rt,i)=>{ rt.on=true; rhtml+='<label><input type="checkbox" data-i="'+i+'" checked> <span style="color:'+rt.color+'">&#9632;</span> '+esc(rt.name)+'</label>'; });
document.getElementById('routeList').innerHTML=rhtml;
document.querySelectorAll('#routeList input').forEach(cb=>{
  cb.onchange=()=>{ ROUTES[+cb.dataset.i].on=cb.checked; drawRoutes(); };
});
drawRoutes();
</script></body></html>
"""

nsec = len(u)
nst = sum(len(r["stations"]) for r in u.values())
nast = sum(len(r["asteroids"]) for r in u.values())
ngate = sum(1 for r in u.values() for g in r["gates"].values() if g)

html_doc = (html_doc
            .replace("__DATA__", data_js)
            .replace("__COLORS__", colors_js)
            .replace("__ROUTES__", routes_js)
            .replace("__NSEC__", str(nsec))
            .replace("__NST__", str(nst))
            .replace("__NAST__", str(nast))
            .replace("__NGATE__", str(ngate)))

with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8", newline="\n") as _f:
    _f.write(html_doc)
print("written:", os.path.join(ROOT, "index.html"), len(html_doc), "bytes")
