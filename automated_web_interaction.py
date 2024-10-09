from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import (
    ElementClickInterceptedException, NoSuchWindowException, 
    TimeoutException, StaleElementReferenceException
)
import time

class WebDriverFactory:
    """Factory class for setting up the WebDriver with options."""
    
    @staticmethod
    def create_driver(executable_path, ignore_ssl_errors=True):
        chrome_options = webdriver.ChromeOptions()
        if ignore_ssl_errors:
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--ignore-ssl-errors')
        return webdriver.Chrome(executable_path=executable_path, options=chrome_options)

class RetryClicker:
    """Class to handle retries for clicking an element."""
    
    @staticmethod
    def click_with_retry(driver, by, identifier, retries=3):
        """Attempts to click an element with retries and JS fallback."""
        for i in range(retries):
            try:
                time.sleep(1)  # Wait briefly before retrying
                element = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((by, identifier)))
                driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(1)
                element.click()
                return True
            except StaleElementReferenceException:
                print(f"StaleElementReferenceException encountered, retrying... {i+1}/{retries}")
                time.sleep(10)
            except TimeoutException:
                print(f"TimeoutException: Unable to locate element {identifier}")
                return False
            except ElementClickInterceptedException as e:
                print(f"ElementClickInterceptedException: {str(e)}")
                try:
                    element = driver.find_element(by, identifier)
                    driver.execute_script("arguments[0].click();", element)
                    return True
                except Exception as js_e:
                    print(f"JavaScript click failed: {str(js_e)}")
        return False

class WebNavigator:
    """Class to encapsulate web navigation logic."""
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        
    def click_grandfather(self, target_element_id):
        """Clicks the grandfather (2 levels up in DOM) of a given element."""
        try:
            target_element = self.driver.find_element(By.ID, target_element_id)
            grandfather_element = target_element.find_element(By.XPATH, './../../..')
            self.driver.execute_script("arguments[0].scrollIntoView(true);", grandfather_element)
            time.sleep(1)
            grandfather_element.click()
            print(f"Successfully clicked on the grandfather of element {target_element_id}")
        except Exception as e:
            print(f"Error clicking on grandfather: {str(e)}")

    def interact_with_page(self):
        """Performs the entire interaction with the web page."""
        try:
            self.driver.get("https://192.168.1.101:5701/")
            self.login("USERNAME", "PASSWORD")
            self.handle_actions()
        except TimeoutException as e:
            print(f"An element was not found in time: {str(e)}")
        except NoSuchWindowException as e:
            print(f"Window not found: {str(e)}")
        finally:
            time.sleep(2)
            self.driver.quit()

    def login(self, username, password):
        """Logs into the application."""
        username_field = self.wait.until(EC.element_to_be_clickable((By.ID, "username")))
        username_field.clear()
        username_field.send_keys(username)
        
        password_field = self.wait.until(EC.element_to_be_clickable((By.ID, "password")))
        password_field.clear()
        password_field.send_keys(password)
        
        login_button = self.wait.until(EC.element_to_be_clickable((By.ID, "login_but")))
        login_button.click()
        time.sleep(2)

        if len(self.driver.window_handles) > 1:
            self.driver.switch_to.window(self.driver.window_handles[1])

    def handle_actions(self):
        """Handles actions after login."""
        RetryClicker.click_with_retry(self.driver, By.ID, "ELM_ID1")
        RetryClicker.click_with_retry(self.driver, By.ID, "ELM_ID2")
        self.click_grandfather("ELM_ID3")

        device_select_element = self.wait.until(EC.element_to_be_clickable((By.ID, "ELM_Select")))
        device_select = Select(device_select_element)
        total_options = len(device_select.options)

        for index in range(total_options):
            option = device_select.options[index]
            option_style = option.get_attribute('style')
            print(f"Selected option {index}: {option.text}")
            if option_style:
                print('Option style not valid, skipping...')
                continue

            device_select.select_by_index(index)
            RetryClicker.click_with_retry(self.driver, By.ID, "selectParametersButton")
            RetryClicker.click_with_retry(self.driver, By.ID, "ELM_ID4")

            try:
                RetryClicker.click_with_retry(self.driver, By.ID, "ELM_ID5")
                print(f"Clicked on 'Train Stage' for option {index}")
            except TimeoutException:
                print(f"No 'Train Stage' button found for option {index}, skipping")
            
            time.sleep(240)
            self.driver.refresh()

# Usage example:
if __name__ == "__main__":
    driver_path = r"C:\PATH TO CHROME DRIVER\chromedriver.exe"
    driver = WebDriverFactory.create_driver(driver_path)
    
    navigator = WebNavigator(driver)
    navigator.interact_with_page()
