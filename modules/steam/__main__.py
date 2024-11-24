from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from modules.steam.steam.spiders import SteamSpider

if __name__ == '__main__':
    process = CrawlerProcess(get_project_settings())
    process.crawl(SteamSpider)
    process.start()
