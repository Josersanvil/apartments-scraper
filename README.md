# Apartments Scraper

A Python package to scrape apartments from various websites using Selenium and BeautifulSoup.

## Setup

### Docker

1. Install [Docker](https://docs.docker.com/get-docker/).
2. Build the Docker image: `docker build -t apartments_scraper .`
3. Run the Docker container: `docker run -it --rm apartments_scraper --help`

To store the scraped data in an S3 bucket you need to setup the [AWS CLI](<https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html>) and mount the AWS credentials file as a volume:

```bash
docker run -it --rm -v $HOME/.aws:/root/.aws apartments_scraper --city amsterdam --s3-dest s3://<bucket-name>/<path>
```

### Environment Variables

You can set the following environment variables to configure the scraper at runtime:

| Variable | Description | Default | Used by |
| --- | --- | --- | --- |
| `LAMBDA_LOG_LEVEL` | The log level for the Lambda function. | `INFO` | `lambda_function.py` |
| `APARTMENTS_SCRAPER_TARGET_S3_DEST` | The S3 destination for the scraped data (used by the Lambda Function) | | `lambda_function.py` |
| `PARARIUS_SCRAPING_URL` | The URL to scrape Pararius from. The variable `{city}` can be templated into the url | `https://www.pararius.com/apartments/{city}/0-1750/1-bedrooms/furnished/50m2` | `apartments_scraper/scrapers/pararius.py`
| `APARTMENTS_SCRAPER_MAX_PAGES` | The maximum number of pages to scrape. | `5` | `lambda_function.py` |
