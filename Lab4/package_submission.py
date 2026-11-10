"""Package the Lab4 submission without including the source dataset."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT / "LAB4_Golek_Aleksandra_Karczmarczyk_Klaudia.zip"
REQUIRED_FILES = (
    ROOT / "README.md",
    ROOT / "requirements.txt",
    ROOT / "run_experiments.py",
    ROOT / "generate_plots.py",
    ROOT / "generate_report.py",
    ROOT / "prepare_data.py",
    ROOT / "preprocess_data.py",
    ROOT / "run_all.py",
    ROOT / "wyniki" / "all_results.csv",
    ROOT / "wykresy" / "f1_wszystkie_polaczenia.png",
    ROOT / "wykresy" / "porownanie_metod_strojenia.png",
    ROOT / "sprawozdanie" / "Sprawozdanie_Lab4.pdf",
    ROOT / "sprawozdanie" / "Sprawozdanie_Lab4.md",
)


def main() -> None:
    missing = [path for path in REQUIRED_FILES if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Cannot package Lab4 before required artifacts exist: "
            + ", ".join(str(path) for path in missing)
        )
    confusion_matrices = list((ROOT / "wykresy" / "macierze_pomylek").glob("*.png"))
    if len(confusion_matrices) != 43:
        raise ValueError(
            "Expected 42 per-pair confusion matrices and one Optuna matrix; "
            f"found {len(confusion_matrices)}."
        )

    files = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path == ARCHIVE:
            continue
        relative = path.relative_to(ROOT)
        if relative.parts[0] in {"data", "__pycache__", ".venv"}:
            continue
        if path.suffix in {".pyc", ".pyo"} or path.name.startswith("~$"):
            continue
        files.append((path, relative))

    if any(relative.parts[0] == "data" for _, relative in files):
        raise RuntimeError("Dataset files must not be included in the submission archive.")

    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(ARCHIVE, "w", compression=ZIP_DEFLATED, compresslevel=8) as archive:
        for path, relative in sorted(files, key=lambda pair: pair[1].as_posix().lower()):
            archive.write(path, arcname=relative.as_posix())

    with ZipFile(ARCHIVE) as archive:
        names = archive.namelist()
        if not names or any(name.startswith("data/") for name in names):
            raise RuntimeError("Submission archive is empty or contains the dataset.")
    print(f"Created {ARCHIVE} ({len(files)} files, dataset excluded).")


if __name__ == "__main__":
    main()
