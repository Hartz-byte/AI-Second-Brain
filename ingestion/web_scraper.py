import requests
from bs4 import BeautifulSoup

def scrape_article(url):

    r = requests.get(url)

    soup = BeautifulSoup(r.text, "html.parser")

    paragraphs = soup.find_all("p")

    text = " ".join([p.get_text() for p in paragraphs])

    return text
