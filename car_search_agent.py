"""
EU Car Search Agent
-------------------
Searches AutoScout24 for the best car deals across EU member states.
The United Kingdom is explicitly excluded from all searches.

Usage (CLI):
    python car_search_agent.py [--make MAKE] [--model MODEL]
                               [--max-price MAX_PRICE] [--max-mileage MAX_MILEAGE]
                               [--max-year MAX_YEAR] [--min-year MIN_YEAR]
                               [--results N]

Example:
    python car_search_agent.py --make Toyota --model Yaris --max-price 10000 --results 10
"""

import argparse
import sys
import time

import requests
from bs4 import BeautifulSoup

from config import (
    AUTOSCOUT24_SEARCH_URL,
    DEFAULT_DESC,
    DEFAULT_MAX_RESULTS,
    DEFAULT_SORT,
    EU_COUNTRY_CODES_STR,
    REQUEST_HEADERS,
)


class CarListing:
    """Represents a single car listing scraped from AutoScout24."""

    def __init__(self, title, price, mileage, year, location, url):
        self.title = title
        self.price = price
        self.mileage = mileage
        self.year = year
        self.location = location
        self.url = url

    def __repr__(self):
        return (
            f"CarListing(title={self.title!r}, price={self.price!r}, "
            f"mileage={self.mileage!r}, year={self.year!r}, "
            f"location={self.location!r})"
        )

    def to_dict(self):
        return {
            "title": self.title,
            "price": self.price,
            "mileage": self.mileage,
            "year": self.year,
            "location": self.location,
            "url": self.url,
        }


