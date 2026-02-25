"""
Unit tests for the EU Car Search Agent.
"""

import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Ensure the project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import EU_COUNTRY_CODES, EU_COUNTRY_CODES_STR
from car_search_agent import CarListing, CarSearchAgent, _print_results, main


SAMPLE_HTML = """
<html><body>
  <article data-testid="regular-ad">
    <h2>Toyota Yaris 1.5 Hybrid</h2>
    <span data-testid="price-label">€ 8,500</span>
    <span data-testid="detail-0">45,000 km</span>
    <span data-testid="detail-1">2019</span>
    <span data-testid="location-with-link">Berlin, Germany</span>
    <a href="/offers/toyota/yaris/12345">View</a>
  </article>
  <article data-testid="regular-ad">
    <h2>Volkswagen Golf 2.0 TDI</h2>
    <span data-testid="price-label">€ 12,900</span>
    <span data-testid="detail-0">80,000 km</span>
    <span data-testid="detail-1">2018</span>
    <span data-testid="location-with-link">Paris, France</span>
    <a href="/offers/volkswagen/golf/67890">View</a>
  </article>
</body></html>
"""


class TestConfig(unittest.TestCase):
    def test_uk_not_in_eu_country_codes(self):
        """The UK must not appear in the EU country codes mapping."""
        country_names = [name.lower() for name in EU_COUNTRY_CODES.keys()]
        self.assertNotIn("united kingdom", country_names)
        self.assertNotIn("uk", country_names)

    def test_uk_code_not_in_country_codes_str(self):
        """AutoScout24 UK country code 'GB' / 'UK' must not be in the query string."""
        codes = EU_COUNTRY_CODES_STR.split(",")
        self.assertNotIn("GB", codes)
        self.assertNotIn("UK", codes)

    def test_eu_contains_key_member_states(self):
        """Germany, France, Italy, and Spain must be present."""
        self.assertIn("Germany", EU_COUNTRY_CODES)
        self.assertIn("France", EU_COUNTRY_CODES)
        self.assertIn("Italy", EU_COUNTRY_CODES)
        self.assertIn("Spain", EU_COUNTRY_CODES)

    def test_eu_country_codes_str_is_comma_separated(self):
        """EU_COUNTRY_CODES_STR must be a non-empty comma-separated string."""
        self.assertGreater(len(EU_COUNTRY_CODES_STR), 0)
        self.assertIn(",", EU_COUNTRY_CODES_STR)


class TestCarListing(unittest.TestCase):
    def _make_listing(self):
        return CarListing(
            title="Toyota Yaris",
            price="€ 8,500",
            mileage="45,000 km",
            year="2019",
            location="Berlin, Germany",
            url="https://www.autoscout24.com/offers/toyota/yaris/12345",
        )

    def test_repr(self):
        listing = self._make_listing()
        self.assertIn("Toyota Yaris", repr(listing))
        self.assertIn("€ 8,500", repr(listing))

    def test_to_dict(self):
        listing = self._make_listing()
        d = listing.to_dict()
        self.assertEqual(d["title"], "Toyota Yaris")
        self.assertEqual(d["price"], "€ 8,500")
        self.assertEqual(d["year"], "2019")
        self.assertIn("url", d)


class TestCarSearchAgentBuildParams(unittest.TestCase):
    def setUp(self):
        self.agent = CarSearchAgent()

    def test_eu_country_codes_always_present(self):
        """All searches must target EU countries only."""
        params = self.agent._build_params()
        self.assertEqual(params["cy"], EU_COUNTRY_CODES_STR)

    def test_uk_not_in_country_param(self):
        """UK country codes must not appear in the search parameters."""
        params = self.agent._build_params()
        codes = params["cy"].split(",")
        self.assertNotIn("GB", codes)
        self.assertNotIn("UK", codes)

    def test_optional_filters_applied(self):
        params = self.agent._build_params(
            make="Toyota",
            model="Yaris",
            max_price=10000,
            min_price=3000,
            max_mileage=50000,
            min_year=2015,
            max_year=2022,
        )
        self.assertIn("mmvmk0", params)
        self.assertIn("mmvmd0", params)
        self.assertEqual(params["priceto"], 10000)
        self.assertEqual(params["pricefrom"], 3000)
        self.assertEqual(params["kmto"], 50000)
        self.assertEqual(params["fregfrom"], 2015)
        self.assertEqual(params["fregto"], 2022)

    def test_sort_by_price_ascending(self):
        """Results should be sorted by price ascending to surface best deals."""
        params = self.agent._build_params()
        self.assertEqual(params["sort"], "price")
        self.assertEqual(params["desc"], 0)

    def test_no_optional_params_leaves_keys_absent(self):
        params = self.agent._build_params()
        for key in ("priceto", "pricefrom", "kmto", "fregfrom", "fregto",
                    "mmvmk0", "mmvmd0"):
            self.assertNotIn(key, params)


