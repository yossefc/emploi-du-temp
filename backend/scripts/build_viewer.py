"""Assemble la page de consultation : template.html + données du planning.

    DATABASE_URL='sqlite:///./demo.db' python scripts/build_viewer.py [schedule_id]
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent / "viewer"
TEMPLATE = ROOT / "template.html"
DATA = ROOT / "data.json"
OUT = ROOT / "index.html"


def main():
    args = [sys.executable, str(Path(__file__).parent / "export_viewer.py")]
    if len(sys.argv) > 1:
        args.append(sys.argv[1])
    res = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
    print(res.stdout.strip() or res.stderr.strip())
    if res.returncode != 0:
        sys.exit(res.returncode)

    html = TEMPLATE.read_text(encoding="utf-8")
    OUT.write_text(html.replace("__DATA__", DATA.read_text(encoding="utf-8")),
                   encoding="utf-8")
    print(f"✅ {OUT}  ({OUT.stat().st_size // 1024} Ko)")


if __name__ == "__main__":
    main()
