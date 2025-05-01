import requests
from bs4 import BeautifulSoup

def scrape_project_data(url):
    """
    Scrape project details from a Farnsworth Group project detail page.

    Parameters:
    - url (str): Full URL of the Farnsworth Group project page.

    Returns:
    - dict: A dictionary containing the extracted project details:
        - 'Project Name' (str)
        - 'Client Name' (str)
        - 'Location' (str)
        - 'Capabilities' (list of str)
        - 'Markets' (list of str)
    """

    # Send GET request to the project page
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch page: {url}")

    # Parse the page content
    soup = BeautifulSoup(response.text, 'html.parser')

    # Initialize result dictionary
    project_data = {
        "Project Name": None,
        "Client Name": None,
        "Location": None,
        "Capabilities": [],
        "Markets": []
    }

    # Find all definition list entries
    for dt in soup.select("dl.specs dt"):
        label = dt.get_text(strip=True)
        dd = dt.find_next_sibling("dd")

        # Match and extract each expected field
        if label == "Project Name":
            project_data["Project Name"] = dd.get_text(strip=True)
        elif label == "Client Name":
            project_data["Client Name"] = dd.get_text(strip=True)
        elif label == "Location":
            # Some locations are inside <p class="address">
            addr_tag = dd.find("p", class_="address")
            project_data["Location"] = addr_tag.get_text(strip=True) if addr_tag else dd.get_text(strip=True)
        elif label == "Capabilities":
            project_data["Capabilities"] = [a.get_text(strip=True) for a in dd.select("li a")]
        elif label == "Markets":
            project_data["Markets"] = [a.get_text(strip=True) for a in dd.select("li a")]

    return project_data

url = "https://www.f-w.com/projects/multi-purpose-meeting-facility-adds-flexibility-to-campus"
data = scrape_project_data(url)
print(data)