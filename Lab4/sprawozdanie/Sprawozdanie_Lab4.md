# Laboratorium 4 — wektoryzacja tekstu i klasyfikacja sentymentu

**Poziom:** 5.0  
**Zadanie:** B — analiza sentymentu recenzji filmowych  
**Autorzy:** Aleksandra Gołek, Klaudia Karczmarczyk  
**Data wygenerowania:** 2026-11-10 08:29 Środkowoeuropejski czas stand.

## 1. Cel i zakres pracy

Celem było porównanie sześciu reprezentacji tekstu i siedmiu klasyfikatorów dla binarnej analizy sentymentu, a następnie zbadanie trzech metod doboru hiperparametrów: Random Search, Grid Search i Optuny. Każdy z 42 układów reprezentacja–klasyfikator oceniono z użyciem RandomizedSearchCV i GridSearchCV. Optuna wykonała 30 prób, wybierając reprezentację, klasyfikator i jego hiperparametry w jednym badaniu.

## 2. Zbiór danych i podział

Użyto Cornell Sentence Polarity v1.0 (Pang i Lee): 10 662 zdań z recenzji filmowych, po 5 331 przykładów negatywnych (etykieta 0) i pozytywnych (etykieta 1). Dane pobrano przez korpus NLTK `sentence_polarity`. Zbiór podzielono stratyfikowanie w proporcji 80/20 z `random_state=42`.

| Podzbiór | Liczba przykładów | Negatywne (0) | Pozytywne (1) | Średnia tokenów po preprocessing |
|---|---:|---:|---:|---:|
| Trening | 8529 | 4264 | 4265 | 10.37 |
| Test | 2133 | 1067 | 1066 | 10.31 |

Zbiór testowy był odłożony przed preprocessingiem i strojenie nie korzystało z jego etykiet. Word2Vec i Doc2Vec uczono wyłącznie na podzbiorze treningowym; GloVe jest modelem zewnętrznym, wytrenowanym wcześniej na korpusie Wikipedia + Gigaword.

## 3. Preprocessing

Zdania przetworzono przez: (1) lowercase, (2) tokenizację wyrażeń alfabetycznych i apostrofów, (3) usunięcie angielskich stop words z `sklearn.feature_extraction.text.ENGLISH_STOP_WORDS`, (4) tagowanie części mowy Penn Treebank, (5) lematyzację WordNet z uwzględnieniem POS. Zachowano słowa negacji i kontrastu, m.in. `not`, `no`, `never`, `but`, `without`, oraz formy zakończone na `n't`, aby nie zatrzeć polaryzacji. Jeśli filtr stop words usunąłby wszystkie tokeny zdania, zachowano jego zlematyzowane tokeny. Oryginalny tekst pozostał w danych obok `processed_text`.

Średnia liczba tokenów zmniejszyła się z 18.87 do 10.37 w treningu oraz z 18.71 do 10.31 w teście.

## 4. Reprezentacje tekstu

| Reprezentacja | Rodzaj | Parametry |
|---|---|---|
| Bag-of-Words | rzadka | CountVectorizer; unigramy, min_df=2, maks. 30 000 cech; macierz treningowa: 8529 × 7451 |
| Word TF-IDF | rzadka | TfidfVectorizer; n-gramy (1, 2), min_df=2, maks. 50 000 cech; macierz treningowa: 8529 × 12484 |
| Character TF-IDF | rzadka | TfidfVectorizer(analyzer='char_wb'); n-gramy znakowe (3, 5), min_df=2, maks. 30 000 cech; macierz treningowa: 8529 × 30000 |
| Word2Vec mean | gęsta, uczona lokalnie | Word2Vec Skip-gram; 100 wymiarów, okno 5, min_count=1, 20 epok; średnia wektorów słów; macierz treningowa: 8529 × 100 |
| Doc2Vec | gęsta, uczona lokalnie | Doc2Vec DBOW (dm=0); 100 wymiarów, okno 5, min_count=2, 30 epok; macierz treningowa: 8529 × 100 |
| GloVe mean (pretrained) | gęsta, gotowa | glove-wiki-gigaword-100; 100 wymiarów, średnia wektorów słów; macierz treningowa: 8529 × 100 |

