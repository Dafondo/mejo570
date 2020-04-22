# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.pipelines.files import FilesPipeline
from scrapy import Request


class Senate2018Pipeline(FilesPipeline):
    # Passes file name and download path arguments to the file_path function
    def get_media_requests(self, item, info):
        return [Request(x, meta={'fileName': item.get('fileName')[0], 'basePath': item.get('basePath')[0]}) for x in item.get(self.files_urls_field, [])]

    # Saves the file to the location specified by our fields
    def file_path(self, request, response=None, info=None):
        return '%s%s' % (request.meta.get('basePath'), request.meta.get('fileName'))
