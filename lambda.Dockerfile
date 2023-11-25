FROM umihico/aws-lambda-selenium-python:latest

RUN dnf install -y gcc

## Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

## Copy the source code
WORKDIR /app
COPY . /app

## Run the scraper
ENTRYPOINT [ "python", "scrape.py" ]