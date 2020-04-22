# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader.processors import MapCompose

# Adds the CSV extension to our files
def addExtension(value):
    return value + '.csv'

class Senate2018Item(scrapy.Item):
    # Required fields
    file_urls = scrapy.Field()
    files = scrapy.Field()

    # Stores the name of our file
    fileName = scrapy.Field(
        input_processor = MapCompose(addExtension),
    )

    # Stores the relative path to our file
    basePath = scrapy.Field()