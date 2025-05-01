import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import csv
import os

# ---------- CONFIG ----------
BASE_URL = "https://www.f-w.com"
PROJECT_LISTING_URL = f"{BASE_URL}/projects"
OUTPUT_CSV = "output/farnsworth_projects_data.csv"
# ----------------------------

class ScraperError(Exception): pass
class URLFetchError(ScraperError):
    def __init__(self, url, status_code):
        self.url = url
        self.status_code = status_code
        super().__init__(f"Error {status_code}: Unable to fetch {url}")

def extract_thumbnail(soup):
    tag = soup.select_one('.hero-image__slide img')
    if tag and 'src' in tag.attrs:
        src = tag['src']
        return BASE_URL + src if src.startswith("/") else src
    return None

def scrape_project_data(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            raise URLFetchError(url, response.status_code)
    except requests.exceptions.RequestException:
        raise URLFetchError(url, "Unknown Error")

    soup = BeautifulSoup(response.text, 'html.parser')
    data = {
        "Project Name": None,
        "Client Name": None,
        "Location": None,
        "Capabilities": [],
        "Markets": [],
        "Thumbnail": extract_thumbnail(soup),
        "URL": url
    }

    for dt in soup.select("dl.specs dt"):
        label = dt.get_text(strip=True)
        dd = dt.find_next_sibling("dd")

        if label == "Project Name":
            data["Project Name"] = dd.get_text(strip=True)
        elif label == "Client Name":
            data["Client Name"] = dd.get_text(strip=True)
        elif label == "Location":
            addr_tag = dd.find("p", class_="address")
            data["Location"] = addr_tag.get_text(strip=True) if addr_tag else dd.get_text(strip=True)
        elif label == "Capabilities":
            data["Capabilities"] = [a.get_text(strip=True) for a in dd.select("li a")]
        elif label == "Markets":
            data["Markets"] = [a.get_text(strip=True) for a in dd.select("li a")]

    return data

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_all_project_links():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)
    driver.get(PROJECT_LISTING_URL)
    wait = WebDriverWait(driver, 10)

    # Click all "Load More" <a> links until they disappear
    while True:
        try:
            load_more_link = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'load more')]")
            ))
            print("Clicking 'Load More' link...")
            driver.execute_script("arguments[0].click();", load_more_link)
            time.sleep(2.5)
        except Exception as e:
            print("No more 'Load More' links or timeout reached.")
            break

    # Collect project page links
    elements = driver.find_elements(By.XPATH, "//a[contains(@href, '/projects/')]")
    links = set()
    for elem in elements:
        href = elem.get_attribute("href")
        if href and '/projects/' in href and not href.rstrip("/").endswith("/projects"):
            links.add(href)

    print(f"✅ Collected {len(links)} unique project URLs.")
    driver.quit()
    return sorted(links)




def main():
    print("Collecting project links...")
    links = get_all_project_links()
    print(f"Found {len(links)} project pages.")

    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    with open(OUTPUT_CSV, "w", newline='', encoding='utf-8') as csvfile:
        fieldnames = ["Project Name", "Client Name", "Location", "Capabilities", "Markets", "Thumbnail", "URL"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for i, url in enumerate(links, 1):
            try:
                data = scrape_project_data(url)
                writer.writerow({
                    **data,
                    "Capabilities": ", ".join(data["Capabilities"]),
                    "Markets": ", ".join(data["Markets"])
                })
                print(f"[{i}/{len(links)}] Scraped: {data['Project Name']}")
            except Exception as e:
                print(f"[{i}/{len(links)}] Failed on {url}: {e}")

if __name__ == "__main__":
    main()