Wszystkie wektory gęste wystandaryzowano przez `StandardScaler` dopasowany wyłącznie do treningu. Dla średniej embeddingów podano pokrycie słownictwa modelu w `wyniki/representation_details.json`. W Word2Vec użyto modelu Skip-gram uczonego na tokenach tekstu treningowego; Doc2Vec używa wariantu DBOW (`dm=0`), a dla testu wektory dokumentów wywnioskowano przez `infer_vector`.

## 5. Klasyfikatory

Każdy klasyfikator uruchomiono na każdej reprezentacji:

- Logistic Regression
- Linear SVC
- RBF SVC
- K-Nearest Neighbors
- Decision Tree
- Random Forest
- SGD Classifier

Zakresy hiperparametrów (Random Search losował konfiguracje z podanych wartości, a Grid Search badał pełny iloczyn siatki):

| Klasyfikator | Random Search — wartości | Grid Search — wartości |
|---|---|---|
| Logistic Regression | `{"C": [0.1, 1.0, 10.0], "class_weight": [null, "balanced"]}` | `{"C": [0.1, 10.0], "class_weight": [null]}` |
| Linear SVC | `{"C": [0.1, 1.0, 10.0], "class_weight": [null, "balanced"]}` | `{"C": [0.1, 10.0], "class_weight": [null]}` |
| RBF SVC | `{"C": [0.1, 1.0, 10.0], "class_weight": [null, "balanced"], "gamma": ["scale", "auto"]}` | `{"C": [0.1, 10.0], "class_weight": [null], "gamma": ["scale"]}` |
| K-Nearest Neighbors | `{"n_neighbors": [3, 5, 7], "weights": ["uniform", "distance"]}` | `{"n_neighbors": [3, 7], "weights": ["distance"]}` |
| Decision Tree | `{"criterion": ["gini", "entropy"], "max_depth": [null, 20, 50], "min_samples_leaf": [1, 2]}` | `{"criterion": ["gini"], "max_depth": [null, 20], "min_samples_leaf": [1]}` |
| Random Forest | `{"max_depth": [null, 30], "max_features": ["sqrt", 0.5], "min_samples_leaf": [1, 2]}` | `{"max_depth": [null, 30], "max_features": ["sqrt"], "min_samples_leaf": [1]}` |
| SGD Classifier | `{"alpha": [1e-05, 0.0001, 0.001], "class_weight": [null, "balanced"], "loss": ["hinge", "log_loss"]}` | `{"alpha": [1e-05, 0.001], "class_weight": [null], "loss": ["hinge"]}` |

## 6. Strojenie i protokół oceny

- **Walidacja:** StratifiedKFold, 2 foldy, tasowanie, `random_state=42`; kryterium wyboru to F1 dla klasy pozytywnej.
- **Random Search:** 2 losowane konfiguracje na każdą parę reprezentacja–klasyfikator (42 pary, 2-fold CV).
- **Grid Search:** pełny przegląd jawnej, ograniczonej siatki parametrów dla każdej z 42 par; liczebności siatek zapisano w `wyniki/experiment_summary.json`.
- **Optuna:** 30 próby TPE w jednym badaniu optymalizującym łącznie reprezentację, klasyfikator i jego hiperparametry; każda próba oceniana tym samym 2-fold CV.
- **Próbka strojenia:** wspólna, stratyfikowana próbka 1500 rekordów treningowych dla wszystkich modeli i metod. Wybrane konfiguracje dopasowano ponownie na pełnym treningu, z wyjątkiem RBF SVC (próbka 1 500 przykładów ze względu na koszt jądra).
- Zbiór testowy użyto dopiero po zakończeniu strojenia, do jednorazowego wyliczenia accuracy, F1 i macierzy pomyłek.

## 7. Wyniki na zbiorze testowym

