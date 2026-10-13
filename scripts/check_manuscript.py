"""Render every content/*.md with StrictUndefined so a missing or misspelt variable fails CI early.

Manubot renders the same templates itself; this check only catches undefined variables.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import jinja2
import yaml

ROOT = Path(__file__).resolve().parents[1]


def render_all(variables: dict, content: Path) -> dict[str, str]:
    meta = yaml.safe_load((content / "metadata.yaml").read_text().replace("---", "", 2))
    manubot_stub = {"title": meta["title"], "authors": meta["authors"], "date_long": "(build date)"}
    env = jinja2.Environment(undefined=jinja2.StrictUndefined, comment_start_string="{##",
                             comment_end_string="##}", keep_trailing_newline=True)
    out = {}
    for path in sorted(content.glob("[0-9][0-9].*.md")):
        out[path.name] = env.from_string(path.read_text()).render(results=variables, manubot=manubot_stub)
    return out


def main() -> int:
    variables = json.loads((ROOT / "build/variables.json").read_text())
    try:
        rendered = render_all(variables, ROOT / "content")
    except jinja2.UndefinedError as exc:
        print(f"ERROR: undefined manuscript variable: {exc}")
        return 1
    print(f"rendered {len(rendered)} sections without undefined variables")
    return 0


if __name__ == "__main__":
    sys.exit(main())
