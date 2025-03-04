import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.firefox import GeckoDriverManager

class GeonodeProxyScraper:
    def __init__(self):
        """Initialize the Firefox WebDriver with proper settings."""
        options = webdriver.FirefoxOptions()
        # REMOVE headless mode for debugging
        # options.add_argument("--headless")

        self.driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
        self.driver.maximize_window()

    def fetch_proxies_from_page(self):
        """Extracts proxy IPs and ports from the correct table."""
        proxies = []
        try:
            print("Waiting for proxy table to load...")

            # Wait for the table to appear
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "free-proxies-table"))
            )
            time.sleep(2)  # Ensure it fully loads

            # Locate the proxy table
            proxy_table = self.driver.find_element(By.CLASS_NAME, "free-proxies-table")
            rows = proxy_table.find_elements(By.CSS_SELECTOR, "tbody tr")

            if not rows:
                print("⚠️ No proxy rows found. Possible bot detection or website change.")
                return []

            for row in rows:
                try:
                    ip = row.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text.strip()   # Column 1: IP Address
                    port = row.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text.strip() # Column 2: Port
                    if ip and port:
                        proxies.append(f"{ip}:{port}")  # Correct format: IP:Port
                except NoSuchElementException:
                    continue  # Skip invalid rows

        except TimeoutException:
            print("❌ Error: Timed out while waiting for proxy list to load.")
        except Exception as e:
            print(f"⚠️ Unexpected error while fetching proxies: {e}")

        return proxies

    def click_next_page(self):
        """Clicks the 'Next' button to load more proxies."""
        try:
            next_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Next')]"))
            )
            next_button.click()
            print("➡️ Moving to next page...")
            time.sleep(5)  # Allow time for next page to load
            return True
        except TimeoutException:
            print("⚠️ No more pages available.")
            return False  # Stop scraping when no "Next" button is found

    def save_proxies_to_file(self, proxies, filename="geonode_proxies.txt"):
        """Saves the proxy list in 'IP:Port' format."""
        with open(filename, "w") as file:
            for proxy in proxies:
                file.write(proxy + "\n")  # Each line is 'IP:Port'
        print(f"✅ Saved {len(proxies)} proxies to {filename}")

    def scrape_proxies(self, proxy_limit):
        """Main function to scrape proxies from multiple pages."""
        proxies = []
        url = "https://geonode.com/free-proxy-list"
        self.driver.get(url)
        time.sleep(5)  # Allow page to load

        while len(proxies) < proxy_limit:
            new_proxies = self.fetch_proxies_from_page()
            if not new_proxies:
                print("⚠️ No proxies found. Possible bot detection or incorrect selector. Stopping.")
                break

            proxies.extend(new_proxies)
            print(f"✅ Fetched {len(new_proxies)} proxies. Total so far: {len(proxies)}")

            if len(proxies) >= proxy_limit:
                break

            # Click "Next" to load more proxies
            if not self.click_next_page():
                break  # Stop if there's no next page

        self.save_proxies_to_file(proxies[:proxy_limit])

    def close(self):
        """Closes the browser and quits WebDriver."""
        self.driver.quit()


if __name__ == "__main__":
    scraper = GeonodeProxyScraper()

    try:
        proxy_limit = int(input("How many proxies do you want to fetch? "))
    except ValueError:
        print("❌ Invalid input. Please enter a number.")
        scraper.close()
        exit()

    scraper.scrape_proxies(proxy_limit)
    scraper.close()
