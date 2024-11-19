# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from stem import Signal
from stem.control import Controller
from bs4 import BeautifulSoup
import time
import random
import urllib.parse
from scrapy.crawler import CrawlerProcess
from scrapy.spiders import Spider
# You may implement anti-captcha stuff
# If site to scrapp has a geoloation blockade, then program may fail. Eg. in Europe most of a tor connections are from Germany

# Tor identify  Mr Maaagic, take a token
def renew_tor_identity():
    with Controller.from_port(port=9051) as controller:
        controller.authenticate()
        controller.signal(Signal.NEWNYM)

# Selenium
def fetch_links(query, start_date, end_date, driver):
    date_filter = ""
    if start_date and end_date:
        date_filter = f"&df={start_date}..{end_date}"
    
    # DuckDuckGo syntax
    url = f"https://duckduckgo.com/?q={urllib.parse.quote(query)}{date_filter}&ia=web"
    
    renew_tor_identity()
    driver.get(url)
    
    links = []
    while True:
        time.sleep(random.uniform(3, 7))
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        results = soup.find_all('a', href=True)
        if not results:
            break
        
        for result in results:
            href = result['href']
            if 'http' in href:
                links.append(href)
        
        try:
            more_button = driver.find_element("id", "more-results")  # If you use DuckDuckGo in another language, locate the button for loading more results
            more_button.click()
        except:
            break

    return links

# Spider (separate file)
class PageSpider(Spider):
    name = "page_spider"
    
    def __init__(self, *args, **kwargs):
        super(PageSpider, self).__init__(*args, **kwargs)
        self.start_urls = kwargs.get('start_urls', [])
    
    def parse(self, response):
        paragraphs = response.css('p::text').getall()
        clean_text = " ".join(paragraph.strip() for paragraph in paragraphs)
        
        yield {
            'text': clean_text,  # Cleared text. More functions are in BeautifulSoup
        }

# Main execution block
if __name__ == "__main__":
    phrase = input("Insert a phrase to search: ")
    title_phrase = input("Enter the phrase you want in the headline (optional, press Enter to skip): ")  # Not recommended, usually very few results
    start_date = input("Enter the start date (YYYY-MM-DD, optional, press Enter to skip): ")
    end_date = input("Enter the end date (YYYY-MM-DD, optional, press Enter to skip): ")

    # Pages to scrape. Change manually or add a GUI.
    site_list = [
        "example.com"
    ]

    # Selenium+Tor configuration
    options = Options()
    options.headless = True

    profile = webdriver.FirefoxProfile()
    profile.set_preference("network.proxy.type", 1)
    profile.set_preference("network.proxy.socks", "127.0.0.1")
    profile.set_preference("network.proxy.socks_port", 9050)
    profile.set_preference("network.proxy.socks_version", 5)
    profile.set_preference("places.history.enabled", False)
    profile.set_preference("privacy.clearOnShutdown.offlineApps", True)
    profile.set_preference("privacy.clearOnShutdown.passwords", True)
    profile.set_preference("privacy.clearOnShutdown.siteSettings", True)
    profile.set_preference("privacy.sanitize.sanitizeOnShutdown", True)
    profile.set_preference("dom.webdriver.enabled", False)
    profile.set_preference('useAutomationExtension', False)
    options.profile = profile

    driver = webdriver.Firefox(options=options)

    links = []
    for site in site_list:
        query = f"{phrase} site:{site}"
        if title_phrase:
            query += f" intitle:{title_phrase}"

        links.extend(fetch_links(query, start_date, end_date, driver))

    if not links:
        print("No results")
    else:
        # Scrapy
        process = CrawlerProcess(settings={
            "FEEDS": {
                "results.json": {"format": "json"},
            },
            "FEED_EXPORT_ENCODING": "utf-8",
        })

        process.crawl(PageSpider, start_urls=links)
        process.start()

    driver.quit()
