import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import os

def get_content_text(url):
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        content_div = soup.find('div', id='content')
        sidebar_div = soup.find('div', id='sidebar-first')

        if not content_div:
            print(f"❌ No <div id='content'> found in {url}")
            return "", []
        
        if not sidebar_div:
            print(f"❌ No <div id='sidebar'> found in {url}")

        text = content_div.get_text(separator='\n', strip=True)

        content_links = content_div.find_all('a', href=True)
        sidebar_links = sidebar_div.find_all('a', href=True) if sidebar_div else []

        links = [urljoin(url, a['href']) for a in content_links + sidebar_links]
        
        return text, links

    except Exception as e:
        print(f"❌ Failed to fetch {url}: {e}")
        return "", []

def crawl_from_root(root_url, domain_limit=True, file_limit=100):
    visited = set()
    to_visit = [root_url]
    files = 0

    while to_visit and files < file_limit:
        current_url = to_visit.pop(0)
        if current_url in visited:
            continue

        visited.add(current_url)
        print(f"Visiting: {current_url}")

        text, links = get_content_text(current_url)

        # print(f"✅ Extracted {len(text)} characters from {current_url}")
        save_page_text(current_url, text)
        files = files + 1

        for link in links:
            full_url = urljoin(current_url, link)

            if domain_limit:
                if urlparse(full_url).netloc != urlparse(root_url).netloc:
                    continue

            if full_url not in visited:
                to_visit.append(full_url)

os.makedirs("mosdac_scraped", exist_ok=True)

import re

def make_safe_filename(url):
    name = url.replace("https://", "").replace("http://", "")
    name = re.sub(r'[<>:"/\\|?*#=]', '_', name)
    return name[:150]

def save_page_text(url, text):
    safe_name = make_safe_filename(url)
    filename = f"mosdac_scraped/{safe_name}.json"

    data = {
        "url": url,
        "text": text
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"💾 Saved: {filename}")

crawl_from_root("https://mosdac.gov.in/sitemap")

# text, link = get_content_text("https://mosdac.gov.in/insat-3dr")

# print(link)