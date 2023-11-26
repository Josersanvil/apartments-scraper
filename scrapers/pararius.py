from datetime import datetime
from functools import cached_property
import logging
from typing import TYPE_CHECKING, Any
import urllib

from bs4 import BeautifulSoup
from selenium import webdriver

if TYPE_CHECKING:
    from bs4.element import Tag


class ParariusScraper:
    SCRAPING_URL = (
        "https://www.pararius.com/apartments/{city}/0-1750/1-bedrooms/furnished/50m2"
    )

    def __init__(self, city: str) -> None:
        self.city = city
        self._url = self.SCRAPING_URL.format(city=city)
        self._latest_extraction = None
        self._logger = self._init_logger()

    @property
    def url(self) -> str:
        return self._url

    @property
    def latest_extraction(self) -> datetime:
        return self._latest_extraction

    @cached_property
    def base_url(self) -> str:
        scheme = urllib.parse.urlparse(self.SCRAPING_URL).scheme
        site = urllib.parse.urlparse(self.SCRAPING_URL).netloc
        return f"{scheme}://{site}"

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    def _init_logger(self) -> logging.Logger:
        """
        Initializes the logger.
        """
        logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        return logger

    def extract_info_from_listing(self, listing: "Tag") -> dict[str, Any]:
        """
        Extracts information from a singular listing.
        """
        title = listing.find(
            "a", class_="listing-search-item__link listing-search-item__link--title"
        ).text.strip()
        address = listing.find(
            "div", class_="listing-search-item__sub-title'"
        ).text.strip()
        price_text = listing.find(
            "div", class_="listing-search-item__price"
        ).text.strip()
        features_item = listing.find("div", class_="listing-search-item__features")
        surface_area = features_item.find(
            "li",
            class_="illustrated-features__item illustrated-features__item--surface-area",
        )
        n_rooms = features_item.find(
            "li",
            class_="illustrated-features__item illustrated-features__item--number-of-rooms",
        )
        interior_type = features_item.find(
            "li",
            class_="illustrated-features__item illustrated-features__item--interior",
        )
        listing_info_item = listing.find(
            "div", class_="listing-search-item__info"
        ).find("a", class_="listing-search-item__link")
        real_estate_company = listing_info_item.text.strip()
        real_estate_company_url = listing_info_item.get("href")
        listing_url = listing.find(
            "a", class_="listing-search-item__link listing-search-item__link--title"
        ).get("href")
        listing_thumbnail = listing.find("img").get("src")
        return {
            "title": title,
            "address": address,
            "price_text": price_text,
            "url": self.base_url + listing_url,
            "thumbnail": listing_thumbnail,
            "real_estate_company": real_estate_company,
            "real_estate_company_url": self.base_url + real_estate_company_url,
            "features": {
                "surface_area": surface_area.text.strip(),
                "n_rooms": n_rooms.text.strip(),
                "interior_type": interior_type.text.strip(),
            },
        }

    def get_chrome_driver(self) -> webdriver.Chrome:
        """
        Gets the Chrome driver.
        """
        options = webdriver.ChromeOptions()
        service = webdriver.ChromeService()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--single-process")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-dev-tools")
        options.add_argument("--no-zygote")
        options.add_argument("--remote-debugging-port=9222")
        chrome = webdriver.Chrome(options=options, service=service)
        return chrome

    def extract_html(self) -> str:
        """
        Extracts the HTML from the Pararius website.
        """
        self._latest_extraction = datetime.now()
        with self.get_chrome_driver() as driver:
            self.logger.info(f"Extracting HTML from {self.url}")
            driver.get(self.url)
            return driver.page_source

    def scrape(self) -> list[dict[str, Any]]:
        """
        Scrapes the Pararius website for apartments
        using Selenium and BeautifulSoup.
        """
        html_src = self.extract_html()
        soup = BeautifulSoup(html_src, "html.parser")
        listings = soup.find_all("li", class_="search-list__item--listing")
        self.logger.info(f"Found {len(listings)} listings")
        return [self.extract_info_from_listing(listing) for listing in listings]
