import argparse
import logging

import polars as pl
import s3fs

from scrapers.pararius import ParariusScraper


def get_args_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        "Scrapes websites for apartments in The Netherlands."
    )
    parser.add_argument(
        "--city",
        type=str,
        help="The city to scrape for apartments",
        required=True,
    )
    parser.add_argument(
        "--s3-dest",
        type=str,
        help="The S3 destination to store the scraped data as an S3 URI.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="The log level to use.",
    )
    return parser


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
    city = df["city"][0]
    date = df["date"][0]
    ts = df["extracted_at"][0].timestamp()
    fs = s3fs.S3FileSystem()
    # Partition the data by city and date:
    dest_path = s3_dest.rstrip("/") + f"/city={city}/date={date}/{ts}.parquet"
    with fs.open(dest_path, "wb") as f:
        df.select(pl.exclude("city", "date")).write_parquet(f)


def main():
    print("Scraping apartments...")
    parser = get_args_parser()
    args = parser.parse_args()
    logging.basicConfig()
    scraper = ParariusScraper(city=args.city.lower())
    scraper.logger.setLevel(args.log_level)
    apartments = scraper.scrape()
    df = pl.DataFrame(apartments)
    df = clean_df_data(scraper, df)
    write_df_to_s3(df, args.s3_dest)


if __name__ == "__main__":
    main()
