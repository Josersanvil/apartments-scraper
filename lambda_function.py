from typing import Any
import json
import logging
import os

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
    payload = json.loads(event["payload"])
    args = {
        **payload,
        "s3_dest": os.environ.get(
            "APARTMENTS_SCRAPER_TARGET_S3_DEST",
            "s3://my-data-integrations/apartments-scraping/apartments",
        ),
        "log_level": lambda_logger.level,
    }
    ## Initiate the scraper:
    try:
        scrape(**args)
    except Exception as e:
        lambda_logger.exception("Received exception while scraping apartments.")
        return {
            "statusCode": 500,
            "body": json.dumps({"status": "error", "message": str(e)}),
        }
    return {
        "statusCode": 200,
        "body": json.dumps({"status": "success"}),
    }
