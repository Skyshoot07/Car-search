"""
Configuration for the EU Car Search Agent.
EU countries are included; the UK is explicitly excluded.
"""

# AutoScout24 country codes for EU member states (UK excluded)
EU_COUNTRY_CODES = {
    "Austria": "A",
    "Belgium": "B",
    "Bulgaria": "BG",
    "Croatia": "HR",
    "Cyprus": "CY",
    "Czech Republic": "CZ",
    "Denmark": "DK",
    "Estonia": "EST",
    "Finland": "FIN",
    "France": "F",
    "Germany": "D",
    "Greece": "GR",
    "Hungary": "H",
    "Ireland": "IRL",
    "Italy": "I",
    "Latvia": "LV",
    "Lithuania": "LT",
    "Luxembourg": "L",
    "Malta": "M",
    "Netherlands": "NL",
    "Poland": "PL",
    "Portugal": "P",
    "Romania": "RO",
    "Slovakia": "SK",
    "Slovenia": "SLO",
    "Spain": "E",
    "Sweden": "S",
}

# Comma-separated string of all EU country codes used in AutoScout24 query
EU_COUNTRY_CODES_STR = ",".join(EU_COUNTRY_CODES.values())

# AutoScout24 base search URL
AUTOSCOUT24_SEARCH_URL = "https://www.autoscout24.com/lst"

# Default search parameters
DEFAULT_MAX_RESULTS = 20
DEFAULT_SORT = "price"  # sort by price ascending to surface cheapest/best deals
DEFAULT_DESC = 0        # ascending order

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
