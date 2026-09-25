"""Rebuild every derived file the Drain notebook reads, in order.

Run: python build_all.py
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = [
    ("data/drugs.csv", os.path.join(HERE, "build_drugs.py")),
    ("data/measured.csv and data/measured_full_provenance.json", os.path.join(HERE, "build_measured.py")),
    ("data/drain/*.csv", os.path.join(HERE, "build_drain_data.py")),
    ("widgets/drain.js and game/drain.html", os.path.join(HERE, "..", "game", "build.py")),
]


def main() -> None:
    for label, script in STEPS:
        print(f"\n=== {label} ({os.path.basename(script)}) ===", flush=True)
        result = subprocess.run([sys.executable, script], cwd=os.path.dirname(script))
        if result.returncode != 0:
            sys.exit(f"{script} failed with exit code {result.returncode}")
    print("\nBuild complete.")


if __name__ == "__main__":
    main()
