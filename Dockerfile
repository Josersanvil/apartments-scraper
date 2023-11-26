# Build Stage
FROM python:3.10-slim as build

ARG CHROME_VERSION=119.0.6045.105

## Install some prerequisites
RUN apt-get update && apt-get install -y unzip curl
## Download Chrome and Chrome Driver
RUN curl -sS -Lo /tmp/chrome.deb https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_${CHROME_VERSION}-1_amd64.deb && \
    curl -sS -Lo "/tmp/chromedriver-linux64.zip" "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${CHROME_VERSION}/linux64/chromedriver-linux64.zip" && \
    unzip /tmp/chromedriver-linux64.zip -d /opt/

# Default Stage
FROM python:3.10-slim

## Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

## Install Chrome:
COPY --from=build /tmp/chrome.deb /tmp/chrome.deb
RUN apt-get update && apt-get install -y /tmp/chrome.deb \
    && rm /tmp/chrome.deb
## Copy Chrome Driver from build stage
COPY --from=build /opt/chromedriver-linux64 /app/

## Copy the source code
WORKDIR /app
COPY ./apartments_scraper /app/apartments_scraper

## Run the scraper as the entrypoint
ENTRYPOINT [ "python", "-m", "apartments_scraper" ]
