import calendar, html, json, os, re, urllib.parse, urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

ROOT=Path(__file__).parent
USER="BehradHZ"
START=date(2006,4,10)
STATIC={
"role":"Computer Engineering Student","university":"Amirkabir University of Technology",
"location":"Tehran","languages":"Persian · English","backend":"Python · Django",
"frontend":"TypeScript · React Native","data":"PostgreSQL","tools":"Git · Docker · VS Code"}

def get(url):
    h={"Accept":"application/vnd.github+json","User-Agent":"BehradHZ-profile"}
    token=os.getenv("GITHUB_TOKEN")
    if token: h["Authorization"]="Bearer "+token
    with urllib.request.urlopen(urllib.request.Request(url,headers=h),timeout=25) as r:
        return json.load(r)

def text(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"BehradHZ-profile"}),timeout=25) as r:
        return r.read().decode("utf-8","replace")

def age():
    today=datetime.now(timezone.utc).date(); years=today.year-START.year
    a=date(START.year+years,START.month,START.day)
    if a>today: years-=1; a=date(START.year+years,START.month,START.day)
    months=0
    while True:
        total=a.year*12+a.month-1+months+1; y,m0=divmod(total,12); m=m0+1
        probe=date(y,m,min(a.day,calendar.monthrange(y,m)[1]))
        if probe>today: break
        months+=1
    total=a.year*12+a.month-1+months; y,m0=divmod(total,12); m=m0+1
    anchor=date(y,m,min(a.day,calendar.monthrange(y,m)[1]))
    return f"{years}y {months}m {(today-anchor).days}d"

def contributions():
    try:
        page=text(f"https://github.com/users/{USER}/contributions")
        m=re.search(r"([0-9,]+)\s+contributions?\s+in\s+the\s+last\s+year",page,re.I)
        return int(m.group(1).replace(",","")) if m else None
    except Exception: return None

def pick(repos,topic,exclude=None):
    tagged=[r for r in repos if topic in (r.get("topics") or []) and r["name"]!=exclude]
    if tagged: return tagged[0]
    return next((r for r in repos if r["name"]!=exclude),None)

def recent(repos):
    found=[]
    for repo in repos[:8]:
        try:
            q=urllib.parse.urlencode({"per_page":3,"author":USER})
            items=get(f"https://api.github.com/repos/{USER}/{repo['name']}/commits?{q}")
        except Exception: continue
        for item in items:
            c=item.get("commit") or {}; a=c.get("author") or {}; msg=(c.get("message") or "").splitlines()[0]
            if msg and not msg.startswith("chore: refresh profile"):
                found.append((a.get("date") or "",(item.get("sha") or "")[:7],repo["name"],msg))
    return sorted(found,reverse=True)[:4]

def esc(v): return html.escape(str(v),quote=False)
def cut(v,n):
    v=" ".join(str(v).split()); return v if len(v)<=n else v[:n-1].rstrip()+"…"

def load():
    try:
        user=get(f"https://api.github.com/users/{USER}")
        repos=[r for r in get(f"https://api.github.com/users/{USER}/repos?per_page=100&sort=pushed") if not r.get("fork") and not r.get("archived") and r["name"]!=USER]
    except Exception: user,repos={},[]
    current=pick(repos,"active"); nxt=pick(repos,"next",current["name"] if current else None)
    return {"name":user.get("name") or "Behrad Hozouri","location":user.get("location") or STATIC["location"],
    "current":current["name"] if current else "—","next":nxt["name"] if nxt else "—",
    "last":f"{current['name']} · {(current.get('pushed_at') or '')[:10]}" if current else "—",
    "repos":len(repos),"stars":sum(r.get("stargazers_count") or 0 for r in repos),"followers":user.get("followers") or 0,
    "contrib":contributions(),"commits":recent(repos),"uptime":age()}

def portrait():
    lines=(ROOT/"assets/portrait.txt").read_text(encoding="utf-8").rstrip("\n").splitlines(); out=['<text x="24" y="68" class="ascii">']
    for i,line in enumerate(lines): out.append(f'<tspan x="24" dy="{"0" if i==0 else "15.2"}">{esc(line)}</tspan>')
    return "".join(out)+"</text>"

