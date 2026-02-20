from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: python scripts/write_latest_json.py <version> <url> [notes] [output]")
        return 1

    version = sys.argv[1].strip()
    url = sys.argv[2].strip()
    notes = sys.argv[3].strip() if len(sys.argv) >= 4 else ""
    output = Path(sys.argv[4]) if len(sys.argv) >= 5 else Path("latest.json")

    payload = {"version": version, "url": url, "notes": notes}
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
