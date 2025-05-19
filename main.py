import os
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

# Set up Selenium Edge browser
options = Options()
#options.add_argument("--headless")  # Run in headless mode (no browser UI)
driver = webdriver.Edge(options=options)

def get_property_links(city, pages=2):  # Adjust number of pages as needed
    all_data = []
    for i in range(1, pages + 1):
        url = f"https://www.magicbricks.com/property-for-sale/residential-real-estate?bedroom=2,3&proptype=Multistorey-Apartment,Builder-Floor-Apartment,Penthouse,Studio-Apartment,Residential-House,Villa&cityName={city}&page={i}"
        print(f"Scraping page {i}: {url}")
        driver.get(url)
        time.sleep(5)
        all_data.extend(extract_property_data_from_cards(driver))
    return all_data

def extract_property_data_from_cards(driver):
    data = []
    cards = driver.find_elements(By.CLASS_NAME, "mb-srp__list")

    for idx, card in enumerate(cards):
        # Scroll the card into view to trigger lazy-loading
        driver.execute_script("arguments[0].scrollIntoView(true);", card)
        time.sleep(1)

        # Hover to ensure images load
        try:
            image_block = card.find_element(By.CLASS_NAME, "swiper-wrapper")
            ActionChains(driver).move_to_element(image_block).perform()
            time.sleep(1)
        except:
            pass

        soup = BeautifulSoup(card.get_attribute("outerHTML"), "html.parser")

        try:
            title = soup.find("h2", class_="mb-srp__card--title").get_text(strip=True)
        except:
            title = None

        try:
            developer = soup.find("a", class_="mb-srp__card__developer--name").get_text(strip=True)
        except:
            developer = None

        summary = soup.find_all("div", class_="mb-srp__card__summary__list--item")
        summary_data = {}
        for item in summary:
            try:
                label = item.find("div", class_="mb-srp__card__summary--label").get_text(strip=True)
                value = item.find("div", class_="mb-srp__card__summary--value").get_text(strip=True)
                summary_data[label] = value
            except:
                continue

        try:
            price = soup.find("div", class_="mb-srp__card__price--amount").get_text(strip=True)
        except:
            price = None

        try:
            desc = soup.find("div", class_="mb-srp__card--desc-lux--text").get_text(strip=True)
        except:
            desc = None

        try:
            builder_name = soup.find("div", class_="mb-srp__card__ads--name").get_text(strip=True)
        except:
            builder_name = None

        try:
            operating_since = soup.find("div", class_="mb-srp__card__ads--since").get_text(strip=True)
        except:
            operating_since = None

        # ✅ Extract real image URLs
        try:
            image_tags = soup.select(".swiper-slide img")
            image_urls = [img['src'] for img in image_tags if img.get('src') and 'staticmb.com' in img['src']]
            image1 = image_urls[0] if len(image_urls) > 0 else None
            image2 = image_urls[1] if len(image_urls) > 1 else None
            image3 = image_urls[2] if len(image_urls) > 2 else None
        except:
            image1 = image2 = image3 = None

        try:
            tags_div = soup.find("div", class_="mb-srp__card__tags")
            tags = [tag.get_text(strip=True) for tag in tags_div.find_all("span")]
        except:
            tags = []

        try:
            amenities_div = soup.find("ul", class_="mb-srp__card__accomodation")
            amenities = [li.get_text(strip=True) for li in amenities_div.find_all("li")]
        except:
            amenities = []
        # ✅ Extract Free Cab Info
        try:
            free_cab_text = soup.find("div", class_="mb-srp__freecab__txt").get_text(strip=True)
        except:
            free_cab_text = None


        data.append({
            "Title": title,
            "Developer": developer,
            "Super Area": summary_data.get("Super Area"),
            "Status": summary_data.get("Under Construction"),
            "Transaction": summary_data.get("Transaction"),
            "Furnishing": summary_data.get("Furnishing"),
            "Parking": summary_data.get("Car Parking"),
            "Bathroom": summary_data.get("Bathroom"),
            "Balcony": summary_data.get("Balcony"),
            "Price": price,
            "Description": desc,
            "Builder Name": builder_name,
            "Operating Since": operating_since,
            "Tags": ", ".join(tags),
            "Amenities": ", ".join(amenities),
            "Free Cab Info": free_cab_text,
            "Image 1": image1,
            "Image 2": image2,
            "Image 3": image3

        })

    return data

def extract_possession(card):
    possession_info = card.find('div', class_='srpPosession')
    if possession_info:
        return possession_info.text.strip().replace("Possession by", "").strip()
    return ""

# Scrape data
city = "Chennai"
results = get_property_links(city, pages=1)

# Save to Excel
df = pd.DataFrame(results)
df.to_excel("properties.xlsx", index=False)
print("✅ Data saved to properties.xlsx")

# Close browser
driver.quit()
