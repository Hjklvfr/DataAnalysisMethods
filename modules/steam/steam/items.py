import logging
from datetime import datetime, date

from itemloaders.processors import TakeFirst, MapCompose, Compose
from scrapy.item import Item, Field
from scrapy.loader import ItemLoader

logger = logging.getLogger(__name__)


class StripText:
    def __init__(self, chars=' \r\t\n'):
        self.chars = chars

    def __call__(self, value):
        try:
            return value.strip(self.chars)
        except:  # noqa E722
            return value


def standardize_date(x):
    fmt_fail = False
    for fmt in ['%d %b, %Y', '%B %d, %Y']:
        try:
            return datetime.strptime(x, fmt).strftime('%Y-%m-%d')
        except ValueError:
            fmt_fail = True

    for fmt in ['%b %d', '%B %d']:
        try:
            d = datetime.strptime(x, fmt)
            d = d.replace(year=date.today().year)
            return d.strftime('%Y-%m-%d')
        except ValueError:
            fmt_fail = True

    if fmt_fail:
        logger.debug(f'Could not process date {x}')

    return x


class ProductItemLoader(ItemLoader):
    default_output_processor = Compose(TakeFirst(), StripText())


class ProductItem(Item):
    _id = Field()
    title = Field()
    release_date = Field(
        output_processor=Compose(
            TakeFirst(),
            StripText(),
            standardize_date
        ))
    developer = Field()
    publisher = Field()
    tags = Field(output_processor=MapCompose(StripText()))
    pass
