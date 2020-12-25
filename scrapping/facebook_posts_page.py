import json
import datetime
import time
import sys

from utils.utils import get_access_token
from config import config

try:
    from urllib.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen, Request

connection = config.initdb()
db = connection.scope_db


def request_until_succeed(url):
    req_count = 0
    req = Request(url)
    success = False
    while success is False:
        try:
            response = urlopen(req)
            if response.getcode() == 200:
                success = True
                req_count = 0
        except Exception as e:
            print(e)
            time.sleep(5)
            req_count += 1
            print("Error for URL {}: {}".format(url, datetime.datetime.now()))

            if req_count == 2:
                sys.exit("Failed")

    return response.read()


def unicode_decode(text):
    try:
        return text.encode('utf-8').decode()
    except UnicodeDecodeError:
        return text.encode('utf-8')


def getFacebookPageFeedUrl(base_url):
    fields = "&fields=message,link,created_time,type,name,id," + \
             "comments.limit(0).summary(true),shares,reactions" + \
             ".limit(0).summary(true)"

    return base_url + fields


def processFacebookPageFeedStatus(status):
    status_id = status['id']
    status_type = status['type']

    status_message = '' if 'message' not in status else \
        unicode_decode(status['message'])
    link_name = '' if 'name' not in status else \
        unicode_decode(status['name'])
    status_link = '' if 'link' not in status else \
        unicode_decode(status['link'])

    status_published = datetime.datetime.strptime(
        status['created_time'], '%Y-%m-%dT%H:%M:%S+0000')
    status_published = status_published + \
                       datetime.timedelta(hours=-5)  # EST
    status_published = status_published.strftime(
        '%Y-%m-%d %H:%M:%S')  # best time format for spreadsheet programs

    # Nested items require chaining dictionary keys.

    num_reactions = 0 if 'reactions' not in status else \
        status['reactions']['summary']['total_count']
    num_comments = 0 if 'comments' not in status else \
        status['comments']['summary']['total_count']
    num_shares = 0 if 'shares' not in status else status['shares']['count']

    return (status_id, status_message, link_name, status_type, status_link,
            status_published, num_reactions, num_comments, num_shares)


def scrapeFacebookPageFeedStatus(page_id, since, until):
    print("=====================scrapeFacebookPageFeedStatus===========================")
    has_next_page = True
    num_processed = 0
    start_time = datetime.datetime.now()
    after = ''
    base = "https://graph.facebook.com/v3.1"
    node = "/{}/posts".format(page_id)

    access_token = get_access_token(page_id)

    parameters = "/?limit={}&access_token={}".format(100, access_token)
    since = "&since={}".format(since) if since is not '' else ''
    until = "&until={}".format(until) if until is not '' else ''

    print("Scraping {} Facebook Page: {}\n".format(page_id, start_time))
    print('Scraping Since: ' + since + ' Until: ' + until)

    record1 = db.fb_posts
    record1.remove({'page_id': page_id})

    while has_next_page:
        after = '' if after is '' else "&after={}".format(after)
        base_url = base + node + parameters + after + since + until

        # Time Limit Check
        minutes_diff = (datetime.datetime.now() - start_time).total_seconds() / 60
        if minutes_diff > (config.delta_time - config.offset_time):
            print('====================Time Limit Reached========================')
            break

        url = getFacebookPageFeedUrl(base_url)
        time.sleep(20)
        statuses = json.loads(request_until_succeed(url))

        for status in statuses['data']:
            # Ensure it is a status with the expected metadata
            if 'reactions' in status:
                status_data = processFacebookPageFeedStatus(status)

                entry = status_data

                entry = {
                    'status_id': entry[0],
                    'page_id': page_id,
                    'status_message': entry[1].strip(),
                    'link_name': entry[2],
                    'status_type': entry[3],
                    'status_link': entry[4],
                    'status_published': entry[5],
                    'num_reactions': entry[6],
                    'num_comments': entry[7],
                    'num_shares': entry[8],
                    'has_tokens': False,
                    'len_tokens': 0,
                    'tokens': []
                }

                # print("================Scrapped Facebook Post {} {}".format(entry['status_id'], entry['page_id']))
                if entry['status_message']:
                    num_processed += 1
                    if record1.find({'status_id': entry['status_id']}).count() > 0:
                        record1.update_one({'status_id': entry['status_id']}, {"$set": entry}, upsert=False)
                    else:
                        record1.insert(entry)
                else:
                    pass

            if num_processed % 100 == 0:
                print("{} Statuses Processed: {}".format(num_processed, datetime.datetime.now()))

        if 'paging' in statuses:
            after = statuses['paging']['cursors']['after']
        else:
            has_next_page = False

    print("\nDone!\n{} Statuses Processed in {}".format(
        num_processed, datetime.datetime.now() - start_time))


if __name__ == '__main__':
    page_id = "RogerioLisboaOFICIAL"  # RogerioLisboaOFICIAL
    # page_id = "ThiagoDeMaristela"  # ThiagoDeMaristela
    # page_id = "jairmessias.bolsonaro"  # jairmessias.bolsonaro
    current_date = datetime.datetime.now()
    since = current_date.replace(year=current_date.year - config.timedelta_facebook).strftime("%Y-%m-%d")
    until = datetime.datetime.now().strftime("%Y-%m-%d")
    scrapeFacebookPageFeedStatus(page_id, since, until)
