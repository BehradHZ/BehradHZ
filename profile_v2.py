import calendar
import html
import json
import os
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
USER = "BehradHZ"
START = date(2006, 4, 10)
PROFILE_REPO = USER

STATIC = {
    "name": "Behrad Hozouri",
    "role": "Computer Engineering Student at Amirkabir University of Technology",
    "contact": "behradhozouri@gmail.com",
    "backend": "Python · Django",
    "frontend": "TypeScript · React Native",
    "data": "PostgreSQL",
    "tools": "Git · Docker · VS Code",
}


def get(url):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "BehradHZ-profile",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token

    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.load(response)


def uptime():
    today = datetime.now(timezone.utc).date()
    years = today.year - START.year
    anniversary = date(START.year + years, START.month, START.day)

    if anniversary > today:
        years -= 1
        anniversary = date(START.year + years, START.month, START.day)

    months = 0
    while True:
        total = anniversary.year * 12 + anniversary.month - 1 + months + 1
        year, month_zero = divmod(total, 12)
        month = month_zero + 1
        probe = date(
            year,
            month,
            min(anniversary.day, calendar.monthrange(year, month)[1]),
        )
        if probe > today:
            break
        months += 1

    total = anniversary.year * 12 + anniversary.month - 1 + months
    year, month_zero = divmod(total, 12)
    month = month_zero + 1
    anchor = date(
        year,
        month,
        min(anniversary.day, calendar.monthrange(year, month)[1]),
    )

    return f"{years}y {months}m {(today - anchor).days}d"


def esc(value):
    return html.escape(str(value), quote=False)


def cut(value, limit):
    value = " ".join(str(value).split())
    return value if len(value) <= limit else value[: limit - 1].rstrip() + "…"


def public_repos():
    repos = get(
        f"https://api.github.com/users/{USER}/repos?per_page=100&sort=pushed"
    )
    return [
        repo
        for repo in repos
        if not repo.get("fork")
        and not repo.get("archived")
        and repo.get("name") != PROFILE_REPO
    ]


def current_project(repos):
    # Optional manual override: add the GitHub topic `active` to a repo.
    active = [repo for repo in repos if "active" in (repo.get("topics") or [])]
    pool = active or repos
    if not pool:
        return None
    return max(pool, key=lambda repo: repo.get("pushed_at") or "")


def latest_commit(repos):
    candidates = []

    # Checking the most recently pushed repositories is enough to identify the
    # latest authored commit without spending the whole API rate limit.
    for repo in repos[:10]:
        try:
            query = urllib.parse.urlencode({"per_page": 1, "author": USER})
            items = get(
                f"https://api.github.com/repos/{USER}/{repo['name']}/commits?{query}"
            )
        except Exception:
            continue

        if not items:
            continue

        item = items[0]
        commit = item.get("commit") or {}
        author = commit.get("author") or {}
        message = (commit.get("message") or "").splitlines()[0]

        if not message or message.startswith("chore: refresh profile"):
            continue

        candidates.append(
            {
                "date": author.get("date") or "",
                "sha": (item.get("sha") or "")[:7],
                "repo": repo["name"],
                "message": message,
            }
        )

    return max(candidates, key=lambda item: item["date"]) if candidates else None


def load():
    try:
        user = get(f"https://api.github.com/users/{USER}")
        repos = public_repos()
    except Exception:
        user, repos = {}, []

    current = current_project(repos)
    shipped = latest_commit(repos)

    return {
        "name": user.get("name") or STATIC["name"],
        "current": current["name"] if current else "—",
        "last_push": (
            f"{current['name']} · {(current.get('pushed_at') or '')[:10]}"
            if current
            else "—"
        ),
        "repos": len(repos),
        "stars": sum(repo.get("stargazers_count") or 0 for repo in repos),
        "followers": user.get("followers") or 0,
        "uptime": uptime(),
        "shipped": shipped,
    }


def portrait():
    lines = (
        (ROOT / "assets/portrait.txt")
        .read_text(encoding="utf-8")
        .rstrip("\n")
        .splitlines()
    )

    output = ['<text x="24" y="68" class="ascii">']
    for index, line in enumerate(lines):
        dy = "0" if index == 0 else "15.2"
        output.append(f'<tspan x="24" dy="{dy}">{esc(line)}</tspan>')
    output.append("</text>")
    return "".join(output)


