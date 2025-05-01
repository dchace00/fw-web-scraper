import requests
from bs4 import BeautifulSoup
import argparse

class ScraperError(Exception):
    """Base class for scraper-related errors."""
    pass

class URLFetchError(ScraperError):
    """Raised when the URL request fails."""
    def __init__(self, url, status_code):
        self.url = url
        self.status_code = status_code
        super().__init__(f"Error {status_code}: Unable to fetch {url}")

def scrape_project_data(url):
    """Scrape project details from a Farnsworth Group project detail page."""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            raise URLFetchError(url, response.status_code)
    except requests.exceptions.RequestException as e:
        raise URLFetchError(url, "Unknown Error") from e

    soup = BeautifulSoup(response.text, 'html.parser')

    project_data = {
        "Project Name": None,
        "Client Name": None,
        "Location": None,
        "Capabilities": [],
        "Markets": []
    }

    for dt in soup.select("dl.specs dt"):
        label = dt.get_text(strip=True)
        dd = dt.find_next_sibling("dd")

        if label == "Project Name":
            project_data["Project Name"] = dd.get_text(strip=True)
        elif label == "Client Name":
            project_data["Client Name"] = dd.get_text(strip=True)
        elif label == "Location":
            addr_tag = dd.find("p", class_="address")
            project_data["Location"] = addr_tag.get_text(strip=True) if addr_tag else dd.get_text(strip=True)
        elif label == "Capabilities":
            project_data["Capabilities"] = [a.get_text(strip=True) for a in dd.select("li a")]
        elif label == "Markets":
            project_data["Markets"] = [a.get_text(strip=True) for a in dd.select("li a")]

    return project_data

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Web scraper for Farnsworth Group project data.")
    parser.add_argument("url", type=str, help="The full URL of the project page to scrape.")
    args = parser.parse_args()

    try:
        data = scrape_project_data(args.url)
        print(data)
    except URLFetchError as e:
        print(f"Error: {e}")