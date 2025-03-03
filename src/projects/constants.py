"""Module specific constants and error codes."""

from selenium.webdriver.common.by import By


class LoginPageLocators:
    USERNAME_INPUT = (By.ID, "normal_login_username")
    PASSWORD_INPUT = (By.ID, "normal_login_password")
    LOG_IN_BUTTON = (By.CSS_SELECTOR, "button.login-form-button")
