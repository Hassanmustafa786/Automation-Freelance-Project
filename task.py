from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
import time
import re
import random
from urllib.parse import urlparse, parse_qs
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import pandas as pd
from pymongo import MongoClient

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["Leads"]
collection = db["lead_collection_1"]

# Global variable for storing the driver
driver = None

def initialize_driver():
    global driver
    if driver is None:
        # Configure Edge options for security and stability
        edge_options = Options()
        edge_options.add_argument("--start-maximized")  # Start browser maximized
        edge_options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
        edge_options.add_experimental_option('useAutomationExtension', False)
        edge_options.add_argument("--profile-directory=Default")
        edge_options.add_argument("--user-data-dir=var/tmp/chrome_user_data")  # Ensure this path is correct
        edge_options.add_argument("--no-sandbox")  # Added for added security, especially for headless modes
        webdriver_path = "edgedriver_mac64/msedgedriver"  # Replace with the correct path for your system
        service = Service(webdriver_path)
        driver = webdriver.Edge(service=service, options=edge_options)
    return driver


headers_list = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36",
        "Accept-Language": "en-GB,en;q=0.8"
    },
    {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36",
        "Accept-Language": "fr-FR,fr;q=0.7"
    }
]
random.shuffle(headers_list)
url = "https://tmsearch.uspto.gov/search/search-information"  # Replace with your target URL
selected_header = headers_list[0]  # Use the first header from the shuffled list
response = requests.get(url, headers=selected_header)
soup = BeautifulSoup(response.text, 'html.parser')
print("Selected Header:", selected_header)

