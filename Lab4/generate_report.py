"""Generate the detailed Polish Lab4 report as Markdown and PDF."""

import csv
import html
import json
import os
import platform
from importlib.metadata import version
from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    LongTable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    TableStyle,
)

if __package__:
    from .run_experiments import GRID_SPACE, SEARCH_SPACE
else:
    from run_experiments import GRID_SPACE, SEARCH_SPACE


ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "wyniki"
REPORT_DIR = ROOT / "sprawozdanie"
MATRICES_DIR = ROOT / "wykresy" / "macierze_pomylek"
PREPROCESSED_DIR = ROOT / "data" / "preprocessed"
ALL_RESULTS_PATH = RESULTS_DIR / "all_results.csv"
REPORT_MD = REPORT_DIR / "Sprawozdanie_Lab4.md"
REPORT_PDF = REPORT_DIR / "Sprawozdanie_Lab4.pdf"
CLASSIFIERS = [
    "Logistic Regression",
    "Linear SVC",
    "RBF SVC",
    "K-Nearest Neighbors",
    "Decision Tree",
    "Random Forest",
    "SGD Classifier",
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def scaled_image(path: Path, width_cm: float) -> Image:
    image_width, image_height = ImageReader(str(path)).getSize()
    width = width_cm * cm
    return Image(
        str(path),
        width=width,
        height=width * image_height / image_width,
    )


def software_versions() -> str:
    packages = (
        ("NLTK", "nltk"),
        ("scikit-learn", "scikit-learn"),
        ("Gensim", "gensim"),
        ("Optuna", "optuna"),
        ("Matplotlib", "matplotlib"),
    )
    return (
        f"Python {platform.python_version()}; "
        + "; ".join(f"{label} {version(package)}" for label, package in packages)
    )


def load_results() -> list[dict[str, str]]:
    with ALL_RESULTS_PATH.open(encoding="utf-8", newline="") as input_file:
        rows = list(csv.DictReader(input_file))
    if len(rows) < 85:
        raise ValueError(f"Expected at least 85 result rows, found {len(rows)}")
    return rows


def best_for_method(rows: list[dict[str, str]], method: str) -> dict[str, str]:
    candidates = [row for row in rows if row["method"].startswith(method)]
    if not candidates:
        raise ValueError(f"No evaluation results found for {method}")
    return max(candidates, key=lambda row: float(row["cv_f1"]))


def representation_rows(details: dict[str, Any]) -> list[tuple[str, str, str]]:
    specifications = {
        "Bag-of-Words": (
            "rzadka",
            "CountVectorizer; unigramy, min_df=2, maks. 30 000 cech",
        ),
        "Word TF-IDF": (
            "rzadka",
            "TfidfVectorizer; n-gramy (1, 2), min_df=2, maks. 50 000 cech",
        ),
        "Character TF-IDF": (
            "rzadka",
            "TfidfVectorizer(analyzer='char_wb'); n-gramy znakowe (3, 5), "
            "min_df=2, maks. 30 000 cech",
        ),
        "Word2Vec mean": (
            "gęsta, uczona lokalnie",
            "Word2Vec Skip-gram; 100 wymiarów, okno 5, min_count=1, 20 epok; "
            "średnia wektorów słów",
        ),
        "Doc2Vec": (
            "gęsta, uczona lokalnie",
            "Doc2Vec DBOW (dm=0); 100 wymiarów, okno 5, min_count=2, 30 epok",
        ),
        "GloVe mean (pretrained)": (
            "gęsta, gotowa",
            "glove-wiki-gigaword-100; 100 wymiarów, średnia wektorów słów",
        ),
    }
    rows = []
    for name, (kind, settings) in specifications.items():
        if name not in details:
            raise ValueError(f"Missing representation details for {name}")
        shape = details[name]["shape_train"]
        rows.append((name, kind, f"{settings}; macierz treningowa: {shape[0]} × {shape[1]}"))
    return rows


def build_markdown(
    summary: dict[str, Any],
    preprocessing: dict[str, Any],
    results: list[dict[str, str]],
) -> str:
    train_stats = preprocessing["splits"]["train"]
    test_stats = preprocessing["splits"]["test"]
    best_random = best_for_method(results, "RandomizedSearchCV")
    best_grid = best_for_method(results, "GridSearchCV")
    best_optuna = best_for_method(results, "Optuna")
    lines = [
        "# Laboratorium 4 — wektoryzacja tekstu i klasyfikacja sentymentu",
        "",
        "**Poziom:** 5.0  ",
        "**Zadanie:** B — analiza sentymentu recenzji filmowych  ",
        "**Autorzy:** Aleksandra Gołek, Klaudia Karczmarczyk  ",
        f"**Data wygenerowania:** {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %Z')}",
        "",
        "## 1. Cel i zakres pracy",
        "",
        "Celem było porównanie sześciu reprezentacji tekstu i siedmiu klasyfikatorów "
        "dla binarnej analizy sentymentu, a następnie zbadanie trzech metod doboru "
        "hiperparametrów: Random Search, Grid Search i Optuny. Każdy z 42 układów "
        "reprezentacja–klasyfikator oceniono z użyciem RandomizedSearchCV i "
        "GridSearchCV. Optuna wykonała 30 prób, wybierając reprezentację, klasyfikator "
        "i jego hiperparametry w jednym badaniu.",
        "",
        "## 2. Zbiór danych i podział",
        "",
        "Użyto Cornell Sentence Polarity v1.0 (Pang i Lee): 10 662 zdań z recenzji "
        "filmowych, po 5 331 przykładów negatywnych (etykieta 0) i pozytywnych "
        "(etykieta 1). Dane pobrano przez korpus NLTK `sentence_polarity`. Zbiór "
        "podzielono stratyfikowanie w proporcji 80/20 z `random_state=42`.",
        "",
        "| Podzbiór | Liczba przykładów | Negatywne (0) | Pozytywne (1) | Średnia tokenów po preprocessing |",
        "|---|---:|---:|---:|---:|",
        f"| Trening | {train_stats['examples']} | "
        f"{train_stats['class_counts']['0']} | {train_stats['class_counts']['1']} | "
        f"{train_stats['mean_tokens_after']:.2f} |",
        f"| Test | {test_stats['examples']} | "
        f"{test_stats['class_counts']['0']} | {test_stats['class_counts']['1']} | "
        f"{test_stats['mean_tokens_after']:.2f} |",
        "",
        "Zbiór testowy był odłożony przed preprocessingiem i strojenie nie korzystało "
        "z jego etykiet. Word2Vec i Doc2Vec uczono wyłącznie na podzbiorze treningowym; "
        "GloVe jest modelem zewnętrznym, wytrenowanym wcześniej na korpusie Wikipedia "
        "+ Gigaword.",
        "",
        "## 3. Preprocessing",
        "",
        "Zdania przetworzono przez: (1) lowercase, (2) tokenizację wyrażeń "
        "alfabetycznych i apostrofów, (3) usunięcie angielskich stop words z "
        "`sklearn.feature_extraction.text.ENGLISH_STOP_WORDS`, (4) tagowanie "
        "części mowy Penn Treebank, (5) lematyzację WordNet z uwzględnieniem POS. "
        "Zachowano słowa negacji i kontrastu, m.in. `not`, `no`, `never`, `but`, "
        "`without`, oraz formy zakończone na `n't`, aby nie zatrzeć polaryzacji. "
        "Jeśli filtr stop words usunąłby wszystkie tokeny zdania, zachowano jego "
        "zlematyzowane tokeny. Oryginalny tekst pozostał w danych obok `processed_text`.",
        "",
        f"Średnia liczba tokenów zmniejszyła się z {train_stats['mean_tokens_before']:.2f} "
        f"do {train_stats['mean_tokens_after']:.2f} w treningu oraz z "
        f"{test_stats['mean_tokens_before']:.2f} do {test_stats['mean_tokens_after']:.2f} "
        "w teście.",
        "",
        "## 4. Reprezentacje tekstu",
        "",
        "| Reprezentacja | Rodzaj | Parametry |",
        "|---|---|---|",
    ]
    for name, kind, settings in representation_rows(summary["representation_details"]):
        lines.append(f"| {name} | {kind} | {settings} |")
    lines.extend(
        [
            "",
            "Wszystkie wektory gęste wystandaryzowano przez `StandardScaler` dopasowany "
            "wyłącznie do treningu. Dla średniej embeddingów podano pokrycie słownictwa "
            "modelu w `wyniki/representation_details.json`. W Word2Vec użyto modelu "
            "Skip-gram uczonego na tokenach tekstu treningowego; Doc2Vec używa "
            "wariantu DBOW (`dm=0`), a dla testu wektory dokumentów wywnioskowano "
            "przez `infer_vector`.",
            "",
            "## 5. Klasyfikatory",
            "",
            "Każdy klasyfikator uruchomiono na każdej reprezentacji:",
            "",
        ]
    )
    lines.extend(f"- {name}" for name in CLASSIFIERS)
    lines.extend(
        [
            "",
            "Zakresy hiperparametrów (Random Search losował konfiguracje z podanych "
            "wartości, a Grid Search badał pełny iloczyn siatki):",
            "",
            "| Klasyfikator | Random Search — wartości | Grid Search — wartości |",
            "|---|---|---|",
        ]
    )
    for classifier in CLASSIFIERS:
        random_values = json.dumps(
            SEARCH_SPACE[classifier], ensure_ascii=False, sort_keys=True
        ).replace("|", "\\|")
        grid_values = json.dumps(
            GRID_SPACE[classifier], ensure_ascii=False, sort_keys=True
        ).replace("|", "\\|")
        lines.append(f"| {classifier} | `{random_values}` | `{grid_values}` |")
    lines.extend(
        [
            "",
            "## 6. Strojenie i protokół oceny",
            "",
            f"- **Walidacja:** {summary['cross_validation']['method']}, "
            f"{summary['cross_validation']['splits']} foldy, tasowanie, "
            f"`random_state=42`; kryterium wyboru to F1 dla klasy pozytywnej.",
            f"- **Random Search:** {summary['random_search_iterations_per_pair']} "
            "losowane konfiguracje na każdą parę reprezentacja–klasyfikator "
            f"(42 pary, {summary['cross_validation']['splits']}-fold CV).",
            "- **Grid Search:** pełny przegląd jawnej, ograniczonej siatki parametrów "
            "dla każdej z 42 par; liczebności siatek zapisano w "
            "`wyniki/experiment_summary.json`.",
            f"- **Optuna:** {summary['optuna_trials']} próby TPE w jednym badaniu "
            "optymalizującym łącznie reprezentację, klasyfikator i jego hiperparametry; "
            f"każda próba oceniana tym samym "
            f"{summary['cross_validation']['splits']}-fold CV.",
            f"- **Próbka strojenia:** wspólna, stratyfikowana próbka "
            f"{summary['cv_tuning_sample_size']} rekordów treningowych dla wszystkich "
            "modeli i metod. Wybrane konfiguracje dopasowano ponownie na pełnym treningu, "
            "z wyjątkiem RBF SVC (próbka 1 500 przykładów ze względu na koszt jądra).",
            "- Zbiór testowy użyto dopiero po zakończeniu strojenia, do jednorazowego "
            "wyliczenia accuracy, F1 i macierzy pomyłek.",
            "",
            "## 7. Wyniki na zbiorze testowym",
            "",
            "Wyniki poniżej zawierają 84 strojenia (42 pary × Random/Grid) oraz "
            "najlepszy układ wybrany przez 30-próbkowe badanie Optuna. `CV F1` "
            "służył do wyboru modelu; accuracy i F1 są wynikiem na odłożonym teście.",
            "",
            "| Reprezentacja | Klasyfikator | Metoda | CV F1 | Accuracy | F1 | TN | FP | FN | TP | Parametry |",
            "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in results:
        params = json.dumps(json.loads(row["best_params"]), ensure_ascii=False, sort_keys=True)
        params = params.replace("|", "\\|")
        lines.append(
            f"| {row['representation']} | {row['classifier']} | {row['method']} | "
            f"{float(row['cv_f1']):.4f} | {float(row['accuracy']):.4f} | "
            f"{float(row['f1']):.4f} | {row['tn']} | {row['fp']} | {row['fn']} | "
            f"{row['tp']} | `{params}` |"
        )
    lines.extend(
        [
            "",
            "### Porównanie najlepszych konfiguracji",
            "",
            "| Metoda strojenia | Reprezentacja | Klasyfikator | CV F1 | Accuracy test | F1 test |",
            "|---|---|---|---:|---:|---:|",
        ]
    )
    for method, row in (
        ("Random Search", best_random),
        ("Grid Search", best_grid),
        ("Optuna", best_optuna),
    ):
        lines.append(
            f"| {method} | {row['representation']} | {row['classifier']} | "
            f"{float(row['cv_f1']):.4f} | {float(row['accuracy']):.4f} | "
            f"{float(row['f1']):.4f} |"
        )
    lines.extend(
        [
            "",
            "### Wykresy i macierze pomyłek",
            "",
            "- `../wykresy/f1_wszystkie_polaczenia.png` — testowy F1 dla 42 par, "
            "osobno po Random Search i Grid Search.",
            "- `../wykresy/porownanie_metod_strojenia.png` — testowe wyniki "
            "najlepszych konfiguracji wybranych na podstawie CV.",
            "- `../wykresy/macierze_pomylek/` — osobna macierz pomyłek dla każdego "
            f"z 42 połączeń (wariant o wyższym CV F1 spośród Random/Grid) oraz "
            "macierz modelu wybranego przez Optunę.",
            "",
            "## 8. Wnioski i ograniczenia",
            "",
            f"Najlepsza konfiguracja Random Search według CV: "
            f"{best_random['representation']} + {best_random['classifier']} "
            f"(CV F1={float(best_random['cv_f1']):.4f}; test F1="
            f"{float(best_random['f1']):.4f}). Najlepszy Grid Search: "
            f"{best_grid['representation']} + {best_grid['classifier']} "
            f"(CV F1={float(best_grid['cv_f1']):.4f}; test F1="
            f"{float(best_grid['f1']):.4f}). Optuna wybrała "
            f"{best_optuna['representation']} + {best_optuna['classifier']} "
            f"(CV F1={float(best_optuna['cv_f1']):.4f}; test F1="
            f"{float(best_optuna['f1']):.4f}).",
            "",
            "Wnioski o przewadze metod odnoszą się do zastosowanego budżetu i "
            "ograniczonych siatek, nie do pełnej przestrzeni hiperparametrów. Uśrednianie "
            "embeddingów redukuje informację o kolejności słów; Word2Vec/Doc2Vec "
            "uczone są na stosunkowo małym korpusie; gotowe GloVe wnosi wiedzę "
            "zewnętrzną i ma ograniczone pokrycie słów. Wyniki dotyczą wyłącznie "
            "angielskich krótkich recenzji z Cornell Sentence Polarity i jednego "
            "stratyfikowanego podziału testowego.",
            "",
            f"Cały eksperyment trwał {summary['elapsed_seconds'] / 60:.1f} min. "
            "Powtórzenie zapewnia stałe ziarno losowości; szczegóły wszystkich "
            "konfiguracji, wyniki i statystyki znajdują się w katalogu `wyniki/`.",
            "",
            "## 9. Uruchomienie",
            "",
            "```powershell",
            "python -m pip install -r Lab4/requirements.txt",
            "python Lab4/prepare_data.py",
            "python Lab4/preprocess_data.py",
            "python Lab4/run_experiments.py",
            "python Lab4/generate_plots.py",
            "python Lab4/generate_report.py",
            "```",
            "",
            "## Literatura i źródła",
            "",
            "1. Pang, B. i Lee, L. (2005), Cornell Sentence Polarity v1.0, "
            "https://www.cs.cornell.edu/people/pabo/movie-review-data/.",
            "2. NLTK, `sentence_polarity`, WordNet i POS tagger, "
            "https://www.nltk.org/.",
            "3. Pennington, J., Socher, R. i Manning, C. (2014), GloVe: Global "
            "Vectors for Word Representation, EMNLP.",
            "4. Scikit-learn, dokumentacja `model_selection`, `feature_extraction` "
            "i klasyfikatorów, https://scikit-learn.org/.",
            "5. Optuna, dokumentacja optymalizacji hiperparametrów, "
            "https://optuna.org/.",
            "",
            "## Środowisko",
            "",
            software_versions() + ".",
        ]
    )
    return "\n".join(lines) + "\n"


def register_report_fonts() -> tuple[str, str]:
    windows_dir = Path(os.environ.get("WINDIR", r"C:\Windows"))
    candidates = [
        (windows_dir / "Fonts" / "arial.ttf", windows_dir / "Fonts" / "arialbd.ttf"),
        (
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ),
    ]
    for regular, bold in candidates:
        if regular.is_file() and bold.is_file():
            pdfmetrics.registerFont(TTFont("Lab4Body", str(regular)))
            pdfmetrics.registerFont(TTFont("Lab4Bold", str(bold)))
            return "Lab4Body", "Lab4Bold"
    raise FileNotFoundError(
        "A TrueType font supporting Polish characters is required to generate the PDF."
    )


def paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def markdown_to_pdf(summary: dict[str, Any], results: list[dict[str, str]]) -> None:
    regular_font, bold_font = register_report_fonts()
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="LabTitle",
            parent=styles["Title"],
            fontName=bold_font,
            fontSize=20,
            leading=24,
            alignment=TA_CENTER,
            spaceAfter=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="LabHeading",
            parent=styles["Heading2"],
            fontName=bold_font,
            fontSize=13,
            leading=16,
            spaceBefore=10,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="LabBody",
            parent=styles["BodyText"],
            fontName=regular_font,
            fontSize=8.5,
            leading=12,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="LabSmall",
            parent=styles["BodyText"],
            fontName=regular_font,
            fontSize=6.2,
            leading=7.5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="LabTableHeader",
            parent=styles["BodyText"],
            fontName=bold_font,
            fontSize=6.8,
            leading=8,
            textColor=colors.white,
        )
    )
    page_size = landscape(A4)
    story = [
        paragraph("Laboratorium 4 — analiza sentymentu", styles["LabTitle"]),
        paragraph(
            "Poziom 5.0 | Zadanie B | Aleksandra Gołek, Klaudia Karczmarczyk",
            styles["LabBody"],
        ),
        paragraph(
            f"10 662 zdania Cornell Sentence Polarity; 6 reprezentacji; "
            f"7 klasyfikatorów; 30 prób Optuny. Eksperyment: "
            f"{summary['elapsed_seconds'] / 60:.1f} min.",
            styles["LabBody"],
        ),
        paragraph("1. Cel i zakres pracy", styles["LabHeading"]),
        paragraph(
            "Porównano sześć reprezentacji tekstu i siedem klasyfikatorów dla "
            "binarnej analizy sentymentu. Każdą z 42 par reprezentacja–klasyfikator "
            "strojoną metodą RandomizedSearchCV i GridSearchCV; Optuna wykonała "
            "30 prób TPE, wspólnie wybierając reprezentację, model i jego parametry.",
            styles["LabBody"],
        ),
        paragraph("2. Dane i preprocessing", styles["LabHeading"]),
        paragraph(
            "Cornell Sentence Polarity v1.0 zawiera 10 662 krótkie recenzje: "
            "5 331 negatywnych (0) i 5 331 pozytywnych (1). Stratyfikowany podział "
            "80/20, random_state=42, dał 8 529 przykładów treningowych "
            "(4 264 negatywne, 4 265 pozytywne) oraz 2 133 testowe "
            "(1 067 negatywnych, 1 066 pozytywnych).",
            styles["LabBody"],
        ),
        paragraph(
            "Preprocessing: lowercase, tokenizacja, angielskie stop words, POS "
            "tagging Penn Treebank i lematyzacja WordNet. Negacje i kontrast "
            "(m.in. not, no, never, but, without oraz n't) zostały zachowane. "
            "Tagowanie, lematyzacja, Word2Vec i Doc2Vec nie korzystały z testu; "
            "parametry skalowania wektorów gęstych dopasowano wyłącznie na treningu.",
            styles["LabBody"],
        ),
        paragraph("3. Reprezentacje", styles["LabHeading"]),
    ]
    representation_table = [
        [
            paragraph("Reprezentacja", styles["LabTableHeader"]),
            paragraph("Rodzaj i parametry", styles["LabTableHeader"]),
            paragraph("Wymiar train", styles["LabTableHeader"]),
        ]
    ]
    for name, kind, settings in representation_rows(summary["representation_details"]):
        details = summary["representation_details"][name]
        representation_table.append(
            [
                paragraph(html.escape(name), styles["LabSmall"]),
                paragraph(html.escape(f"{kind}: {settings}"), styles["LabSmall"]),
                paragraph(str(details["shape_train"][1]), styles["LabSmall"]),
            ]
        )
    story.append(
        LongTable(
            representation_table,
            colWidths=[4.5 * cm, 17.4 * cm, 2.2 * cm],
            repeatRows=1,
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#24476b")),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef3f8")]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ]
            ),
        )
    )
    story.extend(
        [
            paragraph("4. Klasyfikatory i strojenie", styles["LabHeading"]),
            paragraph(
                "Modele: Logistic Regression, Linear SVC, RBF SVC, K-Nearest "
                "Neighbors, Decision Tree, Random Forest i SGD Classifier. "
                f"Random Search losował {summary['random_search_iterations_per_pair']} "
                "konfiguracje na parę, Grid Search przeglądał ograniczone siatki, "
                "a Optuna przeprowadziła "
                f"{summary['optuna_trials']} próby TPE. W każdej metodzie "
                f"użyto {summary['cross_validation']['splits']}-fold "
                "StratifiedKFold z tasowaniem i random_state=42; optymalizowano "
                "F1 klasy pozytywnej. Zbiór testowy oceniono dopiero po wyborze "
                f"parametrów. Każdy model stroił na wspólnej, stratyfikowanej próbce "
                f"{summary['cv_tuning_sample_size']} przykładów, a wybrane konfiguracje "
                "dopasowano ponownie na pełnym treningu, z wyjątkiem RBF SVC, którego "
                f"końcowe dopasowanie na próbce {summary['rbf_svc_final_fit_size']} "
                "rekordów ogranicza koszt obliczania jądra.",
                styles["LabBody"],
            ),
            paragraph("Zakresy hiperparametrów", styles["LabHeading"]),
        ]
    )
    search_space_table = [
        [
            paragraph(label, styles["LabTableHeader"])
            for label in ("Klasyfikator", "Random Search", "Grid Search")
        ]
    ]
    for classifier in CLASSIFIERS:
        search_space_table.append(
            [
                paragraph(html.escape(classifier), styles["LabSmall"]),
                paragraph(
                    html.escape(
                        json.dumps(
                            SEARCH_SPACE[classifier],
                            ensure_ascii=False,
                            sort_keys=True,
                        )
                    ),
                    styles["LabSmall"],
                ),
                paragraph(
                    html.escape(
                        json.dumps(
                            GRID_SPACE[classifier],
                            ensure_ascii=False,
                            sort_keys=True,
                        )
                    ),
                    styles["LabSmall"],
                ),
            ]
        )
    story.append(
        LongTable(
            search_space_table,
            colWidths=[4.2 * cm, 10.1 * cm, 10.1 * cm],
            repeatRows=1,
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#24476b")),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef3f8")]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ]
            ),
        )
    )
    story.append(paragraph("5. Wyniki — porównanie metod", styles["LabHeading"]))
    best_methods = [
        ("Random Search", best_for_method(results, "RandomizedSearchCV")),
        ("Grid Search", best_for_method(results, "GridSearchCV")),
        ("Optuna", best_for_method(results, "Optuna")),
    ]
    best_table = [
        [
            paragraph(label, styles["LabTableHeader"])
            for label in ("Metoda", "Reprezentacja", "Klasyfikator", "CV F1", "Accuracy", "F1")
        ]
    ]
    for method, row in best_methods:
        best_table.append(
            [
                paragraph(html.escape(method), styles["LabSmall"]),
                paragraph(html.escape(row["representation"]), styles["LabSmall"]),
                paragraph(html.escape(row["classifier"]), styles["LabSmall"]),
                paragraph(f"{float(row['cv_f1']):.4f}", styles["LabSmall"]),
                paragraph(f"{float(row['accuracy']):.4f}", styles["LabSmall"]),
                paragraph(f"{float(row['f1']):.4f}", styles["LabSmall"]),
            ]
        )
    story.append(
        LongTable(
            best_table,
            colWidths=[3.4 * cm, 5.4 * cm, 4.3 * cm, 2.4 * cm, 2.4 * cm, 2.4 * cm],
            repeatRows=1,
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#24476b")),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef3f8")]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ]
            ),
        )
    )
    story.extend(
        [
            paragraph(
                "Wyniki wszystkich par reprezentacja–klasyfikator i metod strojenia",
                styles["LabHeading"],
            ),
            paragraph(
                "Poniższa tabela raportuje wszystkie 84 wyniki Random/Grid oraz "
                "wynik wybrany przez Optunę. Parametry wybierano na CV; metryki "
                "testowe nie wpływały na wybór.",
                styles["LabBody"],
            ),
        ]
    )
    detailed_header = (
        "Reprezentacja",
        "Klasyfikator",
        "Metoda",
        "CV F1",
        "Accuracy",
        "F1",
        "Najlepsze parametry",
    )
    detailed_table = [
        [
            paragraph(html.escape(label), styles["LabTableHeader"])
            for label in detailed_header
        ]
    ]
    for row in results:
        params = json.dumps(
            json.loads(row["best_params"]), ensure_ascii=False, sort_keys=True
        )
        detailed_table.append(
            [
                paragraph(html.escape(row["representation"]), styles["LabSmall"]),
                paragraph(html.escape(row["classifier"]), styles["LabSmall"]),
                paragraph(html.escape(row["method"]), styles["LabSmall"]),
                paragraph(f"{float(row['cv_f1']):.4f}", styles["LabSmall"]),
                paragraph(f"{float(row['accuracy']):.4f}", styles["LabSmall"]),
                paragraph(f"{float(row['f1']):.4f}", styles["LabSmall"]),
                paragraph(html.escape(params), styles["LabSmall"]),
            ]
        )
    story.append(
        LongTable(
            detailed_table,
            colWidths=[
                3.3 * cm,
                3.2 * cm,
                3.2 * cm,
                1.6 * cm,
                1.8 * cm,
                1.5 * cm,
                9.2 * cm,
            ],
            repeatRows=1,
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#24476b")),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef3f8")]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            ),
        )
    )
    for relative_path, caption in (
        ("../wykresy/porownanie_metod_strojenia.png", "Rys. 1. Wyniki najlepszych konfiguracji według CV F1."),
        ("../wykresy/f1_wszystkie_polaczenia.png", "Rys. 2. Testowy F1 dla 42 par reprezentacja–klasyfikator."),
    ):
        image_path = (REPORT_DIR / relative_path).resolve()
        if not image_path.is_file():
            raise FileNotFoundError(f"Required report figure not found: {image_path}")
        image = scaled_image(image_path, 17)
        story.extend([PageBreak(), image, paragraph(caption, styles["LabSmall"])])

    confusion_path = MATRICES_DIR / "optuna_best_model.png"
    if confusion_path.is_file():
        image = scaled_image(confusion_path, 10)
        story.extend(
            [
                paragraph("6. Macierz pomyłek — model Optuny", styles["LabHeading"]),
                image,
                paragraph(
                    "Macierze dla 42 par (najlepszy wariant Random/Grid według "
                    "walidacyjnego F1) zapisano osobno w "
                    "`Lab4/wykresy/macierze_pomylek/`. Dane TN/FP/FN/TP dla obu "
                    "metod znajdują się w `Lab4/wyniki/all_results.csv`.",
                    styles["LabBody"],
                ),
            ]
        )
    story.extend(
        [
            paragraph("7. Wnioski i ograniczenia", styles["LabHeading"]),
            paragraph(
                "Najlepszy model każdego strojenia w tabeli wybrano według CV F1, "
                "a nie wyników testowych. Rezultaty zależą od ograniczonych przestrzeni "
                "parametrów i 30-próbkowego budżetu Optuny. Średnie embeddingów "
                "pomijają kolejność słów; Word2Vec i Doc2Vec były uczone na niewielkim "
                "zbiorze, a GloVe ma niepełne pokrycie słownictwa. Badanie dotyczy "
                "angielskich recenzji filmowych i jednego stratyfikowanego holdoutu.",
                styles["LabBody"],
            ),
            paragraph(
                "Szczegółowa tabela wszystkich 85 wyników, parametrów i macierzy "
                "pomylek znajduje się w `Lab4/wyniki/all_results.csv`; pełny opis "
                "implementacji, wszystkich wyników i źródeł w pliku "
                "`Sprawozdanie_Lab4.md`.",
                styles["LabBody"],
            ),
            paragraph("Środowisko: " + html.escape(software_versions()) + ".", styles["LabSmall"]),
        ]
    )

    def page_footer(canvas: Any, document: Any) -> None:
        canvas.saveState()
        canvas.setFont(regular_font, 7)
        canvas.setFillColor(colors.grey)
        canvas.drawString(1.2 * cm, 0.65 * cm, "Laboratorium 4 — analiza sentymentu")
        canvas.drawRightString(page_size[0] - 1.2 * cm, 0.65 * cm, f"Strona {document.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        str(REPORT_PDF),
        pagesize=page_size,
        rightMargin=1.2 * cm,
        leftMargin=1.2 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
        title="Laboratorium 4 — analiza sentymentu",
        author="Aleksandra Gołek, Klaudia Karczmarczyk",
    )
    doc.build(story, onFirstPage=page_footer, onLaterPages=page_footer)


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    summary = load_json(RESULTS_DIR / "experiment_summary.json")
    preprocessing = load_json(PREPROCESSED_DIR / "preprocessing_summary.json")
    results = load_results()
    markdown = build_markdown(summary, preprocessing, results)
    REPORT_MD.write_text(markdown, encoding="utf-8")
    markdown_to_pdf(summary, results)
    print(f"Generated report source: {REPORT_MD}")
    print(f"Generated PDF report: {REPORT_PDF}")


if __name__ == "__main__":
    main()
