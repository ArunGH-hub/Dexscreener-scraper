# code taken from LLM

import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

print("Script started")

# --- Prompt user for token URL ---
user_input = input("Enter DexScreener token URL (must be a token page, e.g. with /base/...): ").strip()
token_url = user_input if user_input else "https://dexscreener.com"
print(f"Using URL: {token_url}")

# --- Selenium setup ---
print("Setting up Chrome WebDriver...")
options = Options()
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
print("Chrome launched successfully")

driver.get(token_url)
wait = WebDriverWait(driver, 20)

# --- Click the "Top Traders" tab ---
try:
    top_traders_tab = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//div[contains(text(),'Top Traders')]"))
    )
    top_traders_tab.click()
    print("Clicked on Top Traders tab")
    time.sleep(3)  # wait for data to load
except Exception as e:
    print("Could not click Top Traders tab:", e)
    driver.quit()
    exit()

# --- Scroll the trader table to load more rows ---
try:
    trader_table = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.overflow-y-auto"))
    )
    print("Scrolling Top Traders table...")
    last_height = driver.execute_script("return arguments[0].scrollHeight;", trader_table)

    for i in range(30):  # max scroll attempts
        driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", trader_table)
        time.sleep(1.5)
        new_height = driver.execute_script("return arguments[0].scrollHeight;", trader_table)
        print(f"Scroll attempt {i+1}, height={new_height}")
        if new_height == last_height:
            break
        last_height = new_height
    print("Finished scrolling.")
except Exception as e:
    print("Could not scroll Top Traders table:", e)

# --- Extract wallet addresses from the Maker column ---
wallet_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/address/']")
wallets = [el.text for el in wallet_elements if el.text.startswith("0x")]

driver.quit()
print("Browser closed")

# --- Save results ---
if wallets:
    wallets = list(set(wallets))  # deduplicate
    print(f"\nExtracted {len(wallets)} wallet addresses")
    csv_filename = "wallets.csv"
    with open(csv_filename, mode="w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Wallet Address"])
        for addr in wallets:
            writer.writerow([addr])
    print(f"All wallet addresses saved to '{csv_filename}'")
else:
    print("No wallets found.")
