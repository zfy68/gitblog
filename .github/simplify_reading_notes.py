# One-shot: replace issue bodies #95-#100 with the files in .github/simplify/.
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

TOKEN = os.environ["GH_TOKEN"]
REPO = os.environ["GITHUB_REPOSITORY"]
ROOT = Path(__file__).resolve().parent / "simplify"


def request(method, url, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "gitblog-simplify",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()
        raise SystemExit(f"{method} {url} -> {exc.code} {detail}") from exc


def main():
    for path in sorted(ROOT.glob("*.md")):
        number = path.stem
        body = path.read_text(encoding="utf-8")
        current = request("GET", f"https://api.github.com/repos/{REPO}/issues/{number}")
        if current.get("body") == body:
            print(f"#{number} unchanged")
            continue
        request(
            "PATCH",
            f"https://api.github.com/repos/{REPO}/issues/{number}",
            {"body": body},
        )
        print(f"#{number} updated title={current.get('title')!r}")


if __name__ == "__main__":
    main()