# Initialize driver
driver = initialize_driver()
url = "https://tmsearch.uspto.gov/search/search-information"
driver.get(url)
# Initialize an empty DataFrame
data = []
counter = 0
while True:
    # Reset all variables to None at the start of each loop iteration
    new_url = None
    abandoned_date = None
    mark_text = None
    phone = None
    email = None
    signatory_name = None
    signatory_position = None
    signatory_phone = None
    signatory_phone_1 = None

    # Wait for the page to load and ensure the button is interactable
    try:
        # Wait for the button to become clickable (adjust the selector as needed)
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "mat-mdc-select.ng-tns-c1154042729-4"))
        )
        # Click the button
        button.click()
        print("Dropdown Button clicked successfully!")

        # Wait for the "Goods and services" option to be clickable
        goods_and_services_item = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//mat-option/span[contains(text(), 'Goods and services')]"))
        )
        # Click on the "Goods and services" option
        goods_and_services_item.click()
        print("Goods and services option clicked successfully!")

        # Wait for the input field to become interactable
        input_field = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "goodsAndServices"))
        )

        # Send a keyword to the input field
        input_field.send_keys("Construction")  # Replace with the desired keyword

        # Press Enter to initiate the search
        input_field.send_keys(Keys.RETURN)
        print("Search initiated by pressing Enter!")

        # Wait for the checkbox to become interactable
        checkbox = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "statusLive"))
        )

        # Uncheck the checkbox if it's already checked
        if checkbox.is_selected():
            checkbox.click()
            print("Checkbox unchecked successfully!")
        time.sleep(5)

        if counter >= 1:
            for i in range(counter):
                time.sleep(5)
                # Wait for the "navigate next" button to be clickable and click it
                try:
                    # Wait for the element to be present
                    navigate_next_button = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//li[@class='page-item']//i[text()='navigate_next']"))
                    )
                    driver.execute_script("arguments[0].scrollIntoView(true);", navigate_next_button)
                    WebDriverWait(driver, 10).until(EC.visibility_of(navigate_next_button))
                    driver.execute_script("arguments[0].click();", navigate_next_button)
                    print("Clicked on the 'navigate next' button.")
                except Exception as e:
                    print(f"An error occurred: {e}")

        # Wait for the div elements with the specific class to be present
        result_cards = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "card.m-2.result-card.ng-star-inserted"))
        )

        # Click on the first result card
        if result_cards:
            # Wait for the elements to load (adjust the timeout as needed)
            wait = WebDriverWait(driver, 20)

            # Wait until at least one of the target div elements is visible
            wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "row.mb-2.ng-star-inserted")))

            # Find all matching elements
            div_elements = driver.find_elements(By.CLASS_NAME, "row.mb-2.ng-star-inserted")

            # Extract serial numbers from the <span> inside each div
            all_serial_numbers = []
            for div in div_elements:
                try:
                    # Find the span inside the div
                    span_element = div.find_element(By.TAG_NAME, "span")
                    all_serial_numbers.append(span_element.text)
                except Exception as e:
                    # Handle any exceptions (e.g., span not found)
                    print(f"Error processing a div: {e}")

            for serial_number in all_serial_numbers:
                # Find the first result card with the clickable span inside it
                new_url = f"https://tsdr.uspto.gov/#caseNumber={serial_number}&caseSearchType=US_APPLICATION&caseType=DEFAULT&searchType=statusSearch"
                driver.get(new_url)
                print(f"{serial_number} card clicked successfully!")
                time.sleep(5)

                # Extract Date Abandoned
                try:
                    abandoned_date_div = WebDriverWait(driver, 20).until(
                        EC.visibility_of_element_located((By.XPATH, "/html/body/div[5]/div[4]/div[6]/div[3]/ul/li[1]/div[1]/div[2]/div/div[2]"))
                    )
                    abandoned_date = abandoned_date_div.text
                except Exception:
                    abandoned_date = None

                # Extract Mark Text
                try:
                    value_mark_text_div = WebDriverWait(driver, 20).until(
                        EC.visibility_of_element_located((By.XPATH, "/html/body/div[5]/div[4]/div[6]/div[3]/ul/li[1]/div[1]/div[1]/div[2]/div/div[2]"))
                    )
                    mark_text = value_mark_text_div.text
                except Exception:
                    mark_text = None

                # Step 3: Click the "Attorney/Correspondence Information" dropdown
                attorney_info_dropdown = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[@data-sectiontitle='Attorney/Correspondence Information']/a[@class='sectionLink']"))
                )
                attorney_info_dropdown.click()
                print("Attorney/Correspondence Information dropdown clicked successfully!")

                # Step 4: Extract Phone from the Correspondence Information
                try:
                    phone_div = WebDriverWait(driver, 20).until(
                        EC.visibility_of_element_located((By.XPATH, "//div[@class='row']//div[@class='key' and text()='Phone:']/following-sibling::div[@class='value']"))
                    )
                    phone = phone_div.text
                    print(f"Phone: {phone}")
                except Exception:
                    phone = None

                # Step 5: Extract Email from the Correspondence Information
                try:
                    email_div = WebDriverWait(driver, 20).until(
                        EC.visibility_of_element_located((By.XPATH, "//div[@class='row']//div[@class='key' and text()='Correspondent e-mail:']/following-sibling::div[@class='value']/a"))
                    )
                    email = email_div.text
                    print(f"Email: {email}")
                except Exception:
                    email = None    

                # Step 6: Click on Documents tab
                documents_tab = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, "/html/body/div[5]/div[4]/div[6]/div[2]/ul/li[2]/a"))
                )
                documents_tab.click()
                print("Documents tab clicked successfully!") 

                # Locate the anchor tag using XPath
                try:
                    anchor_element = WebDriverWait(driver, 20).until(
                        EC.visibility_of_element_located((By.XPATH, '/html/body/div[5]/div[4]/div[6]/div[3]/ul/li[2]/div[2]/div[1]/div[2]/table/tbody/tr[2]/td[3]/a'))
                    )
                    # Extract the href attribute
                    href_value = anchor_element.get_attribute('href')
                    print(">>>>", href_value)
                    if href_value:
                        driver.get(href_value)
                        time.sleep(5)

                        # Wait for the dropdown button to be visible and clickable
                        wait = WebDriverWait(driver, 10)
                        dropdown_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "ui-multiselect")))

                        # Click the dropdown button to expand the options
                        dropdown_button.click()

                        # Wait for the dropdown options to be present
                        try:
                            dropdown_options = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//li")))

                            # Check for the desired option
                            option_found = False
                            for index, option in enumerate(dropdown_options):
                                if "TEAS Plus New Application" in option.text:
                                    option.click()
                                    option_found = True
                                    print(f"Option 'TEAS Plus New Application' selected at index {index}.")
                                    time.sleep(5)
                                    # Get the current URL from the browser's address bar
                                    current_url = driver.current_url
                                    print("Current URL: ", current_url)

                                    try:
                                        driver.get(current_url)
                                        print("Navigated to the current URL for the search!")
                                        time.sleep(5)

                                        iframe = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'docPage')))
                                        iframe_src = iframe.get_attribute('src')
                                        print("Iframe Source:", iframe_src)

                                        driver.get(iframe_src)
                                        print("Navigated to the iframe URL for the search!")
                                        
                                        time.sleep(5)
                                        # Retrieve the page source
                                        html_source = driver.page_source

                                        # Parse the HTML using BeautifulSoup
                                        soup_document = BeautifulSoup(html_source, 'html.parser')

                                        # Find the table with the ID 'inputTable'
                                        input_table = soup_document.find('table', id='inputTable')

                                        # If the table is found, you can proceed with extracting data
                                        if input_table:
                                            # Print the entire HTML content of the inputTable (you can inspect this as needed)
                                            # print(input_table.prettify())

                                            # Extract the signatory name and phone using appropriate CSS selectors or XPath logic
                                            try:
                                                # Extract the signatory name (adjust the selector to match your HTML structure)
                                                signatory_name = input_table.select_one("th[id='signatoryname-sign'] + td").text.strip()
                                                print("Signatory's Name:", signatory_name)

                                                # Extract signatory's position
                                                signatory_position = input_table.select_one("th[id='sign-position-sign'] + td").text.strip()
                                                print("Signatory's Position:", signatory_position)

                                                # Extract signatory's phone number
                                                # Use the position in the hierarchy to differentiate between the same id for phone and position
                                                signatory_phone = input_table.select("th[id='sign-position-sign'] + td")[1].text.strip()
                                                print("Signatory's Phone Number:", signatory_phone)
                                                
                                                # Locate the signatory phone using the appropriate XPath or CSS selector
                                                signatory_phone_1 = WebDriverWait(driver, 10).until(
                                                    EC.visibility_of_element_located((By.XPATH, "/html/body/div[2]/table/tbody/tr[62]/td"))
                                                )
                                                signatory_phone_1 = signatory_phone_1.text.strip()
                                                print("Signatory's Phone:", signatory_phone_1)
                                            except Exception as e:
                                                print("Error extracting data:", e)
                                        else:
                                            print("Table with ID 'inputTable' not found.")

                                    except Exception:
                                        signatory_name = None
                                        signatory_position = None
                                        signatory_phone = None
                                        signatory_phone_1 = None

                            if not option_found:
                                print("Option 'TEAS Plus New Application' not found. Moving to the next step.")

                        except Exception as e:
                            print(f"An error occurred while handling the dropdown: {e}")

                except Exception:
                    href_value = None

                # Store data
                data.append({
                    "Serial Number": serial_number,
                    "Date Abandoned": abandoned_date,
                    "Mark Text": mark_text,
                    "email": email,
                    "phone": phone,
                    "Signatory Name": signatory_name,
                    "Signatory Position": signatory_position,
                    "Signatory Phone": signatory_phone,
                    "Signatory Phone 1": signatory_phone_1,
                })
                # print(data)

                # Reset all variables to None at the start of each loop iteration
                abandoned_date = None
                mark_text = None
                phone = None
                email = None
                signatory_name = None
                signatory_position = None
                signatory_phone = None
                signatory_phone_1 = None
            print("Total result cards: ", len(all_serial_numbers))   

    except Exception as e:
        print("Error occurred:", e)

    finally:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Save data to DataFrame
        df = pd.DataFrame(data)
        # Save DataFrame to MongoDB
        collection.insert_many(df.to_dict("records"))
        print(f"Data inserted into MongoDB collection '{collection.name}' successfully!")

        driver.get("https://tmsearch.uspto.gov/search/search-information")
        counter += 1

        # Close the browser
        # driver.quit()