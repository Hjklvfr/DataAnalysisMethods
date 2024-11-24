import logging
import re

from scrapy.http import FormRequest
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from ..items import ProductItem, ProductItemLoader

logger = logging.getLogger(__name__)


def load_product(response):
    loader = ProductItemLoader(item=ProductItem(), response=response)

    found_id = re.findall('/app/(.*?)/', response.url)
    if found_id:
        id = found_id[0]
        loader.add_value('_id', id)

    try:
        details = response.xpath("//div[@class='app_header_grid_container']")

        loader.add_value('developer', details.xpath(
            "//div[contains(text(), 'Developer')]/following-sibling::div[@class='grid_content']/a/text()").get())
        loader.add_value('publisher', details.xpath(
            "//div[contains(text(), 'Publisher')]/following-sibling::div[@class='grid_content']/a/text()").get())
        loader.add_value('release_date', details.xpath(
            "//div[contains(text(), 'Release Date:')]/following-sibling::div[@class='date']/text()").get())

    except:  # noqa E722
        pass

    loader.add_css('title', '.apphub_AppName ::text')
    loader.add_css('tags', 'a.app_tag::text')

    return loader.load_item()


class SteamSpider(CrawlSpider):
    name = "steam"
    allowed_domains = ["store.steampowered.com"]
    start_urls = [
        "https://store.steampowered.com/search/?sort_by=&sort_order=0&filter=topsellers&supportedlang=english&page=1"]

    rules = [
        Rule(LinkExtractor(
            allow='/app/(.+)/'),
            callback='parse_product'),
        Rule(LinkExtractor(
            allow='page=(\d+)',
            restrict_xpaths="//a[@class='pagebtn' and contains(text(), '>')]"))
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def parse_product(self, response):
        if '/agecheck/app' in response.url:
            logger.debug(f'Form-type age check triggered for {response.url}.')

            form = response.css('#agegate_box form')

            action = form.xpath('@action').extract_first()
            name = form.xpath('input/@name').extract_first()
            value = form.xpath('input/@value').extract_first()

            form_data = {
                name: value,
                'ageDay': '1',
                'ageMonth': '1',
                'ageYear': '1955'
            }

            yield FormRequest(
                url=action,
                method='POST',
                formdata=form_data,
                callback=self.parse_product
            )

        else:
            yield load_product(response)
