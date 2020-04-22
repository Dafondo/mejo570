import scrapy
from scrapy.loader import ItemLoader
import json
from datetime import datetime
import re
import csv
from urllib.parse import parse_qs, urljoin, urlparse
from senate2018.items import Senate2018Item


class ReceiptsSpider(scrapy.Spider):
    name = "receipts"

    # Used to translate Report Types to shortened file names
    fileNameSwitch = {
        'First Quarter': 'q1',
        'Second Quarter': 'q2',
        'Third Quarter': 'q3',
        'Fourth Quarter': 'q4',
        'Final': 'q4'
    }

    # Converts a Report Type into a shortened file name
    # Returns a shortened file name
    def reportToFileName(self, report):
        return self.fileNameSwitch.get(report, lambda: "Invalid report type")

    # Initializes the spider with arguments
    # Accepts arguments for csv file path and project folder name
    def __init__(self, csv="urls.csv", proj="senate2018", * args, **kwargs):
        self.csvPath = csv
        self.projectName = proj
        super(ReceiptsSpider, self).__init__(*args, **kwargs)

    # Creates the Request objects to parse
    # Expects a csv file from which to read request parameters including urls
    # Returns a list of scrapy Request objects to parse
    def start_requests(self):
        pages = []
        with open(self.csvPath, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            self.fieldnames = reader.fieldnames
            for row in reader:
                url = row["url"]
                if url:
                    # Sets the fields in the csv as meta attributes that are passed to the request
                    # Meta attribute names are the same as the csv header names
                    meta = {}
                    for f in reader.fieldnames:
                        meta[f] = row[f]
                    page = scrapy.Request(url, callback=self.parse, meta=meta)
                    pages.append(page)

        return pages

    # Topmost parse function
    # Gets the page urls for quarterly disclosure reports
    def parse(self, response):
        # Initializes our reports as None
        quarterReports = {
            'q1': None,
            'q2': None,
            'q3': None,
            'q4': None,
        }

        # Looks for the table data which is hardcoded in a script tag at the bottom of the HTML page
        pattern = r'data = (.*)'
        data = response.css('script::text').re_first(pattern)
        # Load the data as a JSON array
        reportsArray = json.loads(data)

        for item in reportsArray:
            # Checks for Disclosure Reports that are quarterly or final reports, also checks that it has a Data Link to download
            if item['DocumentType'] == 'Disclosure Report' and item['DataLink'] and item['ReportType'] in self.fileNameSwitch:
                # Grabs the start and end years
                startdate = item['PeriodStartDate']
                enddate = item['PeriodEndDate']
                startyear = datetime.strptime(startdate, '%m/%d/%Y').year
                endyear = datetime.strptime(enddate, '%m/%d/%Y').year

                # If found, save the rows as objects
                # TODO allow the user to pass in a year
                if item['ReportType'] == 'First Quarter' and endyear == 2018:
                    quarterReports['q1'] = quarterReports['q1'] if quarterReports['q1'] else item
                elif item['ReportType'] == 'Second Quarter' and startyear == 2018 and endyear == 2018:
                    quarterReports['q2'] = quarterReports['q2'] if quarterReports['q2'] else item
                elif item['ReportType'] == 'Third Quarter' and startyear == 2018 and endyear == 2018:
                    quarterReports['q3'] = quarterReports['q3'] if quarterReports['q3'] else item
                elif item['ReportType'] == 'Fourth Quarter' and startyear == 2018:
                    quarterReports['q4'] = quarterReports['q4'] if quarterReports['q4'] else item
                elif item['ReportType'] == 'Final' and startyear == 2018 and endyear == 2018:
                    quarterReports['q4'] = quarterReports['q4'] if quarterReports['q4'] else item

        for key in quarterReports:
            report = quarterReports[key]
            if report:
                # Create the URL for the Report summary page for each quarterly report
                # The URL is not relative to the current URL, so we must craft it from scratch
                reportUrl = 'https://cf.ncsbe.gov/CFOrgLkup/ReportSection/?RID=' + \
                    str(report['DataLink']) \
                    + '&SID=' + report['SBoEID'] \
                    + '&CN=' + report['CommitteeName'] \
                    + '&RN=' + str(report['ReportYear']) + \
                    ' ' + report['ReportType']

                # Call the second parse function and pass some meta attributes
                yield scrapy.Request(reportUrl, callback=self.parse_report_summary,
                                     meta={'fileName': self.reportToFileName(report['ReportType']), 'basePath': 'data/%s/%s/%s/' % (self.projectName, response.meta.get('district'), str.lower(response.meta.get('lastname')))})

    # Second parse function
    # Parses the Report summary pages for the Detailed Receipts row and grabs the view link
    def parse_report_summary(self, response):
        # Looks for the table data which is hardcoded in a script tag at the bottom of the HTML page
        pattern = r'data = (.*)'
        data = response.css('script::text').re_first(pattern)
        # Load the data as a JSON array
        docsArray = json.loads(data)

        # Grabs the RID url parameter which is needed for the Report table view URL
        # The URL is not relative to the current url, so we must craft it from scratch
        parsedUrl = urlparse(response.url)
        rid = parse_qs(parsedUrl.query)['RID'][0]
        urlBase = 'https://cf.ncsbe.gov/CFOrgLkup/ReportDetail/?RID=' + rid

        for doc in docsArray:
            # Checks to make sure receipts exist
            if doc['SectionName'] == 'Detailed Receipts' and doc['Count'] > 0:
                # Adds the TP parameter to our base link
                viewUrl = urlBase + '&TP=' + doc['Link']
                yield scrapy.Request(viewUrl, callback=self.parse_report_view,
                                     meta=response.meta)

    # Third parse function
    # Finds the CSV download link on the Report table view page
    # Adds CSV download link to our file pipeline
    def parse_report_view(self, response):
        # Gets the base URL of the site which is needed to create the CSV download URL
        parsedUri = urlparse(response.url)
        baseUrl = '{uri.scheme}://{uri.netloc}/'.format(uri=parsedUri)
        # Finds the relative URL of the CSV file and joins it to the base URL
        relativeUrl = response.xpath(
            "//a[contains(text(), 'Export data to .CSV')]//@href").get()
        csvUrl = urljoin(baseUrl, relativeUrl)

        # Add the CSV download URL to the file pipeline and pass some arguments
        loader = ItemLoader(item=Senate2018Item(), selector=csvUrl)
        loader.add_value('file_urls', csvUrl)
        loader.add_value('fileName', response.meta.get('fileName'))
        loader.add_value('basePath', response.meta.get('basePath'))
        yield loader.load_item()
