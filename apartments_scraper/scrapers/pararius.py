from datetime import datetime
from functools import cached_property
import logging
import os
from typing import TYPE_CHECKING, Any
import urllib

from bs4 import BeautifulSoup

from apartments_scraper.utils.selenium import get_chrome_driver

if TYPE_CHECKING:
    from bs4.element import Tag


class ParariusScraper:
    SITE_NAME = "pararius"
    DEFAULT_SCRAPING_URL = (
        "https://www.pararius.com/apartments/{city}/0-1750/1-bedrooms/furnished/50m2"
    )
    DEFAULT_MAX_PAGES = 3

    def __init__(self, city: str, max_pages:int=None) -> None:
        """
        Instantiates an object that can scrape the Pararius website for apartments.
        
        @param city: The city in The Netherlands to scrape apartments for.
        @param max_pages: The maximum number of pages to scrape.
        """
        self.city = city
        self._latest_extraction = None
        self._logger = self._init_logger()
        self.max_pages = max_pages or self.DEFAULT_MAX_PAGES

    @cached_property
    def url(self) -> str:
        scraping_url = os.environ.get("PARARIUS_SCRAPING_URL", self.DEFAULT_SCRAPING_URL)
        city_part = "-".join(self.city.lower().split())
        scraping_url = scraping_url.format(city=city_part)
        return scraping_url

    @property
    def latest_extraction(self) -> datetime:
        return self._latest_extraction

    @cached_property
    def base_url(self) -> str:
        scheme = urllib.parse.urlparse(self.url).scheme
        site = urllib.parse.urlparse(self.url).netloc
        return f"{scheme}://{site}"

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    def _init_logger(self) -> logging.Logger:
        """
        Initializes the logger.
        """
        logger = logging.getLogger(
            f"apartments_scraper.{__name__}.{self.__class__.__name__}"
        )
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
                "surface_area": surface_area.text.strip() if surface_area else None,
                "n_rooms": n_rooms.text.strip() if n_rooms else None,
                "interior_type": interior_type.text.strip() if interior_type else None,
            },
        }

    def extract_html(self, url=None) -> str:
        """
        Extracts the HTML from the Pararius website.
        """
        url = url or self.url
        self._latest_extraction = datetime.now()
        with get_chrome_driver() as driver:
            self.logger.info(f"Extracting HTML from {url}")
            driver.get(url)
            return driver.page_source

    def scrape(self) -> list[dict[str, Any]]:
        """
        Scrapes the Pararius website for apartments
        using Selenium and BeautifulSoup.
        """
        listings_data = []
        page_url = None
        for i in range(self.max_pages):
            self.logger.info(f"Scraping page {i+1}/{self.max_pages} from site {self.SITE_NAME}")
            html_src = self.extract_html(url=page_url)
            soup = BeautifulSoup(html_src, "html.parser")
            listings = soup.find_all("li", class_="search-list__item--listing")
            self.logger.info(f"Found {len(listings)} listings")
            listings_data.extend([self.extract_info_from_listing(listing) for listing in listings])
            # Set the next page URL:
            next_page_button = soup.find("a", class_="pagination__link pagination__link--next")
            next_page_url = next_page_button.get("href") if next_page_button else None
            if next_page_url:
                page_url = self.base_url + next_page_url
            else:
                self.logger.info(f"No next page found, stopping at page {i+1}")
                break
        return listings_data
