import time
import os
import platform
import shutil
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from utils.logger import logger

class WalmartBot:
    def __init__(self, config):
        self.config = config
        self.driver = None
    
    def start_driver(self):
        logger.info("Starting browser for Walmart...")
        options = uc.ChromeOptions()
        if self.config.get("headless", False):
            options.add_argument("--headless=new")
        options.add_argument("--disable-blink-features=AutomationControlled")

        system = platform.system().lower()
        if system == "linux":
            options.binary_location = "/usr/bin/chromium"
            driver_path = "/usr/local/bin/chromedriver"
        elif system == "windows":
            default_chrome_path = os.path.expandvars(r"%ProgramFiles%\\Google\\Chrome\\Application\\chrome.exe")
            alt_chrome_path = os.path.expandvars(r"%ProgramFiles(x86)%\\Google\\Chrome\\Application\\chrome.exe")
            if os.path.exists(default_chrome_path):
                options.binary_location = default_chrome_path
            elif os.path.exists(alt_chrome_path):
                options.binary_location = alt_chrome_path
            else:
                logger.warning("Chrome installation not found, relying on PATH")
            driver_path = shutil.which("chromedriver.exe") or "chromedriver.exe"
        elif system == "darwin":  # macOS
            options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            driver_path = shutil.which("chromedriver") or "/usr/local/bin/chromedriver"
        else:
            logger.error(f"Unsupported OS: {system}")
            raise RuntimeError("Unsupported operating system")

        self.driver = uc.Chrome(
            options=options,
            driver_executable_path=driver_path,
            use_subprocess=True
        )
        self.driver.maximize_window()
        return self.driver

    def login(self):
        wait = WebDriverWait(self.driver, 40)
        self.driver.get("https://www.walmart.com/")
        logger.info("Opened Walmart homepage")

        try:
            account_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@link-identifier='Account']")))
            account_link.click()
            logger.info("Clicked Account link")
        except TimeoutException:
            logger.error("Could not find Account link — check page structure")
            self.driver.save_screenshot("debug_login_failed.png")
            return False

        try:
            sign_in_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='sign-in']")))
            sign_in_btn.click()
            logger.info("Clicked 'Sign in or create account'")
        except TimeoutException:
            logger.error("Could not find sign-in button")
            self.driver.save_screenshot("debug_login_failed.png")
            return False

        try:
            email_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@aria-label='Phone number or email']")))
            email_input.clear()
            email_input.send_keys(self.config["email"])
            continue_btn = wait.until(EC.element_to_be_clickable((By.ID, "login-continue-button")))
            continue_btn.click()
            logger.info(f"Entered email: {self.config['email']}")
        except TimeoutException:
            logger.error("Could not find email input or continue button")
            return False

        try:
            password_radio = wait.until(EC.element_to_be_clickable((By.XPATH, "//label[contains(., 'Password')]//input")))
            self.driver.execute_script("arguments[0].click();", password_radio)
            logger.info("Selected Password option")
        except TimeoutException:
            logger.info("Password option not shown (may not be needed)")

        try:
            pwd_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@aria-label='Enter your password']")))
            pwd_input.clear()
            pwd_input.send_keys(self.config["password"])
            sign_in_btn = wait.until(EC.element_to_be_clickable((By.ID, "withpassword-sign-in-button")))
            sign_in_btn.click()
            logger.info("Clicked Sign in")
        except TimeoutException:
            logger.error("Could not find password input or sign in button")
            return False

        if self.config.get("account_name"):
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, f"//div[contains(text(), '{self.config['account_name']}')]"))
                )
                logger.info(f"Login confirmed — detected name: {self.config['account_name']}")
            except TimeoutException:
                logger.warning(f"Could not confirm login for '{self.config['account_name']}'")
        
        return True

    def buy_now(self):
        wait = WebDriverWait(self.driver, 30)
        self.driver.get(self.config["product_url"])
        logger.info(f"Navigated to product page: {self.config['product_url']}")

        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))
            logger.info("Product page loaded")
        except TimeoutException:
            logger.warning("Product page may not have loaded fully")

        try:
            buy_now_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='buy-now-wrapper']"))
            )
            self.driver.execute_script("arguments[0].click();", buy_now_btn)
            logger.info("Clicked Buy Now")
        except TimeoutException:
            logger.warning("Buy Now button not available (maybe out of stock)")
            return False

        try:
            place_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Place order')]"))
            )
            if self.config.get("place_order", False):
                self.driver.execute_script("arguments[0].click();", place_btn)
                logger.info("ORDER PLACED SUCCESSFULLY!")
            else:
                logger.info("Dry run — not placing order (enable place_order=true in config.json)")
            return True
        except TimeoutException:
            logger.error("Could not find Place Order button")
            self.driver.save_screenshot("debug_place_order_failed.png")
            return False

    def run(self):
        try:
            self.start_driver()
            if not self.login():
                return False

            bought = False
            while not bought:
                bought = self.buy_now()
                if not bought:
                    logger.info("Product not available — retrying in 10 seconds...")
                    time.sleep(10)
            
            return True

        except Exception as e:
            logger.error(f"Walmart bot failed: {e}")
            return False
        finally:
            if self.driver:
                logger.info("Script finished — closing browser")
                self.driver.quit()