Wyniki poniżej zawierają 84 strojenia (42 pary × Random/Grid) oraz najlepszy układ wybrany przez 30-próbkowe badanie Optuna. `CV F1` służył do wyboru modelu; accuracy i F1 są wynikiem na odłożonym teście.

| Reprezentacja | Klasyfikator | Metoda | CV F1 | Accuracy | F1 | TN | FP | FN | TP | Parametry |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| Bag-of-Words | Logistic Regression | RandomizedSearchCV | 0.6252 | 0.7487 | 0.7512 | 788 | 279 | 257 | 809 | `{"C": 0.1, "class_weight": null}` |
| Bag-of-Words | Logistic Regression | GridSearchCV | 0.6252 | 0.7487 | 0.7512 | 788 | 279 | 257 | 809 | `{"C": 0.1, "class_weight": null}` |
| Bag-of-Words | Linear SVC | RandomizedSearchCV | 0.6200 | 0.7478 | 0.7502 | 787 | 280 | 258 | 808 | `{"C": 0.1, "class_weight": null}` |
| Bag-of-Words | Linear SVC | GridSearchCV | 0.6220 | 0.7159 | 0.7166 | 761 | 306 | 300 | 766 | `{"C": 10.0, "class_weight": null}` |
| Bag-of-Words | RBF SVC | RandomizedSearchCV | 0.6727 | 0.6442 | 0.6804 | 566 | 501 | 258 | 808 | `{"C": 10.0, "class_weight": null, "gamma": "auto"}` |
| Bag-of-Words | RBF SVC | GridSearchCV | 0.6257 | 0.6728 | 0.6763 | 706 | 361 | 337 | 729 | `{"C": 10.0, "class_weight": null, "gamma": "scale"}` |
| Bag-of-Words | K-Nearest Neighbors | RandomizedSearchCV | 0.6258 | 0.5762 | 0.4271 | 892 | 175 | 729 | 337 | `{"n_neighbors": 3, "weights": "uniform"}` |
| Bag-of-Words | K-Nearest Neighbors | GridSearchCV | 0.6258 | 0.5762 | 0.4271 | 892 | 175 | 729 | 337 | `{"n_neighbors": 3, "weights": "distance"}` |
| Bag-of-Words | Decision Tree | RandomizedSearchCV | 0.5230 | 0.5959 | 0.6788 | 360 | 707 | 155 | 911 | `{"criterion": "entropy", "max_depth": 50, "min_samples_leaf": 1}` |
| Bag-of-Words | Decision Tree | GridSearchCV | 0.5887 | 0.6409 | 0.6197 | 743 | 324 | 442 | 624 | `{"criterion": "gini", "max_depth": null, "min_samples_leaf": 1}` |
| Bag-of-Words | Random Forest | RandomizedSearchCV | 0.5611 | 0.7271 | 0.7234 | 790 | 277 | 305 | 761 | `{"max_depth": null, "max_features": "sqrt", "min_samples_leaf": 2}` |
| Bag-of-Words | Random Forest | GridSearchCV | 0.6019 | 0.7121 | 0.6933 | 825 | 242 | 372 | 694 | `{"max_depth": null, "max_features": "sqrt", "min_samples_leaf": 1}` |
| Bag-of-Words | SGD Classifier | RandomizedSearchCV | 0.6219 | 0.7468 | 0.7507 | 780 | 287 | 253 | 813 | `{"alpha": 0.001, "class_weight": null, "loss": "log_loss"}` |
| Bag-of-Words | SGD Classifier | GridSearchCV | 0.6074 | 0.7164 | 0.7101 | 787 | 280 | 325 | 741 | `{"alpha": 1e-05, "class_weight": null, "loss": "hinge"}` |
| Word TF-IDF | Logistic Regression | RandomizedSearchCV | 0.6311 | 0.7375 | 0.7395 | 778 | 289 | 271 | 795 | `{"C": 0.1, "class_weight": null}` |
| Word TF-IDF | Logistic Regression | GridSearchCV | 0.6349 | 0.7595 | 0.7617 | 800 | 267 | 246 | 820 | `{"C": 10.0, "class_weight": null}` |
| Word TF-IDF | Linear SVC | RandomizedSearchCV | 0.6347 | 0.7665 | 0.7692 | 805 | 262 | 236 | 830 | `{"C": 0.1, "class_weight": null}` |
| Word TF-IDF | Linear SVC | GridSearchCV | 0.6347 | 0.7665 | 0.7692 | 805 | 262 | 236 | 830 | `{"C": 0.1, "class_weight": null}` |
| Word TF-IDF | RBF SVC | RandomizedSearchCV | 0.6344 | 0.6934 | 0.6978 | 724 | 343 | 311 | 755 | `{"C": 10.0, "class_weight": "balanced", "gamma": "scale"}` |
| Word TF-IDF | RBF SVC | GridSearchCV | 0.6464 | 0.6376 | 0.7163 | 384 | 683 | 90 | 976 | `{"C": 0.1, "class_weight": null, "gamma": "scale"}` |
| Word TF-IDF | K-Nearest Neighbors | RandomizedSearchCV | 0.6146 | 0.5152 | 0.0701 | 1060 | 7 | 1027 | 39 | `{"n_neighbors": 3, "weights": "uniform"}` |
| Word TF-IDF | K-Nearest Neighbors | GridSearchCV | 0.6235 | 0.5035 | 0.0149 | 1066 | 1 | 1058 | 8 | `{"n_neighbors": 7, "weights": "distance"}` |
| Word TF-IDF | Decision Tree | RandomizedSearchCV | 0.4960 | 0.5949 | 0.6667 | 405 | 662 | 202 | 864 | `{"criterion": "entropy", "max_depth": 50, "min_samples_leaf": 1}` |
| Word TF-IDF | Decision Tree | GridSearchCV | 0.5984 | 0.6249 | 0.6135 | 698 | 369 | 431 | 635 | `{"criterion": "gini", "max_depth": null, "min_samples_leaf": 1}` |
| Word TF-IDF | Random Forest | RandomizedSearchCV | 0.5887 | 0.7135 | 0.7064 | 787 | 280 | 331 | 735 | `{"max_depth": null, "max_features": "sqrt", "min_samples_leaf": 2}` |
| Word TF-IDF | Random Forest | GridSearchCV | 0.6242 | 0.7089 | 0.6856 | 835 | 232 | 389 | 677 | `{"max_depth": null, "max_features": "sqrt", "min_samples_leaf": 1}` |
| Word TF-IDF | SGD Classifier | RandomizedSearchCV | 0.6349 | 0.7412 | 0.7437 | 780 | 287 | 265 | 801 | `{"alpha": 0.001, "class_weight": null, "loss": "log_loss"}` |
| Word TF-IDF | SGD Classifier | GridSearchCV | 0.6258 | 0.7342 | 0.7412 | 754 | 313 | 254 | 812 | `{"alpha": 0.001, "class_weight": null, "loss": "hinge"}` |
| Character TF-IDF | Logistic Regression | RandomizedSearchCV | 0.6518 | 0.7304 | 0.7281 | 788 | 279 | 296 | 770 | `{"C": 0.1, "class_weight": null}` |
| Character TF-IDF | Logistic Regression | GridSearchCV | 0.6518 | 0.7304 | 0.7281 | 788 | 279 | 296 | 770 | `{"C": 0.1, "class_weight": null}` |
| Character TF-IDF | Linear SVC | RandomizedSearchCV | 0.6458 | 0.7543 | 0.7551 | 801 | 266 | 258 | 808 | `{"C": 0.1, "class_weight": null}` |
| Character TF-IDF | Linear SVC | GridSearchCV | 0.6458 | 0.7543 | 0.7551 | 801 | 266 | 258 | 808 | `{"C": 0.1, "class_weight": null}` |
| Character TF-IDF | RBF SVC | RandomizedSearchCV | 0.6578 | 0.6554 | 0.7030 | 528 | 539 | 196 | 870 | `{"C": 10.0, "class_weight": null, "gamma": "auto"}` |
| Character TF-IDF | RBF SVC | GridSearchCV | 0.6414 | 0.6109 | 0.7017 | 327 | 740 | 90 | 976 | `{"C": 0.1, "class_weight": null, "gamma": "scale"}` |
| Character TF-IDF | K-Nearest Neighbors | RandomizedSearchCV | 0.5940 | 0.6446 | 0.5634 | 886 | 181 | 577 | 489 | `{"n_neighbors": 3, "weights": "uniform"}` |
| Character TF-IDF | K-Nearest Neighbors | GridSearchCV | 0.6089 | 0.6915 | 0.6573 | 844 | 223 | 435 | 631 | `{"n_neighbors": 7, "weights": "distance"}` |
| Character TF-IDF | Decision Tree | RandomizedSearchCV | 0.5256 | 0.5823 | 0.5318 | 736 | 331 | 560 | 506 | `{"criterion": "entropy", "max_depth": 50, "min_samples_leaf": 1}` |
| Character TF-IDF | Decision Tree | GridSearchCV | 0.5354 | 0.5907 | 0.5849 | 645 | 422 | 451 | 615 | `{"criterion": "gini", "max_depth": null, "min_samples_leaf": 1}` |
| Character TF-IDF | Random Forest | RandomizedSearchCV | 0.5738 | 0.6953 | 0.6842 | 779 | 288 | 362 | 704 | `{"max_depth": 30, "max_features": "sqrt", "min_samples_leaf": 2}` |
| Character TF-IDF | Random Forest | GridSearchCV | 0.5988 | 0.6892 | 0.6780 | 772 | 295 | 368 | 698 | `{"max_depth": 30, "max_features": "sqrt", "min_samples_leaf": 1}` |
| Character TF-IDF | SGD Classifier | RandomizedSearchCV | 0.6459 | 0.7332 | 0.7340 | 779 | 288 | 281 | 785 | `{"alpha": 0.001, "class_weight": null, "loss": "log_loss"}` |
| Character TF-IDF | SGD Classifier | GridSearchCV | 0.6353 | 0.7421 | 0.7343 | 823 | 244 | 306 | 760 | `{"alpha": 0.001, "class_weight": null, "loss": "hinge"}` |
| Word2Vec mean | Logistic Regression | RandomizedSearchCV | 0.6692 | 0.7000 | 0.6990 | 750 | 317 | 323 | 743 | `{"C": 0.1, "class_weight": null}` |
| Word2Vec mean | Logistic Regression | GridSearchCV | 0.6692 | 0.7000 | 0.6990 | 750 | 317 | 323 | 743 | `{"C": 0.1, "class_weight": null}` |
| Word2Vec mean | Linear SVC | RandomizedSearchCV | 0.6590 | 0.7000 | 0.6987 | 751 | 316 | 324 | 742 | `{"C": 0.1, "class_weight": null}` |
| Word2Vec mean | Linear SVC | GridSearchCV | 0.6590 | 0.7000 | 0.6987 | 751 | 316 | 324 | 742 | `{"C": 0.1, "class_weight": null}` |
| Word2Vec mean | RBF SVC | RandomizedSearchCV | 0.6315 | 0.6362 | 0.6381 | 673 | 394 | 382 | 684 | `{"C": 10.0, "class_weight": "balanced", "gamma": "scale"}` |
| Word2Vec mean | RBF SVC | GridSearchCV | 0.6315 | 0.6362 | 0.6381 | 673 | 394 | 382 | 684 | `{"C": 10.0, "class_weight": null, "gamma": "scale"}` |
| Word2Vec mean | K-Nearest Neighbors | RandomizedSearchCV | 0.5823 | 0.5992 | 0.5823 | 682 | 385 | 470 | 596 | `{"n_neighbors": 3, "weights": "uniform"}` |
| Word2Vec mean | K-Nearest Neighbors | GridSearchCV | 0.6042 | 0.6259 | 0.6038 | 727 | 340 | 458 | 608 | `{"n_neighbors": 7, "weights": "distance"}` |
| Word2Vec mean | Decision Tree | RandomizedSearchCV | 0.5616 | 0.5720 | 0.5687 | 618 | 449 | 464 | 602 | `{"criterion": "entropy", "max_depth": 50, "min_samples_leaf": 1}` |
| Word2Vec mean | Decision Tree | GridSearchCV | 0.5659 | 0.5654 | 0.5596 | 617 | 450 | 477 | 589 | `{"criterion": "gini", "max_depth": null, "min_samples_leaf": 1}` |
| Word2Vec mean | Random Forest | RandomizedSearchCV | 0.6417 | 0.6774 | 0.6607 | 775 | 292 | 396 | 670 | `{"max_depth": null, "max_features": "sqrt", "min_samples_leaf": 2}` |
| Word2Vec mean | Random Forest | GridSearchCV | 0.6292 | 0.6559 | 0.6374 | 754 | 313 | 421 | 645 | `{"max_depth": null, "max_features": "sqrt", "min_samples_leaf": 1}` |
| Word2Vec mean | SGD Classifier | RandomizedSearchCV | 0.6597 | 0.6873 | 0.6852 | 740 | 327 | 340 | 726 | `{"alpha": 0.001, "class_weight": null, "loss": "log_loss"}` |
| Word2Vec mean | SGD Classifier | GridSearchCV | 0.6214 | 0.6198 | 0.6162 | 671 | 396 | 415 | 651 | `{"alpha": 1e-05, "class_weight": null, "loss": "hinge"}` |
| Doc2Vec | Logistic Regression | RandomizedSearchCV | 0.5543 | 0.6357 | 0.6473 | 643 | 424 | 353 | 713 | `{"C": 0.1, "class_weight": null}` |
| Doc2Vec | Logistic Regression | GridSearchCV | 0.5543 | 0.6357 | 0.6473 | 643 | 424 | 353 | 713 | `{"C": 0.1, "class_weight": null}` |
| Doc2Vec | Linear SVC | RandomizedSearchCV | 0.5427 | 0.6357 | 0.6470 | 644 | 423 | 354 | 712 | `{"C": 0.1, "class_weight": null}` |
| Doc2Vec | Linear SVC | GridSearchCV | 0.5437 | 0.6357 | 0.6470 | 644 | 423 | 354 | 712 | `{"C": 10.0, "class_weight": null}` |
| Doc2Vec | RBF SVC | RandomizedSearchCV | 0.5480 | 0.5607 | 0.5173 | 694 | 373 | 564 | 502 | `{"C": 10.0, "class_weight": "balanced", "gamma": "scale"}` |
| Doc2Vec | RBF SVC | GridSearchCV | 0.5686 | 0.5331 | 0.4113 | 789 | 278 | 718 | 348 | `{"C": 0.1, "class_weight": null, "gamma": "scale"}` |
| Doc2Vec | K-Nearest Neighbors | RandomizedSearchCV | 0.5175 | 0.5762 | 0.5654 | 641 | 426 | 478 | 588 | `{"n_neighbors": 3, "weights": "uniform"}` |
| Doc2Vec | K-Nearest Neighbors | GridSearchCV | 0.5175 | 0.5762 | 0.5654 | 641 | 426 | 478 | 588 | `{"n_neighbors": 3, "weights": "distance"}` |
| Doc2Vec | Decision Tree | RandomizedSearchCV | 0.5101 | 0.5401 | 0.5286 | 602 | 465 | 516 | 550 | `{"criterion": "entropy", "max_depth": 50, "min_samples_leaf": 1}` |
| Doc2Vec | Decision Tree | GridSearchCV | 0.5106 | 0.4984 | 0.5128 | 500 | 567 | 503 | 563 | `{"criterion": "gini", "max_depth": null, "min_samples_leaf": 1}` |
| Doc2Vec | Random Forest | RandomizedSearchCV | 0.5268 | 0.5874 | 0.5956 | 605 | 462 | 418 | 648 | `{"max_depth": null, "max_features": "sqrt", "min_samples_leaf": 2}` |
| Doc2Vec | Random Forest | GridSearchCV | 0.5256 | 0.5438 | 0.5284 | 615 | 452 | 521 | 545 | `{"max_depth": null, "max_features": "sqrt", "min_samples_leaf": 1}` |
| Doc2Vec | SGD Classifier | RandomizedSearchCV | 0.5588 | 0.6212 | 0.6242 | 654 | 413 | 395 | 671 | `{"alpha": 0.001, "class_weight": "balanced", "loss": "hinge"}` |
| Doc2Vec | SGD Classifier | GridSearchCV | 0.5588 | 0.6254 | 0.6292 | 656 | 411 | 388 | 678 | `{"alpha": 0.001, "class_weight": null, "loss": "hinge"}` |
| GloVe mean (pretrained) | Logistic Regression | RandomizedSearchCV | 0.6813 | 0.7154 | 0.7157 | 762 | 305 | 302 | 764 | `{"C": 0.1, "class_weight": null}` |
| GloVe mean (pretrained) | Logistic Regression | GridSearchCV | 0.6813 | 0.7154 | 0.7157 | 762 | 305 | 302 | 764 | `{"C": 0.1, "class_weight": null}` |
| GloVe mean (pretrained) | Linear SVC | RandomizedSearchCV | 0.6822 | 0.7168 | 0.7167 | 765 | 302 | 302 | 764 | `{"C": 0.1, "class_weight": null}` |
| GloVe mean (pretrained) | Linear SVC | GridSearchCV | 0.6843 | 0.7168 | 0.7167 | 765 | 302 | 302 | 764 | `{"C": 10.0, "class_weight": null}` |
| GloVe mean (pretrained) | RBF SVC | RandomizedSearchCV | 0.6684 | 0.6676 | 0.6638 | 724 | 343 | 366 | 700 | `{"C": 10.0, "class_weight": "balanced", "gamma": "scale"}` |
| GloVe mean (pretrained) | RBF SVC | GridSearchCV | 0.6684 | 0.6676 | 0.6638 | 724 | 343 | 366 | 700 | `{"C": 10.0, "class_weight": null, "gamma": "scale"}` |
| GloVe mean (pretrained) | K-Nearest Neighbors | RandomizedSearchCV | 0.5895 | 0.6399 | 0.6257 | 723 | 344 | 424 | 642 | `{"n_neighbors": 3, "weights": "uniform"}` |
| GloVe mean (pretrained) | K-Nearest Neighbors | GridSearchCV | 0.6128 | 0.6606 | 0.6409 | 763 | 304 | 420 | 646 | `{"n_neighbors": 7, "weights": "distance"}` |
| GloVe mean (pretrained) | Decision Tree | RandomizedSearchCV | 0.5856 | 0.5893 | 0.5982 | 605 | 462 | 414 | 652 | `{"criterion": "entropy", "max_depth": 50, "min_samples_leaf": 1}` |
| GloVe mean (pretrained) | Decision Tree | GridSearchCV | 0.5527 | 0.5752 | 0.5817 | 597 | 470 | 436 | 630 | `{"criterion": "gini", "max_depth": null, "min_samples_leaf": 1}` |
| GloVe mean (pretrained) | Random Forest | RandomizedSearchCV | 0.6504 | 0.6995 | 0.6932 | 768 | 299 | 342 | 724 | `{"max_depth": null, "max_features": "sqrt", "min_samples_leaf": 2}` |
| GloVe mean (pretrained) | Random Forest | GridSearchCV | 0.6321 | 0.6821 | 0.6718 | 761 | 306 | 372 | 694 | `{"max_depth": null, "max_features": "sqrt", "min_samples_leaf": 1}` |
| GloVe mean (pretrained) | SGD Classifier | RandomizedSearchCV | 0.6545 | 0.7131 | 0.7088 | 776 | 291 | 321 | 745 | `{"alpha": 0.001, "class_weight": null, "loss": "log_loss"}` |
| GloVe mean (pretrained) | SGD Classifier | GridSearchCV | 0.6538 | 0.7131 | 0.7102 | 771 | 296 | 316 | 750 | `{"alpha": 0.001, "class_weight": null, "loss": "hinge"}` |
| GloVe mean (pretrained) | Linear SVC | Optuna (30 prób) | 0.6822 | 0.7168 | 0.7167 | 765 | 302 | 302 | 764 | `{"C": 0.1, "class_weight": "balanced"}` |