class CarSearchAgent:
    """
    Agent that searches AutoScout24 for best car deals in the EU market.
    The UK is excluded by only passing EU member-state country codes.
    """

    BASE_URL = AUTOSCOUT24_SEARCH_URL

    def __init__(self, session=None):
        self._session = session or requests.Session()
        self._session.headers.update(REQUEST_HEADERS)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def search(
        self,
        make=None,
        model=None,
        max_price=None,
        min_price=None,
        max_mileage=None,
        min_year=None,
        max_year=None,
        max_results=DEFAULT_MAX_RESULTS,
    ):
        """
        Search for car listings in EU countries (UK excluded).

        Parameters
        ----------
        make : str, optional
            Car manufacturer (e.g. "Toyota", "BMW").
        model : str, optional
            Car model (e.g. "Yaris", "3 Series").
        max_price : int, optional
            Maximum price in EUR.
        min_price : int, optional
            Minimum price in EUR.
        max_mileage : int, optional
            Maximum mileage in km.
        min_year : int, optional
            Minimum registration year.
        max_year : int, optional
            Maximum registration year.
        max_results : int
            Maximum number of listings to return (default: 20).

        Returns
        -------
        list[CarListing]
            Listings sorted by price (ascending) so the best deals appear first.
        """
        params = self._build_params(
            make=make,
            model=model,
            max_price=max_price,
            min_price=min_price,
            max_mileage=max_mileage,
            min_year=min_year,
            max_year=max_year,
        )

        listings = []
        page = 1
        while len(listings) < max_results:
            params["page"] = page
            page_listings = self._fetch_page(params)
            if not page_listings:
                break
            listings.extend(page_listings)
            page += 1
            time.sleep(1)  # be polite to the server

        return listings[:max_results]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_params(
        self,
        make=None,
        model=None,
        max_price=None,
        min_price=None,
        max_mileage=None,
        min_year=None,
        max_year=None,
    ):
        """Build the query-parameter dict for AutoScout24."""
        params = {
            "cy": EU_COUNTRY_CODES_STR,  # EU countries only – UK excluded
            "atype": "C",               # cars
            "sort": DEFAULT_SORT,
            "desc": DEFAULT_DESC,
        }
        if make:
            params["mmvmk0"] = make.lower()
        if model:
            params["mmvmd0"] = model.lower()
        if max_price is not None:
            params["priceto"] = int(max_price)
        if min_price is not None:
            params["pricefrom"] = int(min_price)
        if max_mileage is not None:
            params["kmto"] = int(max_mileage)
        if min_year is not None:
            params["fregfrom"] = int(min_year)
        if max_year is not None:
            params["fregto"] = int(max_year)
        return params

    def _fetch_page(self, params):
        """Fetch one page of results and return a list of CarListing objects."""
        try:
            response = self._session.get(
                self.BASE_URL, params=params, timeout=15
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"[WARNING] Request failed: {exc}", file=sys.stderr)
            return []

        return self._parse_listings(response.text, response.url)

    def _parse_listings(self, html, page_url):
        """Parse the AutoScout24 results page and extract listings."""
        soup = BeautifulSoup(html, "html.parser")
        listings = []

        # AutoScout24 article cards have data-testid="regular-ad" or
        # class patterns that include "ListItem".  We target article tags.
        articles = soup.find_all("article", {"data-testid": "regular-ad"})
        if not articles:
            # Fallback: look for any article with class containing "cldt-summary"
            articles = soup.find_all("article", class_=lambda c: c and "cldt" in c)

        for article in articles:
            listing = self._extract_listing(article, page_url)
            if listing:
                listings.append(listing)

        return listings

    def _extract_listing(self, article, page_url):
        """Extract a CarListing from a single article element."""
        try:
            # Title / car name
            title_tag = (
                article.find("h2")
                or article.find("a", {"data-testid": "listing-title"})
            )
            title = title_tag.get_text(strip=True) if title_tag else "N/A"

            # Price
            price_tag = article.find(attrs={"data-testid": "price-label"})
            if not price_tag:
                price_tag = article.find(class_=lambda c: c and "price" in c.lower())
            price = price_tag.get_text(strip=True) if price_tag else "N/A"

            # Mileage & Year (usually in a details list)
            details = article.find_all("span", {"data-testid": lambda v: v and "detail" in v})
            mileage = details[0].get_text(strip=True) if len(details) > 0 else "N/A"
            year_text = details[1].get_text(strip=True) if len(details) > 1 else "N/A"

            # Location
            location_tag = article.find(attrs={"data-testid": "location-with-link"})
            if not location_tag:
                location_tag = article.find(class_=lambda c: c and "location" in c.lower())
            location = location_tag.get_text(strip=True) if location_tag else "N/A"

            # Listing URL
            link_tag = article.find("a", href=True)
            if link_tag:
                href = link_tag["href"]
                url = (
                    href
                    if href.startswith("http")
                    else f"https://www.autoscout24.com{href}"
                )
            else:
                url = page_url

            return CarListing(
                title=title,
                price=price,
                mileage=mileage,
                year=year_text,
                location=location,
                url=url,
            )
        except Exception as exc:  # pragma: no cover – defensive catch
            print(f"[WARNING] Could not parse listing: {exc}", file=sys.stderr)
            return None


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def _print_results(listings):
    if not listings:
        print("No listings found matching your criteria.")
        return

    print(f"\nFound {len(listings)} listing(s) – sorted by price (best deals first):\n")
    separator = "-" * 70
    for i, listing in enumerate(listings, start=1):
        print(separator)
        print(f"  #{i:>2}  {listing.title}")
        print(f"       Price:    {listing.price}")
        print(f"       Year:     {listing.year}")
        print(f"       Mileage:  {listing.mileage}")
        print(f"       Location: {listing.location}")
        print(f"       URL:      {listing.url}")
    print(separator)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Search for best car deals in the EU market (UK excluded)."
    )
    parser.add_argument("--make", help="Car manufacturer (e.g. Toyota)")
    parser.add_argument("--model", help="Car model (e.g. Yaris)")
    parser.add_argument("--max-price", type=int, help="Maximum price in EUR")
    parser.add_argument("--min-price", type=int, help="Minimum price in EUR")
    parser.add_argument("--max-mileage", type=int, help="Maximum mileage in km")
    parser.add_argument("--min-year", type=int, help="Earliest registration year")
    parser.add_argument("--max-year", type=int, help="Latest registration year")
    parser.add_argument(
        "--results",
        type=int,
        default=DEFAULT_MAX_RESULTS,
        help=f"Number of results to return (default: {DEFAULT_MAX_RESULTS})",
    )

    args = parser.parse_args(argv)

    agent = CarSearchAgent()
    listings = agent.search(
        make=args.make,
        model=args.model,
        max_price=args.max_price,
        min_price=args.min_price,
        max_mileage=args.max_mileage,
        min_year=args.min_year,
        max_year=args.max_year,
        max_results=args.results,
    )
    _print_results(listings)


if __name__ == "__main__":
    main()
