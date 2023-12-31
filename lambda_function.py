import json
import logging
import os
from typing import Any

from apartments_scraper.scrape import scrape


def get_logger():
    logger = logging.getLogger()
    logger.setLevel(os.environ.get("LAMBDA_LOG_LEVEL", "INFO"))
    return logger


def handler(event: dict[str, Any], context):
    """
    Reacts to an events from CloudWatch Events.
    The event should set the parameter `city` to the city to scrape.
    """
    lambda_logger = get_logger()
    lambda_logger.info(
        f"Got event for invocation request with id: '{context.aws_request_id}'"
    )
    print(json.dumps(event))
    max_pages = os.environ.get("APARTMENTS_SCRAPER_MAX_PAGES", None)
    try:
        max_pages = int(max_pages) if max_pages else None
    except ValueError:
        lambda_logger.error(
            f"Could not convert 'APARTMENTS_SCRAPER_MAX_PAGES' environment variable to an integer. Got '{max_pages}'. "
            "Setting max_pages to None."
        )
        max_pages = None
    args = {
        **event,
        "s3_dest": os.environ.get(
            "APARTMENTS_SCRAPER_TARGET_S3_DEST",
            "s3://my-data-integrations/apartments-scraping/apartments",
        ),
        "max_pages": max_pages,
        "log_level": lambda_logger.level,
        "format": "parquet",
    }
    ## Initiate the scraper:
    try:
        scrape(**args)
    except Exception as e:
        lambda_logger.error(f"Received exception '{e}' while scraping apartments.")
        raise
    return {
        "statusCode": 200,
        "body": json.dumps({"status": "success"}),
    }
