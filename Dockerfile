## Build
FROM python:3.10-slim as build

ARG CHROME_DRIVER_VERSION=119.0.6045.105

RUN apt-get update && apt-get install -y unzip curl && \
    curl -Lo "/tmp/chromedriver-linux64.zip" "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${CHROME_DRIVER_VERSION}/linux64/chromedriver-linux64.zip" && \
    curl -Lo "/tmp/chrome-linux64.zip" "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${CHROME_DRIVER_VERSION}/linux64/chrome-linux64.zip" && \
    unzip /tmp/chromedriver-linux64.zip -d /opt/ && \
    unzip /tmp/chrome-linux64.zip -d /opt/

## Default
FROM python:3.10-slim

## Install some prerequisites
# RUN apt-get update && apt-get install -y \
#     atk cups-libs gtk3 libXcomposite alsa-lib \
#     libXcursor libXdamage libXext libXi libXrandr libXScrnSaver \
#     libXtst pango at-spi2-atk libXt xorg-x11-server-Xvfb \
#     xorg-x11-xauth dbus-glib dbus-glib-devel nss mesa-libgbm
# RUN apt-get update && apt-get install -y libatk1.0-0 libcups2 libgtk-3-0 libxcomposite1 \
#     libxcursor1 libxdamage1 libxext6 libxi6 libxrandr2 libxss1 \
#     libxtst6 libpango-1.0-0 libatspi2.0-0 libxt6 xvfb \
#     xauth libdbus-glib-1-2 libdbus-1-dev libnss3 libgbm1

## Install dependencies for Chrome:
RUN apt-get update && apt-get install -y curl gpg
RUN curl -Lo /tmp/google.pub https://dl-ssl.google.com/linux/linux_signing_key.pub \
    && gpg --no-default-keyring --keyring /etc/apt/keyrings/google-chrome.gpg --import /tmp/google.pub \
    && echo 'deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main' | tee /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y google-chrome-stable

## Copy Chrome and Chrome Driver from build stage
COPY --from=build /opt/chrome-linux64 /opt/chrome
COPY --from=build /opt/chromedriver-linux64 /opt/

## Install dependencies
# RUN apt-get install -y gcc

## Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

## Copy the source code
WORKDIR /app
COPY . /app

## Run the scraper
ENTRYPOINT [ "python", "scrape.py" ]
