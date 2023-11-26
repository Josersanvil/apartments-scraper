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
