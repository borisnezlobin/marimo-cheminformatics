"""Run the whole build in order, then verify it.

Run: python build_all.py
"""

import subprocess
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = [
    ("drugs.csv", "build_drugs.py"),
    ("fda_roles.csv", "build_fda_roles.py"),
    ("clinical_auc.csv", "build_clinical_auc.py"),
    ("measured.csv and measured_full_provenance.json", "build_measured.py"),
    ("sources.json", "build_sources_doc.py"),
    ("game.json, game_provenance.json and the game structure cards", "build_game.py"),
    ("VERIFIED.md", "verify.py"),
    ("GAME_VERIFIED.md", "verify_game.py"),
]


def main() -> None:
    for label, script in STEPS:
        print(f"\n=== {label} ({script}) ===", flush=True)
        result = subprocess.run([sys.executable, os.path.join(HERE, script)], cwd=HERE)
        if result.returncode != 0:
            sys.exit(f"{script} failed with exit code {result.returncode}")
    print("\nBuild complete. Read VERIFIED.md before quoting any number.")


if __name__ == "__main__":
    main()
