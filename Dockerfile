FROM python:3.10-slim

## Set the Chrome Driver version (Needs to be versions 115 or higher)
ARG CHROME_DRIVER_VERSION=119.0.6045.105

## Install some prerequisites
RUN apt-get update && apt-get install -y curl unzip gnupg \
    libatk1.0-0 libcups2 libgtk-3-0 libxcomposite1 \
    libxcursor1 libxdamage1 libxext6 libxi6 libxrandr2 libxss1 \
    libxtst6 libpango-1.0-0 libatspi2.0-0 libxt6 xvfb \
    xauth libdbus-glib-1-2 libdbus-1-dev libnss3 libgbm1

## Download Chrome and Chrome Driver
RUN curl -Lo "/tmp/chromedriver-linux64.zip" "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${CHROME_DRIVER_VERSION}/linux64/chromedriver-linux64.zip" && \
    curl -Lo "/tmp/chrome-linux64.zip" "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${CHROME_DRIVER_VERSION}/linux64/chrome-linux64.zip" && \
    unzip /tmp/chromedriver-linux64.zip -d /tmp/ && \
    unzip /tmp/chrome-linux64.zip -d /tmp/ && \
    mv /tmp/chromedriver-linux64/* /opt/ && \
    mv /tmp/chrome-linux64 /opt/chrome

## Login as a non-root user
RUN useradd -ms /bin/bash scraper
USER scraper

## Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

## Set the Chrome Driver path
ENV PATH="/opt/chromedriver:${PATH}"
## Set display port
ENV DISPLAY=:99

## Copy the source code
COPY . /app
WORKDIR /app

## Run the scraper
ENTRYPOINT [ "python", "scrape.py" ]
