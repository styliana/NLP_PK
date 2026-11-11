"""Run every Lab4 preparation, experiment, reporting, and packaging step."""

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STEPS = (
    "scripts/prepare_data.py",
    "scripts/preprocess_data.py",
    "scripts/run_experiments.py",
    "scripts/generate_plots.py",
    "scripts/additional_analysis.py",
    "scripts/generate_report.py",
    "scripts/package_submission.py",
)


def main() -> None:
    for step in STEPS:
        script = ROOT / step
        print(f"\n=== Lab4: {step} ===", flush=True)
        subprocess.run([sys.executable, str(script)], check=True, cwd=ROOT.parent)
    print("\nLab4 pipeline completed successfully.", flush=True)


if __name__ == "__main__":
    main()
