import argparse
from apartments_scraper.scrape import scrape


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


if __name__ == "__main__":
    parser = get_args_parser()
    args = parser.parse_args()
    scrape(
        city=args.city,
        s3_dest=args.s3_dest,
        log_level=args.log_level,
    )
