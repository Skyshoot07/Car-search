# Car-search

A Python agent that searches [AutoScout24](https://www.autoscout24.com) for the best car deals across the **EU market**. The **United Kingdom is explicitly excluded** from all searches.

## Features

- Searches across all EU member states (UK excluded)
- Filters by make, model, price range, mileage, and registration year
- Results sorted by price ascending so the cheapest/best deals appear first
- Polite multi-page scraping with a 1-second delay between pages
- Simple CLI interface

## Requirements

- Python 3.8+
- [pip](https://pip.pypa.io/)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python car_search_agent.py [OPTIONS]
```

### Options

| Option | Description |
|---|---|
| `--make MAKE` | Car manufacturer (e.g. `Toyota`) |
| `--model MODEL` | Car model (e.g. `Yaris`) |
| `--max-price N` | Maximum price in EUR |
| `--min-price N` | Minimum price in EUR |
| `--max-mileage N` | Maximum mileage in km |
| `--min-year N` | Earliest registration year |
| `--max-year N` | Latest registration year |
| `--results N` | Number of results to return (default: `20`) |

### Examples

```bash
# Find cheap Toyotas under €10 000 anywhere in the EU
python car_search_agent.py --make Toyota --max-price 10000

# Find a VW Golf, between 2015–2022, under 80 000 km
python car_search_agent.py --make Volkswagen --model Golf \
    --min-year 2015 --max-year 2022 --max-mileage 80000

# Top 5 cheapest BMWs across the EU
python car_search_agent.py --make BMW --results 5
```

## Running Tests

```bash
python -m pytest tests/ -v
```

## Project Structure

```
Car-search/
├── car_search_agent.py   # Main agent (scraping + CLI)
├── config.py             # EU country codes & site configuration
├── requirements.txt      # Python dependencies
├── tests/
│   └── test_car_search_agent.py
└── README.md
```

## Country Coverage

All **27 EU member states** are covered. The United Kingdom is intentionally omitted:

Austria · Belgium · Bulgaria · Croatia · Cyprus · Czech Republic · Denmark ·
Estonia · Finland · France · Germany · Greece · Hungary · Ireland · Italy ·
Latvia · Lithuania · Luxembourg · Malta · Netherlands · Poland · Portugal ·
Romania · Slovakia · Slovenia · Spain · Sweden
