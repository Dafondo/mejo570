# Receipts Scraper
This scraper downloads receipts from quarterly disclosure reports for political campaigns from the NC State Board of Elections.

## How to Run:
1. Download Python 3
1. Enter the `senate2018` directory: `cd senate2018`
1. (optional, recommended) Create and activate a virtual environment
1. Install from `requirements.txt`: `pip3 install -r requirements.txt`
1. Run `scrapy crawl receipts -a csv=INPUT_CSV_PATH -a proj=PROJECT_NAME`
    1. The `csv` arg tells scrapy where to find the input csv described later on
    1. The `proj` arg tells scrapy what subdirectory to save downloaded files to
    1. If you don't provide `csv` or `proj` arguments, their default values (`urls.csv` and `senate2018`) will be used
1. Look in `/python/data` for the downloaded files

## CSV input file
This file should have the following fields:
- `district`
- `name`
    - The files will be saved under `/python/data/PROJECT_NAME/district/name/`
- `url`: The NCSBE page listing all the available documents for a candidate