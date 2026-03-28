# SuperAuto Global Wholesale Sales Dashboard

Demonstracyjny dashboard Power BI przedstawiający globalne dane sprzedaży hurtowej fikcyjnej marki samochodów **SuperAuto**. Dane są w pełni syntetyczne i służą wyłącznie celom prezentacyjnym.

---

## Wymagania

- **Python 3.10+** (tylko biblioteki standardowe — żadnych instalacji pip)
- **Power BI Desktop** (najnowsza wersja) z włączonymi funkcjami:
  - Developer Mode / Power BI Project (*.pbip)
  - Store semantic model using TMDL format

---

## Szybki start

```bash
# 1. Wygeneruj dane syntetyczne
python scripts/generate_data.py

# 2. Zwaliduj dane (opcjonalnie)
python scripts/validate_data.py

# 3. Otwórz projekt w Power BI Desktop
#    (patrz sekcja "Jak otworzyć w Power BI Desktop" poniżej)
```

---

## Struktura plików

```
superauto-dashboard/
├── README.md
├── CLAUDE.md                              # instrukcje projektu
├── SuperAuto.pbip                         # plik główny projektu
│
├── scripts/
│   ├── generate_data.py                   # generowanie danych (uruchom jako pierwsze)
│   └── validate_data.py                   # walidacja spójności danych
│
├── data/                                  # generowane automatycznie
│   ├── dim_date.csv                       # wymiar dat (731 wierszy, 2024–2025)
│   ├── dim_dealer.csv                     # wymiar dealerów (100 dealerów, 5 regionów)
│   ├── dim_model.csv                      # wymiar modeli samochodów (7 modeli)
│   └── fact_sales.csv                     # fakty sprzedaży (~31 000 transakcji)
│
├── SuperAuto.Report/
│   ├── definition.pbir                    # definicja raportu (wskazanie na semantic model)
│   └── report.json                        # szkielet stron raportu
│
└── SuperAuto.SemanticModel/
    ├── definition.pbism                   # definicja semantic modelu
    └── definition/
        ├── database.tmdl
        ├── model.tmdl
        ├── relationships.tmdl             # 3 relacje: fact → dim
        ├── expressions.tmdl              # parametr ścieżki
        └── tables/
            ├── dim_date.tmdl
            ├── dim_dealer.tmdl
            ├── dim_model.tmdl
            └── fact_sales.tmdl            # kolumny + 11 miar DAX
```

---

## Jak otworzyć w Power BI Desktop

1. **Włącz Developer Mode:**
   - `File → Options and settings → Options → Preview features`
   - Zaznacz: **Power BI Project (.pbip) support**

2. **Włącz format TMDL:**
   - W tym samym miejscu zaznacz: **Store semantic model in TMDL format**

3. **Otwórz projekt:**
   - `File → Open → Browse` → wybierz plik `SuperAuto.pbip`

4. **Zaktualizuj ścieżki do plików CSV:**
   - W Power Query Editor (`Home → Transform data`) otwórz każdą tabelę
   - Zmień placeholder `<SCIEZKA_DO_DANYCH>` na pełną ścieżkę do katalogu projektu
   - Przykład (Windows): `C:/Users/Jan/projekty/PowerBI_demo`

5. **Odśwież dane:**
   - `Home → Refresh`

---

## Model danych

Schemat gwiazdy (star schema):

```
dim_date ──────┐
dim_dealer ────┼──── fact_sales
dim_model ─────┘
```

### dim_date
Każdy dzień kalendarzowy w zakresie 2024-01-01 do 2025-12-31 (731 wierszy).
Kolumny: `date`, `year`, `quarter`, `month`, `month_name`, `year_month`, `day_of_week`, `is_weekend`

### dim_dealer
100 dealerów hurtowych w 5 regionach świata.
Kolumny: `dealer_id`, `dealer_name`, `country`, `region`, `city`, `dealer_tier`

Regiony: Europe (35), North America (25), Asia-Pacific (18), South America (12), MEA (10)
Tiery: Premium (~20%), Standard (~50%), Local (~30%)

### dim_model
7 modeli samochodów SuperAuto.
Kolumny: `model_id`, `model_name`, `segment`, `fuel_type`, `vehicle_class`

| model_id | Nazwa             | Segment     | Napęd    | Klasa      |
|----------|-------------------|-------------|----------|------------|
| M01      | SuperAuto City    | Compact     | Petrol   | Economy    |
| M02      | SuperAuto Urban   | Hatchback   | Petrol   | Economy    |
| M03      | SuperAuto Family  | Sedan       | Hybrid   | Mid-Range  |
| M04      | SuperAuto Tourer  | SUV         | Diesel   | Mid-Range  |
| M05      | SuperAuto Cargo   | Van         | Diesel   | Commercial |
| M06      | SuperAuto Electra | EV          | Electric | Premium    |
| M07      | SuperAuto Falcon  | Premium SUV | Hybrid   | Premium    |

### fact_sales
~31 000 transakcji hurtowych (dni robocze, 40–80 transakcji dziennie).
Klucze obce: `date`, `dealer_id`, `model_id`

---

## Miary DAX

Wszystkie miary zdefiniowane w tabeli `fact_sales`:

| Miara             | Opis                                        | Format    |
|-------------------|---------------------------------------------|-----------|
| Net Revenue       | Suma przychodów po rabatach                 | € #,##0   |
| Gross Revenue     | Suma przychodów przed rabatami              | € #,##0   |
| Units Sold        | Łączna liczba sprzedanych sztuk             | #,##0     |
| Profit            | Łączny zysk (net_revenue - total_cost)      | € #,##0   |
| Margin %          | Marża = Profit / Net Revenue                | 0.0%      |
| Avg Selling Price | Średnia cena sprzedaży na sztukę            | € #,##0   |
| Avg Discount %    | Średni procent rabatu                       | 0.0%      |
| Total Cost        | Łączny koszt własny                         | € #,##0   |
| Cost per Unit     | Koszt na sztukę                             | € #,##0   |
| Revenue YoY %     | Wzrost przychodu rok do roku                | 0.0%      |
| Transaction Count | Liczba transakcji                           | #,##0     |

---

## Strony raportu

### 1. Executive Overview
Widok zarządczy — przegląd całościowych wyników sprzedaży.
Planowane wizualizacje: karty KPI, wykres liniowy trendu, mapa geograficzna, wykresy słupkowe.

### 2. Product & Dealer Analysis
Analiza produktowa i dealerska — porównanie modeli i dealerów.
Planowane wizualizacje: macierz (matrix), wykres punktowy, drzewo dekompozycji.

### 3. Interactive Demo
Interaktywne narzędzia analityczne.
Planowane wizualizacje: parametry pól (field parameters), zakładki (bookmarks), analiza what-if.

---

## Kluczowe insighty dostępne w danych

- **Europa** ma najwyższy przychód, ale niższą marżę (wyższe rabaty)
- **North America** — mniejszy wolumen, lepszy profit mix
- **SuperAuto Electra (EV)** rośnie dynamicznie w 2025, ale ma najniższą marżę
- **SuperAuto Falcon** generuje najwyższy profit % (najlepsza marża)
- **SuperAuto Tourer (SUV)** — największy przychód ogółem
- Dealerzy **Premium** mają wyższy revenue, ale słabszy margin %
- **APAC** wyraźnie przyspiesza w 2025 roku
