from tempfile import mkdtemp
import os

from selenium import webdriver


def get_chrome_driver() -> webdriver.Chrome:
    """
    Retrieves a configured Chrome driver.
    """
    options = webdriver.ChromeOptions()
    service = webdriver.ChromeService()

    if os.environ.get("SELENIUM_CHROME_EXEC_PATH"):
        options.binary_location = os.environ.get("SELENIUM_CHROME_EXEC_PATH")
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--single-process")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-dev-tools")
    options.add_argument("--no-zygote")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument(f"--user-data-dir={mkdtemp()}")
    options.add_argument(f"--data-path={mkdtemp()}")
    options.add_argument(f"--disk-cache-dir={mkdtemp()}")
    chrome = webdriver.Chrome(options=options, service=service)
    return chrome