class TestCarSearchAgentParseListings(unittest.TestCase):
    def setUp(self):
        self.agent = CarSearchAgent()

    def test_parse_two_listings(self):
        listings = self.agent._parse_listings(SAMPLE_HTML, "https://www.autoscout24.com/lst")
        self.assertEqual(len(listings), 2)

    def test_first_listing_fields(self):
        listings = self.agent._parse_listings(SAMPLE_HTML, "https://www.autoscout24.com/lst")
        first = listings[0]
        self.assertIn("Toyota", first.title)
        self.assertIn("8,500", first.price)

    def test_listing_url_is_absolute(self):
        listings = self.agent._parse_listings(SAMPLE_HTML, "https://www.autoscout24.com/lst")
        for listing in listings:
            self.assertTrue(listing.url.startswith("http"))

    def test_empty_html_returns_no_listings(self):
        listings = self.agent._parse_listings("<html><body></body></html>", "")
        self.assertEqual(listings, [])


class TestCarSearchAgentSearch(unittest.TestCase):
    def setUp(self):
        self.agent = CarSearchAgent()

    def _mock_response(self, html):
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_resp.url = "https://www.autoscout24.com/lst?page=1"
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    @patch("car_search_agent.time.sleep")
    def test_search_returns_listings(self, _mock_sleep):
        self.agent._session.get = MagicMock(
            side_effect=[
                self._mock_response(SAMPLE_HTML),
                self._mock_response("<html><body></body></html>"),  # empty page → stop
            ]
        )
        results = self.agent.search(make="Toyota", max_results=10)
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)

    @patch("car_search_agent.time.sleep")
    def test_search_respects_max_results(self, _mock_sleep):
        self.agent._session.get = MagicMock(
            return_value=self._mock_response(SAMPLE_HTML)
        )
        results = self.agent.search(max_results=1)
        self.assertEqual(len(results), 1)

    @patch("car_search_agent.time.sleep")
    def test_search_returns_empty_on_request_error(self, _mock_sleep):
        import requests as req
        self.agent._session.get = MagicMock(
            side_effect=req.RequestException("network error")
        )
        results = self.agent.search()
        self.assertEqual(results, [])


class TestPrintResults(unittest.TestCase):
    def test_prints_no_listings_message(self):
        import io
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            _print_results([])
            self.assertIn("No listings found", mock_out.getvalue())

    def test_prints_listings(self):
        import io
        listing = CarListing("BMW 3", "€10,000", "50,000 km", "2020", "Munich, DE",
                             "https://example.com")
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            _print_results([listing])
            output = mock_out.getvalue()
            self.assertIn("BMW 3", output)
            self.assertIn("€10,000", output)


class TestCLI(unittest.TestCase):
    @patch("car_search_agent.CarSearchAgent.search", return_value=[])
    def test_main_runs_without_error(self, _mock_search):
        """CLI should run without raising exceptions."""
        main([])

    @patch("car_search_agent.CarSearchAgent.search", return_value=[])
    def test_main_passes_filters(self, mock_search):
        main([
            "--make", "Toyota",
            "--model", "Yaris",
            "--max-price", "10000",
            "--min-price", "2000",
            "--max-mileage", "100000",
            "--min-year", "2015",
            "--max-year", "2022",
            "--results", "5",
        ])
        mock_search.assert_called_once_with(
            make="Toyota",
            model="Yaris",
            max_price=10000,
            min_price=2000,
            max_mileage=100000,
            min_year=2015,
            max_year=2022,
            max_results=5,
        )


if __name__ == "__main__":
    unittest.main()
