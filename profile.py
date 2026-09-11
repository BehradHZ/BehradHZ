from __future__ import annotations

import html
import json
import os
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
USER = "BehradHZ"


def github_json(url: str):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "BehradHZ-profile",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def summary() -> tuple[str, str]:
    try:
        user = github_json(f"https://api.github.com/users/{USER}")
        repos = github_json(
            f"https://api.github.com/users/{USER}/repos?per_page=100&sort=pushed"
        )
        visible = [
            repo
            for repo in repos
            if not repo.get("fork") and repo.get("name") != USER
        ]

        github = (
            f"{user.get('public_repos', len(visible))} public repos · "
            f"{user.get('followers', 0)} followers"
        )

        latest = visible[0] if visible else None
        activity = (
            f"{latest['name']} · {latest.get('pushed_at', '')[:10]}"
            if latest
            else "—"
        )
        return github, activity
    except Exception:
        return "public profile", "—"


def replace_text(svg: str, element_id: str, value: str) -> str:
    pattern = rf'(<text[^>]*id="{re.escape(element_id)}"[^>]*>).*?(</text>)'
    safe_value = html.escape(value)
    return re.sub(
        pattern,
        lambda match: f"{match.group(1)}{safe_value}{match.group(2)}",
        svg,
        count=1,
    )


def update_svg(path: Path, github: str, activity: str) -> None:
    svg = path.read_text(encoding="utf-8")
    svg = replace_text(svg, "github_data", github)
    svg = replace_text(svg, "activity_data", activity)
    path.write_text(svg, encoding="utf-8")


def main() -> None:
    github, activity = summary()
    for filename in ("dark.svg", "light.svg"):
        update_svg(ROOT / filename, github, activity)


if __name__ == "__main__":
    main()
