import logging
import os
from io import BytesIO
from typing import Literal

import fsspec
import polars as pl

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


def write_df(
    df: pl.DataFrame, dest: str, format: Literal["parquet", "csv"] = "parquet"
):
    logger = get_logger()
    city = df["city"][0]
    date = df["date"][0]
    ts = df["extracted_at"][0].timestamp()
    if dest.startswith("s3://"):
        fs = fsspec.filesystem("s3")
    else:
        fs = fsspec.filesystem("file")
    fb = BytesIO()
    if format == "parquet":
        # Partition the data by city and date:
        dest_path = dest.rstrip("/") + f"/city={city}/date={date}/{int(ts)}.parquet"
        df_contents = df.select(pl.exclude("city", "date")).write_parquet(fb)
    elif format == "csv":
        dest_path = dest.rstrip("/") + f"/{city}_{date}_{int(ts)}.csv"
        df_contents = df.write_csv(fb)
    logger.info(f"Writing dataframe to destination: '{dest_path}'")
    if not dest.startswith("s3://"):
        fs.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with fs.open(dest_path, "wb") as f:
        f.write(fb.getvalue())


def scrape(
    city: str,
    outdir: str = None,
    s3_dest: str = None,
    format: Literal["parquet", "csv"] = "csv",
    max_pages: int = None,
    log_level: int | str = "INFO",
) -> None:
    """ "
    Scrapes apartments in the given city and writes the results to
    a file in the local machine and/or to S3.

    @param city: The city to scrape apartments for.
    @param outdir: The path of a directory in the local machine to write the results to.
    @param s3_dest: The S3 destination to write the results to.
        Should be in the format: s3://<bucket>/<prefix>
    @param format: The format to write the file in.
        One of: 'parquet', 'csv'. If 'parquet', the results will be written
        using file partitioning by city and date in separate directories.
    @param max_pages: The maximum number of pages to scrape.
    @param log_level: The log level to use.
    """
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
        write_df(df, s3_dest, format=format)
    if outdir:
        write_df(df, outdir, format=format)
    logger.info(f"Scraped {len(apartments)} apartments for city: '{city}'")
