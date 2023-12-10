import logging

import polars as pl
import s3fs

from apartments_scraper.scrapers.pararius import ParariusScraper


def get_logger():
    logger = logging.getLogger(f"apartments_scraper.{__name__}")
    return logger


def clean_df_data(scraper: ParariusScraper, df: pl.DataFrame) -> pl.DataFrame:
    parsed_df = df.unnest("features")
    parsed_price_text = parsed_df["price_text"].str.extract_groups(
        r"€(?<price>\d+,?\d+) per (?<period>\w+)"
    )
    parsed_surface_area = parsed_df["surface_area"].str.extract_groups(
        r"(?<amount>\d+)\s*(?<unit>.*)"
    )
    parsed_df = parsed_df.with_columns(
        city=pl.lit(scraper.city),
        website=pl.lit(scraper.base_url),
        price=(
            parsed_price_text.struct.field("price")
            .str.replace(",", "")
            .cast(pl.Float64)
        ),
        price_period=parsed_price_text.struct.field("period"),
        surface_area_amount=parsed_surface_area.struct.field("amount").cast(pl.Float64),
        surface_area_unit=parsed_surface_area.struct.field("unit"),
        n_rooms=parsed_df["n_rooms"].str.extract(r"(\d+) rooms").cast(pl.Float64),
        date=pl.lit(scraper.latest_extraction.date()),
        extracted_at=pl.from_epoch(pl.lit(scraper.latest_extraction.timestamp())),
    ).select(pl.exclude("price_text"))
    return parsed_df


def write_df_to_s3(df: pl.DataFrame, s3_dest: str) -> None:
    logger = get_logger()
    city = df["city"][0]
    date = df["date"][0]
    ts = df["extracted_at"][0].timestamp()
    fs = s3fs.S3FileSystem()
    # Partition the data by city and date:
    dest_path = s3_dest.rstrip("/") + f"/city={city}/date={date}/{int(ts)}.parquet"
    logger.info(f"Writing dataframe to S3 destination: '{dest_path}'")
    with fs.open(dest_path, "wb") as f:
        df.select(pl.exclude("city", "date")).write_parquet(f)


def scrape(city: str, s3_dest: str = None, max_pages=None, log_level: int | str = "INFO") -> None:
    logging.basicConfig()
    logger = get_logger()
    logger.setLevel(log_level)
    logger.info(f"Scraping apartments for city: '{city}'")
    scraper = ParariusScraper(city=city.lower(), max_pages=max_pages)
    scraper.logger.setLevel(log_level)
    apartments = scraper.scrape()
    df = pl.DataFrame(apartments)
    df = clean_df_data(scraper, df)
    if s3_dest:
        write_df_to_s3(df, s3_dest)
    logger.info(f"Scraped {len(apartments)} apartments for city: '{city}'")