### Porównanie najlepszych konfiguracji

| Metoda strojenia | Reprezentacja | Klasyfikator | CV F1 | Accuracy test | F1 test |
|---|---|---|---:|---:|---:|
| Random Search | GloVe mean (pretrained) | Linear SVC | 0.6822 | 0.7168 | 0.7167 |
| Grid Search | GloVe mean (pretrained) | Linear SVC | 0.6843 | 0.7168 | 0.7167 |
| Optuna | GloVe mean (pretrained) | Linear SVC | 0.6822 | 0.7168 | 0.7167 |

### Wykresy i macierze pomyłek

- `../wykresy/f1_wszystkie_polaczenia.png` — testowy F1 dla 42 par, osobno po Random Search i Grid Search.
- `../wykresy/porownanie_metod_strojenia.png` — testowe wyniki najlepszych konfiguracji wybranych na podstawie CV.
- `../wykresy/macierze_pomylek/` — osobna macierz pomyłek dla każdego z 42 połączeń (wariant o wyższym CV F1 spośród Random/Grid) oraz macierz modelu wybranego przez Optunę.

## 8. Wnioski i ograniczenia

Najlepsza konfiguracja Random Search według CV: GloVe mean (pretrained) + Linear SVC (CV F1=0.6822; test F1=0.7167). Najlepszy Grid Search: GloVe mean (pretrained) + Linear SVC (CV F1=0.6843; test F1=0.7167). Optuna wybrała GloVe mean (pretrained) + Linear SVC (CV F1=0.6822; test F1=0.7167).

