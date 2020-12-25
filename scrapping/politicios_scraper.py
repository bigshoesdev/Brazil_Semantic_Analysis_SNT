import json
import datetime
import time
from config import config

try:
    from urllib.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen, Request

connection = config.initdb()

db = connection.scope_db
record1 = db.politicios


def request_until_succeed(url):
    req = Request(url)
    success = False
    while success is False:
        try:
            response = urlopen(req)
            if response.getcode() == 200:
                success = True
        except Exception as e:
            print(e)
            time.sleep(5)

            print("Error for URL {}: {}".format(url, datetime.datetime.now()))
            print("Retrying.")

    return response.read()


# Needed to write tricky unicode correctly to csv
def unicode_decode(text):
    try:
        return text.encode('utf-8').decode()
    except UnicodeDecodeError:
        return text.encode('utf-8')


def scrapePoliticos(year):
    num_processed = 0
    scrape_starttime = datetime.datetime.now()
    after = ''
    base_url = "http://politicos.olhoneles.org"
    api_url = "/api/v0/candidacies"
    parameters = "/?election_round__election__year={}".format(year)

    print("Scraping candidates' data for year {}\n".format(year))

    url = base_url + api_url + parameters + after

    while True:
        response = json.loads(request_until_succeed(url))
        record1.insert(response['objects'])

        total_count = response["meta"]["total_count"]
        offset = response["meta"]["offset"]
        url = base_url + response["meta"]["next"]

        print("=================================")

        if total_count - offset < 20:
            break

    print("\nDone!\n{} Comments Processed in {}".format(
        num_processed, datetime.datetime.now() - scrape_starttime))


if __name__ == '__main__':
    # year_list = ['2012', '2014', '2016']
    year_list = ['2016']

    for year in year_list:
        scrapePoliticos(year)
