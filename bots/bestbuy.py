import time
import os
import platform
import shutil
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, StaleElementReferenceException
from utils.logger import logger

class BestBuyBot:
    def __init__(self, config):
        self.config = config
        self.driver = None

    def start_driver(self):
        logger.info("Starting browser for BestBuy...")
        options = uc.ChromeOptions()
        if self.config.get("headless", False):
            options.add_argument("--headless=new")
        options.add_argument("--disable-blink-features=AutomationControlled")

        # --------- Cross-Platform Chrome Binary Detection ---------
        system = platform.system().lower()
        print(f"Detected OS: {system}")
        chrome_binary = None
        if system == "linux":
            # Prefer chromium, fallback to google-chrome
            chrome_binary = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
        elif system == "darwin":  # macOS
            chrome_binary = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        elif system == "windows":
            possible_paths = [
                os.path.join(os.environ.get("PROGRAMFILES", ""), "Google/Chrome/Application/chrome.exe"),
                os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "Google/Chrome/Application/chrome.exe"),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google/Chrome/Application/chrome.exe"),
            ]
            chrome_binary = next((p for p in possible_paths if os.path.exists(p)), None)

        if chrome_binary:
            options.binary_location = chrome_binary
            logger.info(f"Using Chrome binary: {chrome_binary}")
        else:
            logger.warning("Could not detect Chrome/Chromium automatically — falling back to system default")

        # --------- Cross-Platform Chromedriver Detection ---------
        driver_path = shutil.which("chromedriver")
        if not driver_path:
            logger.warning("chromedriver not found in PATH — relying on undetected-chromedriver's default")
            driver_path = None

        self.driver = uc.Chrome(
            options=options,
            driver_executable_path=driver_path,
            use_subprocess=True
        )
        try:
            self.driver.maximize_window()
        except:
            logger.warning("Could not maximize window — possibly running headless")

        return self.driver

    def login(self):
        wait = WebDriverWait(self.driver, 40)
        self.driver.get("https://www.bestbuy.com/?intl=nosplash")
        logger.info("Opened BestBuy homepage")
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        try:
            account_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(@class, 'line-clamp') and text()='Account']"))
            )
            account_button.click()
            logger.info("Clicked Account button")
            time.sleep(1)
        except:
            logger.error("Could not find Account button — page layout may have changed")
            self.driver.save_screenshot("debug_login_failed.png")
            return False

        try:
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//a[@data-testid='signInButton' and text()='Sign In']")
            )).click()
            logger.info("Clicked Sign in link")
        except:
            logger.error("Could not find Sign in link")
            self.driver.save_screenshot("debug_login_failed.png")
            return False

        email_input = wait.until(EC.presence_of_element_located((By.ID, "fld-e")))
        email_input.send_keys(self.config["email"])
        logger.info(f"Entered email: {self.config['email']}")

        continue_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "cia-form__controls__submit")))
        continue_btn.click()
        logger.info("Clicked Continue after email")

        time.sleep(2)

        try:
            self.driver.find_element(By.ID, "fld-p1")
            logger.info("Password field already visible — skipping 'Use password' button")
        except:
            use_password_clicked = False
            possible_xpaths = [
                "//span[contains(text(),'Use password')]",
                "//button[contains(., 'Use password')]",
                "//button[contains(text(), 'password')]",
                "//button[contains(@class,'cia-button') and contains(.,'password')]",
                "//button[contains(@data-track, 'SignIn_Password')]"
            ]
            for xpath in possible_xpaths:
                try:
                    use_password_el = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    try:
                        use_password_el.click()
                    except (ElementClickInterceptedException, StaleElementReferenceException):
                        self.driver.execute_script("arguments[0].click();", use_password_el)
                    logger.info(f"Clicked 'Use password' via selector: {xpath}")
                    use_password_clicked = True
                    break
                except TimeoutException:
                    continue

            if not use_password_clicked:
                logger.warning("'Use password' element not found — maybe password field is already visible")

        pwd_input = wait.until(EC.presence_of_element_located((By.ID, "fld-p1")))
        pwd_input.send_keys(self.config["password"])
        logger.info("Entered password")

        sign_in_btn = wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, "cia-form__controls__submit"))
        )
        sign_in_btn.click()
        logger.info("Clicked 'Continue' to sign in")

        if self.config.get("account_name"):
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located(
                        (By.XPATH, f"//span[contains(text(), '{self.config['account_name']}')]")
                    )
                )
                logger.info(f"Login confirmed — detected account name: {self.config['account_name']}")
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
            add_btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[@data-test-id='add-to-cart']//span[text()='Add to cart']/..")
            ))
            add_btn.click()
            logger.info("Clicked Add to Cart — waiting 5 seconds")
            time.sleep(5)
            return True
        except:
            logger.warning("Product out of stock or Add to Cart button not clickable")
            self.driver.save_screenshot("debug_add_to_cart.png")
            return False

    def go_to_checkout(self):
        self.driver.get("https://www.bestbuy.com/cart")
        logger.info("Navigated to cart page")

        try:
            checkout_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[@class='btn btn-lg btn-block btn-primary' and @data-track='Checkout - Top']")
                )
            )
            checkout_btn.click()
            logger.info("Clicked Checkout")
            return True
        except:
            logger.error("Could not find Checkout button — maybe cart is empty or page layout changed")
            self.driver.save_screenshot("debug_checkout_click.png")
            return False

    def continue_to_payment(self):
        wait = WebDriverWait(self.driver, 20)
        try:
            cont_btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//span[text()='Continue to Payment Information']")
            ))
            cont_btn.click()
            logger.info("Clicked 'Continue to Payment Information'")
            time.sleep(2)
            return True
        except:
            logger.error("Could not find 'Continue to Payment Information' button")
            self.driver.save_screenshot("debug_continue_to_payment.png")
            return False

    def fill_shipping(self):
        wait = WebDriverWait(self.driver, 20)
        try:
            self.driver.find_element(By.ID, "first-name").clear()
            self.driver.find_element(By.ID, "first-name").send_keys(self.config["full_name"].split()[0])
            self.driver.find_element(By.ID, "last-name").send_keys(self.config["full_name"].split()[-1])
            self.driver.find_element(By.ID, "address-input").send_keys(self.config["address"])
            self.driver.find_element(By.ID, "city").send_keys(self.config["city"])
            self.driver.find_element(By.ID, "state").send_keys(self.config["state"])
            self.driver.find_element(By.ID, "postalCode").send_keys(self.config["zip"])
            self.driver.find_element(By.ID, "phone").send_keys(self.config["phone"])
            logger.info("Filled shipping info")
            return True
        except:
            logger.info("Shipping info may already be saved — skipping")
            return False

    def fill_payment(self):
        wait = WebDriverWait(self.driver, 20)
        try:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1)

            self.driver.find_element(By.ID, "number").send_keys(self.config["card_number"])
            self.driver.find_element(By.ID, "expirationDate").send_keys(self.config["card_exp"])
            self.driver.find_element(By.ID, "cvv").send_keys(self.config["card_cvv"])
            self.driver.find_element(By.ID, "first-name").send_keys(self.config["full_name"].split()[0])
            self.driver.find_element(By.ID, "last-name").send_keys(self.config["full_name"].split()[-1])
            logger.info("Entered card details and name")

            cont_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Continue to Payment Information']/.."))
            )
            cont_btn.click()
            logger.info("Clicked 'Continue to Review'")
            time.sleep(2)
            return True
        except Exception as e:
            logger.error(f"Payment filling failed: {e}")
            return False

    def place_order(self):
        wait = WebDriverWait(self.driver, 20)
        try:
            place_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-track='Place your Order - In-line']")))
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

            # Retry loop
            in_stock = False
            while not in_stock:
                in_stock = self.check_stock_and_add()
                if not in_stock:
                    logger.info("Product not in stock — retrying in 10 seconds...")
                    time.sleep(10)

            if not self.go_to_checkout():
                return False

            if not self.continue_to_payment():
                return False

            self.fill_shipping()
            self.fill_payment()
            self.place_order()

            return True

        except Exception as e:
            logger.error(f"BestBuy bot failed: {e}")
            return False
        finally:
            if self.driver:
                logger.info("Script finished — closing browser")
                self.driver.quit()