Wnioski o przewadze metod odnoszą się do zastosowanego budżetu i ograniczonych siatek, nie do pełnej przestrzeni hiperparametrów. Uśrednianie embeddingów redukuje informację o kolejności słów; Word2Vec/Doc2Vec uczone są na stosunkowo małym korpusie; gotowe GloVe wnosi wiedzę zewnętrzną i ma ograniczone pokrycie słów. Wyniki dotyczą wyłącznie angielskich krótkich recenzji z Cornell Sentence Polarity i jednego stratyfikowanego podziału testowego.

Cały eksperyment trwał 400.9 min. Powtórzenie zapewnia stałe ziarno losowości; szczegóły wszystkich konfiguracji, wyniki i statystyki znajdują się w katalogu `wyniki/`.

## 9. Uruchomienie

```powershell
python -m pip install -r Lab4/requirements.txt
python Lab4/prepare_data.py
python Lab4/preprocess_data.py
python Lab4/run_experiments.py
python Lab4/generate_plots.py
python Lab4/generate_report.py
```

## Literatura i źródła

1. Pang, B. i Lee, L. (2005), Cornell Sentence Polarity v1.0, https://www.cs.cornell.edu/people/pabo/movie-review-data/.
2. NLTK, `sentence_polarity`, WordNet i POS tagger, https://www.nltk.org/.
3. Pennington, J., Socher, R. i Manning, C. (2014), GloVe: Global Vectors for Word Representation, EMNLP.
4. Scikit-learn, dokumentacja `model_selection`, `feature_extraction` i klasyfikatorów, https://scikit-learn.org/.
5. Optuna, dokumentacja optymalizacji hiperparametrów, https://optuna.org/.

## Środowisko

Python 3.13.2; NLTK 3.9.1; scikit-learn 1.6.1; Gensim 4.4.0; Optuna 5.0.0; Matplotlib 3.10.1.