def svg(theme,d,p):
    dark=theme=="dark"; c={"bg":"#0e1116" if dark else "#f6f8fa","line":"#253041" if dark else "#d0d7de","text":"#e6edf3" if dark else "#24292f","muted":"#8b98aa" if dark else "#57606a","accent":"#6ea8fe" if dark else "#0969da","soft":"#b9d2ff" if dark else "#0550ae","portrait":"#c9ddff" if dark else "#3b4858"}
    contrib=f"{d['contrib']:,}" if isinstance(d['contrib'],int) else "—"
    rows=[]; y=512
    commits=list(d["commits"])
    while len(commits)<4: commits.append(("","───────","—","—"))
    for _,sha,repo,msg in commits[:4]:
        rows.append(f'<text x="535" y="{y}" class="muted">{esc(sha)}</text><text x="610" y="{y}" class="key">{esc(cut(repo,16))}</text><text x="765" y="{y}" class="value">{esc(cut(msg,44))}</text>'); y+=25
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1180" height="760" viewBox="0 0 1180 760"><style>text{{font-family:"Cascadia Mono","SFMono-Regular",Menlo,Consolas,monospace;white-space:pre}}.ascii{{fill:{c['portrait']};font-size:11.4px}}.text{{fill:{c['text']};font-size:15px}}.muted{{fill:{c['muted']};font-size:13px}}.key{{fill:{c['accent']};font-size:14px}}.value{{fill:{c['text']};font-size:14px}}.accent{{fill:{c['soft']};font-size:14px}}.cursor{{animation:blink 1s step-end infinite}}@keyframes blink{{0%,49%{{opacity:1}}50%,100%{{opacity:0}}}}</style><rect width="1180" height="760" rx="18" fill="{c['bg']}"/><rect x="1" y="1" width="1178" height="758" rx="17" fill="none" stroke="{c['line']}"/><text x="28" y="32" class="muted">~/profile</text><text x="1085" y="32" class="muted">tty0</text><line x1="28" y1="46" x2="1152" y2="46" stroke="{c['line']}"/>{p}<text x="30" y="505" class="muted">rendered with symbol-art · text mode</text><text x="28" y="542" class="accent">identity</text><text x="28" y="570" class="key">name</text><text x="155" y="570" class="value">{esc(d['name'])}</text><text x="28" y="595" class="key">role</text><text x="155" y="595" class="value">{STATIC['role']}</text><text x="28" y="620" class="key">university</text><text x="155" y="620" class="value">{STATIC['university']}</text><text x="28" y="645" class="key">location</text><text x="155" y="645" class="value">{esc(d['location'])}</text><text x="28" y="670" class="key">languages</text><text x="155" y="670" class="value">{STATIC['languages']}</text><text x="28" y="695" class="key">contact</text><text x="155" y="695" class="value">@{USER} · github.com/{USER}</text><text x="28" y="720" class="key">uptime</text><text x="155" y="720" class="value">{d['uptime']}</text><text x="535" y="86" class="text">behrad@github</text><text x="535" y="108" class="muted">────────────────────────────────────────────────</text><text x="535" y="141" class="accent">session</text><text x="535" y="169" class="key">current</text><text x="660" y="169" class="value">{esc(d['current'])}</text><text x="535" y="194" class="key">next</text><text x="660" y="194" class="value">{esc(d['next'])}</text><text x="535" y="219" class="key">last push</text><text x="660" y="219" class="value">{esc(d['last'])}</text><text x="535" y="262" class="accent">github</text><text x="535" y="290" class="value">repos {d['repos']}  ·  stars {d['stars']}  ·  contrib {contrib}  ·  followers {d['followers']}</text><text x="535" y="337" class="accent">stack</text><text x="535" y="365" class="key">backend</text><text x="660" y="365" class="value">{STATIC['backend']}</text><text x="535" y="390" class="key">frontend</text><text x="660" y="390" class="value">{STATIC['frontend']}</text><text x="535" y="415" class="key">data</text><text x="660" y="415" class="value">{STATIC['data']}</text><text x="535" y="440" class="key">tools</text><text x="660" y="440" class="value">{STATIC['tools']}</text><text x="535" y="484" class="accent">recently shipped</text>{''.join(rows)}<line x1="535" y1="696" x2="1150" y2="696" stroke="{c['line']}"/><text x="535" y="730" class="accent">behrad@github:~$</text><text x="700" y="730" class="text cursor">█</text></svg>'''

def main():
    d=load(); p=portrait()
    for theme in ("dark","light"): (ROOT/f"{theme}.svg").write_text(svg(theme,d,p),encoding="utf-8")
if __name__=="__main__": main()
