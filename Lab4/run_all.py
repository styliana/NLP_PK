"""Run every Lab4 preparation, experiment, reporting, and packaging step."""

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
STEPS = (
    "prepare_data.py",
    "preprocess_data.py",
    "run_experiments.py",
    "generate_plots.py",
    "generate_report.py",
    "package_submission.py",
)


def main() -> None:
    for step in STEPS:
        script = ROOT / step
        print(f"\n=== Lab4: {step} ===", flush=True)
        subprocess.run([sys.executable, str(script)], check=True, cwd=ROOT.parent)
    print("\nLab4 pipeline completed successfully.", flush=True)


if __name__ == "__main__":
    main()
