"""Module specific business logic."""

import functools
import os
from functools import reduce
from typing import Callable, Generator
from urllib.parse import unquote

from loguru import logger
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeWebDriver
from selenium.webdriver.remote.webelement import WebElement

from src.projects.constants import LoginPageLocators, MainPageLocators, VesyncService
from src.projects.exceptions import ElementNotFoundError
from src.utils import load_env


class BasePage(object):
    """Base class to initialize the base page that will be called from all pages."""

    def __init__(self, driver: ChromeWebDriver):
        self.driver = driver


class BasePageElement:
    """Base page element class that is initialized on every page object class."""

    def __init__(self, *locators: tuple):
        """Init descriptor.

        Note:
            If multiple locators were supplied,
            the second one is relative to the first, the third is relative to the second, and so on.

        >>> e = BasePageElement((By.ID, "some-id"), (By.CSS_SELECTOR, ".some-class"))

        :param locators: Tuple of locator.
        """
        self.locators = locators

    def get_web_element(self, driver: ChromeWebDriver) -> WebElement:
        """Return WebElement instance.

        :param driver: ChromeWebDriver instance.
        """
        try:
            e = reduce(
                lambda node, locator: node.find_element(*locator),
                [driver, *self.locators],
            )
            logger.debug(f"An element was found by locator {self.locators}.")
            return e
        except NoSuchElementException as e:
            logger.error((message := f"No element found by locator {self.locators}."))
            raise ElementNotFoundError(message) from e

    def __set__(self, obj: BasePage, value: str):
        """Set the text to the value supplied.

        :param obj: BasePage instance.
        :param value: Value to set.
        """
        element = self.get_web_element(obj.driver)
        element.clear()
        element.send_keys(value)

    def __get__(self, obj: BasePage, owner) -> WebElement:
        """Get the text of the specified object.

        :param obj: BasePage instance.
        :param owner: Owner of the descriptor.
        """
        return self.get_web_element(obj.driver)


class LoginPage(BasePage):
    """Login page."""

    username_input = BasePageElement(LoginPageLocators.USERNAME_INPUT)
    password_input = BasePageElement(LoginPageLocators.PASSWORD_INPUT)
    log_in_input = BasePageElement(LoginPageLocators.LOG_IN_BUTTON)


class MainPage(BasePage):
    """Main page."""

    active_tab = BasePageElement(MainPageLocators.ACTIVE_TAB)


def init_chrome_driver(
    url: str, is_headless: bool = True, wait_seconds: int = 10
) -> ChromeWebDriver:
    """Return an instance of Chrome WebDriver.

    :param url: URL to open.
    :param is_headless: Headless mode.
    :param wait_seconds: Wait seconds for every element.
    """
    options = webdriver.ChromeOptions()

    if is_headless:
        options.add_argument("--headless=new")

    # Fix: DevToolsActivePort file doesn't exist while trying to initiate Chrome Browser on CentOS.
    # Reference: https://stackoverflow.com/a/50725918/10306969
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    # Wait for every element.
    driver.implicitly_wait(wait_seconds)

    driver.get(url)

    logger.success(f"Successfully initializing selenium driver ({url}).")

    return driver


def wait_until_main_page_loaded(driver: ChromeWebDriver):
    """Wait until main page of ops was loaded.

    :param driver: ChromeWebDriver instance.
    """
    main_page = MainPage(driver)
    main_page.active_tab.click()


def auth(
    driver: ChromeWebDriver,
    username: str,
    password: str,
    wait_processor: Callable,
    *cookies_to_read: str,
) -> Generator[tuple, None, None]:
    """Authenticate and return token info.

    :param driver: ChromeWebDriver instance.
    :param username: Username.
    :param password: Password.
    :param wait_processor: Wait until some condition is met, e.g. page is loaded.
    :param cookies_to_read: Cookies to read.
    :return: Generator of cookie and value.
    """
    # Authenticate.
    login_page = LoginPage(driver)
    login_page.username_input = username
    login_page.password_input = password
    login_page.log_in_input.click()

    try:
        # Wait until page is loaded.
        wait_processor(driver)
        logger.success("Log in successfully.")
    except Exception as e:
        logger.error(
            f"Failed to enter main page after logging in, "
            f"possible reasons: login failed (password changed), page elements changed, exception: {e}"
        )

    # read cookie
    for cookie in cookies_to_read:
        yield cookie, unquote(driver.get_cookie(cookie)["value"])


@functools.cache
def auth_pm() -> dict[str, str]:
    """Authenticate to pm.vesync.co and return token info.

    Dotenv file should exist in the root directory and contain the following keys:
    - IT_USERNAME
    - IT_PASSWORD

    :return: Dictionary of token info, e.g. {"userId": "123", "token": "token"}
    """
    load_env()

    # Initialize Chrome WebDriver.
    driver = init_chrome_driver(VesyncService.PM_FRONTEND_ORIGIN)

    # Authenticate.
    return dict(
        auth(
            driver,
            os.getenv("IT_USERNAME"),
            os.getenv("IT_PASSWORD"),
            wait_until_main_page_loaded,
            "userId",
            "token",
        )
    )
