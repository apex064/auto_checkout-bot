import os
import time
import platform
import shutil
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.logger import logger

class TargetBot:
    def __init__(self, config):
        self.config = config
        self.driver = None

    def start_driver(self):
        logger.info("Starting browser for Target...")
        options = uc.ChromeOptions()
        if self.config.get("headless", False):
            options.add_argument("--headless=new")
        options.add_argument("--disable-blink-features=AutomationControlled")

        system = platform.system().lower()

        if system == "linux":
            options.binary_location = "/usr/bin/chromium"
            driver_path = "/usr/local/bin/chromedriver"
        elif system == "windows":
            default_chrome_path = os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe")
            alt_chrome_path = os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe")
            if os.path.exists(default_chrome_path):
                options.binary_location = default_chrome_path
            elif os.path.exists(alt_chrome_path):
                options.binary_location = alt_chrome_path
            else:
                logger.warning("Chrome installation not found — relying on PATH")

            driver_path = shutil.which("chromedriver.exe") or "chromedriver.exe"
        elif system == "darwin":  # macOS
            possible_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    options.binary_location = path
                    break
            driver_path = shutil.which("chromedriver") or "/usr/local/bin/chromedriver"
        else:
            raise RuntimeError(f"Unsupported OS: {system}")

        self.driver = uc.Chrome(
            options=options,
            driver_executable_path=driver_path,
            use_subprocess=True
        )
        self.driver.maximize_window()
        return self.driver

    def login(self):
        wait = WebDriverWait(self.driver, 40)
        self.driver.get("https://www.target.com/")
        logger.info("Opened Target homepage")

        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        try:
            close_modal = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Close') or contains(., 'Not now')]"))
            )
            close_modal.click()
            logger.info("Closed region/zip modal")
        except:
            pass

        try:
            accept_cookies = self.driver.find_elements(By.XPATH, "//button[contains(., 'Accept all cookies')]")
            if accept_cookies:
                accept_cookies[0].click()
                logger.info("Accepted cookies")
        except:
            pass

        try:
            account_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Account']"))
            )
            account_button.click()
            logger.info("Clicked Account button")
            time.sleep(1)
        except:
            logger.error("Could not find Account button — page layout may have changed")
            self.driver.save_screenshot("debug_login_failed.png")
            return False

        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href,'/signin')]"))).click()
            logger.info("Clicked Sign in link")
        except:
            logger.error("Could not find Sign in link")
            self.driver.save_screenshot("debug_login_failed.png")
            return False

        email_input = wait.until(EC.presence_of_element_located((By.ID, "username")))
        email_input.send_keys(self.config["email"])
        logger.info(f"Entered email: {self.config['email']}")

        continue_btn = wait.until(EC.element_to_be_clickable((By.ID, "login")))
        continue_btn.click()
        logger.info("Clicked Continue after email")

        enter_pwd_span = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Enter your password']"))
        )
        enter_pwd_span.click()
        logger.info("Clicked 'Enter your password'")

        pwd_input = wait.until(EC.presence_of_element_located((By.ID, "password")))
        pwd_input.send_keys(self.config["password"])
        logger.info("Entered password")

        sign_in_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Sign in with password']"))
        )
        sign_in_btn.click()
        logger.info("Clicked 'Sign in with password'")

        try:
            skip_link = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[text()='Skip']"))
            )
            skip_link.click()
            logger.info("Phone number page detected — clicked 'Skip'")
        except:
            logger.info("No phone number page — continuing to home page")

        if self.config.get("account_name"):
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located(
                        (By.XPATH, f"//span[contains(text(), 'Hi, {self.config['account_name']}')]")
                    )
                )
                logger.info(f"Login confirmed — detected header: Hi, {self.config['account_name']}")
            except:
                logger.warning(f"Could not confirm login for account '{self.config['account_name']}'")
        else:
            logger.warning("No account_name provided — cannot confirm login header")
        
        return True

    def check_stock_and_add(self):
        wait = WebDriverWait(self.driver, 30)
        self.driver.get(self.config["product_url"])
        logger.info(f"Navigated to product page: {self.config['product_url']}")

        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))
            logger.info("Product page loaded")
        except:
            logger.warning("Product main content not fully loaded — proceeding anyway")

        try:
            add_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Add to cart')]")))
            add_btn.click()
            logger.info("Clicked Add to cart — waiting 5 seconds")
            time.sleep(5)
            return True
        except:
            logger.warning("Product out of stock or Add to cart button not clickable")
            return False

    def go_to_checkout(self):
        self.driver.get("https://www.target.com/checkout/start")
        logger.info("Navigated to direct checkout page")
        for _ in range(10):
            try:
                WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, "//h1[contains(., 'Checkout')]"))
                )
                logger.info("Checkout page loaded")
                return True
            except:
                time.sleep(1)
        logger.warning("Checkout page may not have fully loaded yet")
        self.driver.save_screenshot("debug_checkout_failed.png")
        return False

    def fill_shipping(self):
        wait = WebDriverWait(self.driver, 20)
        try:
            name_input = wait.until(EC.presence_of_element_located((By.NAME, "firstName")))
            name_input.clear()
            name_input.send_keys(self.config["full_name"])
            self.driver.find_element(By.NAME, "addressLine1").send_keys(self.config["address"])
            self.driver.find_element(By.NAME, "city").send_keys(self.config["city"])
            self.driver.find_element(By.NAME, "state").send_keys(self.config["state"])
            self.driver.find_element(By.NAME, "zip").send_keys(self.config["zip"])
            self.driver.find_element(By.NAME, "phone").send_keys(self.config["phone"])
            logger.info("Filled shipping information")
            return True
        except:
            logger.info("Shipping info may already be saved — skipping")
            return False

    def fill_payment(self):
        wait = WebDriverWait(self.driver, 20)
        try:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1)

            add_card_radio = wait.until(
                EC.element_to_be_clickable((By.ID, "AddCreditDebitCellRadio"))
            )
            add_card_radio.click()
            logger.info("Selected 'Credit or Debit Card'")
            time.sleep(1)

            wait.until(EC.presence_of_element_located((By.ID, "credit-card-number-input"))).send_keys(self.config["card_number"])
            self.driver.find_element(By.ID, "credit-card-expiration-input").send_keys(self.config["card_exp"])
            self.driver.find_element(By.ID, "credit-card-cvv-input").send_keys(self.config["card_cvv"])
            self.driver.find_element(By.ID, "credit-card-name-input").send_keys(self.config["full_name"])
            logger.info("Entered card details")

            self.driver.find_element(By.ID, "billing-address-first-name-input").send_keys(self.config["full_name"].split()[0])
            self.driver.find_element(By.ID, "billing-address-last-name-input").send_keys(self.config["full_name"].split()[-1])
            self.driver.find_element(By.ID, "billing-address-line1-input").send_keys(self.config["address"])
            self.driver.find_element(By.ID, "billing-address-city-input").send_keys(self.config["city"])
            self.driver.find_element(By.ID, "billing-address-state-input").send_keys(self.config["state"])
            self.driver.find_element(By.ID, "billing-address-zip-code-input").send_keys(self.config["zip"])
            self.driver.find_element(By.ID, "billing-address-phone-input").send_keys(self.config["phone"])
            logger.info("Entered billing address")

            save_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[@data-test='save_and_continue_button_step_PAYMENT']"))
            )
            save_btn.click()
            logger.info("Clicked 'Save and continue'")
            time.sleep(2)
            return True
        except Exception as e:
            logger.error(f"Payment filling failed: {e}")
            return False

    def place_order(self):
        wait = WebDriverWait(self.driver, 20)
        try:
            place_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Place your order')]")))
            if self.config.get("place_order", False):
                place_btn.click()
                logger.info("ORDER PLACED SUCCESSFULLY!")
            else:
                logger.info("Dry run: not placing order (set place_order=true in config.json to buy)")
            return True
        except:
            logger.error("Could not find Place Order button")
            return False

    def run(self):
        try:
            self.start_driver()
            if not self.login():
                return False

            attempt = 0
            added_to_cart = False
            while not added_to_cart:
                attempt += 1
                logger.info(f"Attempt #{attempt} — Checking product stock...")
                added_to_cart = self.check_stock_and_add()
                if not added_to_cart:
                    logger.info(f"Product not in stock — refreshing in {self.config.get('refresh_interval', 10)} seconds")
                    time.sleep(self.config.get('refresh_interval', 10))

            if not self.go_to_checkout():
                return False

            self.fill_shipping()
            self.fill_payment()
            self.place_order()

            return True

        except Exception as e:
            logger.error(f"Target bot failed: {e}")
            return False
        finally:
            if self.driver:
                logger.info("Script finished — closing browser")
                self.driver.quit()