def svg(theme, data, portrait_svg):
    dark = theme == "dark"
    colors = {
        "bg": "#0e1116" if dark else "#f6f8fa",
        "line": "#253041" if dark else "#d0d7de",
        "text": "#e6edf3" if dark else "#24292f",
        "muted": "#8b98aa" if dark else "#57606a",
        "accent": "#6ea8fe" if dark else "#0969da",
        "soft": "#b9d2ff" if dark else "#0550ae",
        "portrait": "#c9ddff" if dark else "#3b4858",
    }

    shipped = data["shipped"]
    if shipped:
        shipped_svg = (
            f'<text x="535" y="535" class="muted">{esc(shipped["sha"])}</text>'
            f'<text x="610" y="535" class="key">{esc(cut(shipped["repo"], 18))}</text>'
            f'<text x="775" y="535" class="value">{esc(cut(shipped["message"], 47))}</text>'
        )
    else:
        shipped_svg = '<text x="535" y="535" class="muted">—</text>'

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1180" height="700" viewBox="0 0 1180 700">
<style>
text {{ font-family:"Cascadia Mono","SFMono-Regular",Menlo,Consolas,monospace; white-space:pre; }}
.ascii {{ fill:{colors['portrait']}; font-size:11.4px; }}
.text {{ fill:{colors['text']}; font-size:15px; }}
.muted {{ fill:{colors['muted']}; font-size:13px; }}
.key {{ fill:{colors['accent']}; font-size:14px; }}
.value {{ fill:{colors['text']}; font-size:14px; }}
.value-small {{ fill:{colors['text']}; font-size:12.5px; }}
.accent {{ fill:{colors['soft']}; font-size:14px; }}
.cursor {{ animation:blink 1s step-end infinite; }}
@keyframes blink {{ 0%,49% {{ opacity:1; }} 50%,100% {{ opacity:0; }} }}
</style>
<rect width="1180" height="700" rx="18" fill="{colors['bg']}"/>
<rect x="1" y="1" width="1178" height="698" rx="17" fill="none" stroke="{colors['line']}"/>
<text x="28" y="32" class="muted">~/profile</text>
<text x="1085" y="32" class="muted">tty0</text>
<line x1="28" y1="46" x2="1152" y2="46" stroke="{colors['line']}"/>

{portrait_svg}
<text x="30" y="505" class="muted">rendered with symbol-art · text mode</text>
<text x="30" y="540" class="key">uptime</text>
<text x="145" y="540" class="value">{esc(data['uptime'])}</text>
<text x="30" y="568" class="key">contact</text>
<text x="145" y="568" class="value">{STATIC['contact']}</text>

<text x="535" y="86" class="text">behrad@github</text>
<text x="535" y="108" class="muted">────────────────────────────────────────────────</text>

<text x="535" y="143" class="accent">identity</text>
<text x="535" y="171" class="key">name</text>
<text x="660" y="171" class="value">{esc(data['name'])}</text>
<text x="535" y="198" class="key">role</text>
<text x="660" y="198" class="value-small">{STATIC['role']}</text>

<text x="535" y="242" class="accent">current</text>
<text x="535" y="270" class="key">project</text>
<text x="660" y="270" class="value">{esc(data['current'])}</text>
<text x="535" y="297" class="key">last push</text>
<text x="660" y="297" class="value">{esc(data['last_push'])}</text>

<text x="535" y="341" class="accent">github</text>
<text x="535" y="369" class="key">repos</text>
<text x="660" y="369" class="value">{data['repos']}</text>
<text x="535" y="396" class="key">stars</text>
<text x="660" y="396" class="value">{data['stars']}</text>
<text x="535" y="423" class="key">followers</text>
<text x="660" y="423" class="value">{data['followers']}</text>

<text x="535" y="467" class="accent">stack</text>
<text x="535" y="495" class="key">stack.backend</text><text x="690" y="495" class="value">{STATIC['backend']}</text>
<text x="535" y="520" class="key">stack.frontend</text><text x="690" y="520" class="value">{STATIC['frontend']}</text>
<text x="535" y="545" class="key">stack.data</text><text x="690" y="545" class="value">{STATIC['data']}</text>
<text x="535" y="570" class="key">stack.tools</text><text x="690" y="570" class="value">{STATIC['tools']}</text>

<text x="535" y="614" class="accent">recently shipped</text>
{shipped_svg}

<line x1="535" y1="648" x2="1150" y2="648" stroke="{colors['line']}"/>
<text x="535" y="680" class="accent">behrad@github:~$</text>
<text x="700" y="680" class="text cursor">█</text>
</svg>'''


def main():
    data = load()
    portrait_svg = portrait()
    for theme in ("dark", "light"):
        (ROOT / f"{theme}.svg").write_text(
            svg(theme, data, portrait_svg),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
