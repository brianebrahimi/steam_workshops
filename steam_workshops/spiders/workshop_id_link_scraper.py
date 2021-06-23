import scrapy
import re
from scrapy.spiders import Rule, CrawlSpider
from scrapy.linkextractors import LinkExtractor


class Workshop_Spider(scrapy.Spider):
	name = 'workshops'
	
	base_workshop_link = "https://steamcommunity.com/workshop/browse/?appid=289070&browsesort=trend&section=readytouseitems&days=90&actualsort=trend&p="
	links = []
	for x in range(1, 165):
		links.append(base_workshop_link + str(x))

	start_urls = links


	def parse(self, response):
		page = response.css("a::attr(href)").re(r'https://steamcommunity.com/sharedfiles/filedetails/\?id=[0-9]*&searchtext=')
		set_of_links = set()
		for link in page:
			set_of_links.add(link)

		with open("output/workshop.txt", "a") as f:
			for link in set_of_links:
				f.write(link + "\n")



