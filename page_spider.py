import scrapy
import json

class PageSpider(scrapy.Spider):
    name = 'page_spider'
    
    def start_requests(self):
        with open('links.json', 'r') as f:
            links = json.load(f)
        
        for link in links:
            yield scrapy.Request(url=link, callback=self.parse)
    
    def parse(self, response):
        # Przetwarzanie treści strony
        title = response.xpath('//title/text()').get()
        body = response.xpath('//body//text()').getall()
        
        yield {
            'url': response.url,
            'title': title,
            'body': ' '.join(body),
        }
