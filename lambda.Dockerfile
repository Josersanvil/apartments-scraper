## Build
FROM public.ecr.aws/lambda/python:3.10 as build

ARG CHROME_DRIVER_VERSION=119.0.6045.105

RUN yum install -y unzip && \
    curl -Lo "/tmp/chromedriver-linux64.zip" "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${CHROME_DRIVER_VERSION}/linux64/chromedriver-linux64.zip" && \
    curl -Lo "/tmp/chrome-linux64.zip" "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${CHROME_DRIVER_VERSION}/linux64/chrome-linux64.zip" && \
    unzip /tmp/chromedriver-linux64.zip -d /opt/ && \
    unzip /tmp/chrome-linux64.zip -d /opt/

## Default
FROM public.ecr.aws/lambda/python:3.10

## Install some prerequisites
RUN yum install -y gcc atk cups-libs gtk3 libXcomposite alsa-lib \
    libXcursor libXdamage libXext libXi libXrandr libXScrnSaver \
    libXtst pango at-spi2-atk libXt xorg-x11-server-Xvfb \
    xorg-x11-xauth dbus-glib dbus-glib-devel nss mesa-libgbm

## Copy Chrome and Chrome Driver from build stage
COPY --from=build /opt/chrome-linux64 /opt/chrome
COPY --from=build /opt/chromedriver-linux64 /opt/
ENV SELENIUM_CHROME_EXEC_PATH=/opt/chrome/chrome
ENV SELENIUM_CHROME_DRIVER_PATH=/opt/chromedriver

## Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
RUN pip install botocore==1.32.6 --target ${LAMBDA_TASK_ROOT}

## Copy the source code
WORKDIR ${LAMBDA_TASK_ROOT}
COPY ./apartments_scraper ${LAMBDA_TASK_ROOT}/apartments_scraper
COPY ./lambda_function.py ${LAMBDA_TASK_ROOT}/

## Run the scraper
CMD ["lambda_function.handler"]
