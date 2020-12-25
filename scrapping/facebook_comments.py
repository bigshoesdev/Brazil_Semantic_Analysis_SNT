import json
import datetime
import time
from config import config
from utils.utils import get_access_token
from scrapping.facebook_posts_page import request_until_succeed

try:
    from urllib.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen, Request

connection = config.initdb()
db = connection.scope_db


def unicode_decode(text):
    try:
        return text.encode('utf-8').decode()
    except UnicodeDecodeError:
        return text.encode('utf-8')


def getFacebookCommentFeedUrl(base_url):
    # Construct the URL string
    fields = "&fields=id,message,reactions.limit(0).summary(true)" + \
             ",created_time,comments,from,attachment"
    url = base_url + fields

    return url


def processFacebookComment(comment, status_id, parent_id=''):
    comment_id = comment['id']
    comment_message = '' if 'message' not in comment or comment['message'] \
                            is '' else unicode_decode(comment['message'])

    if 'from' in comment:
        comment_author = unicode_decode(comment['from']['id'])
    else:
        comment_author = ''

    num_reactions = 0 if 'reactions' not in comment else \
        comment['reactions']['summary']['total_count']

    if 'attachment' in comment:
        attachment_type = comment['attachment']['type']
        attachment_type = 'gif' if attachment_type == 'animated_image_share' \
            else attachment_type
        attach_tag = "[[{}]]".format(attachment_type.upper())
        comment_message = attach_tag if comment_message is '' else \
            comment_message + " " + attach_tag

    # Time needs special care since a) it's in UTC and
    # b) it's not easy to use in statistical programs.

    comment_published = datetime.datetime.strptime(
        comment['created_time'], '%Y-%m-%dT%H:%M:%S+0000')
    comment_published = comment_published + datetime.timedelta(hours=-5)  # EST
    comment_published = comment_published.strftime(
        '%Y-%m-%d %H:%M:%S')  # best time format for spreadsheet programs

    # Return a tuple of all processed data
    return (comment_id, status_id, parent_id, comment_message, comment_author,
            comment_published, num_reactions)


def scrapeFacebookPageFeedComments(candidate):
    num_processed = 0
    base = "https://graph.facebook.com/v3.1"
    parameters = "/?limit={}&access_token={}".format(100, get_access_token(candidate))

    scrape_starttime = datetime.datetime.now()
    print("Scraping Comments From Posts: {}\n".format(scrape_starttime))

    record1 = db.fb_posts
    record2 = db.fb_comments

    status_list = list(record1.find({'page_id': candidate,
                                     'status_message': {"$exists": True, "$ne": ""}}, no_cursor_timeout=True))

    sleep_time = 10
    limit_comments_count_per_status = config.comments_per_page

    record2.remove({'page_id': candidate})

    for i in range(len(status_list)):
        status = status_list[i]
        print("==============Scrape Status {}======= Progress {} %=============".
              format(status['status_id'], int(i * 100 / len(status_list))))
        has_next_page = True
        after = ''
        status_comments_count = 0

        # Time Limit Check
        minutes_diff = (datetime.datetime.now() - scrape_starttime).total_seconds() / 60
        if minutes_diff > (config.delta_time - config.offset_time):
            print('====================Time Limit Reached========================')
            break

        while has_next_page:
            node = "/{}/comments".format(status['status_id'])
            after = '' if after is '' else "&after={}".format(after)
            base_url = base + node + parameters + after
            url = getFacebookCommentFeedUrl(base_url)
            time.sleep(sleep_time)
            comments = json.loads(request_until_succeed(url))

            for comment in comments['data']:
                comment_data = processFacebookComment(
                    comment, status['status_id'])

                entry = comment_data

                entry = {
                    'comment_id': entry[0],
                    'status_id': entry[1],
                    'page_id': candidate,
                    'comment_message': entry[3].strip(),
                    'comment_author': entry[4],
                    'comment_published': entry[5],
                    'num_reactions': entry[6],
                }

                print('comment_id', entry['comment_id'])

                if entry['comment_message']:
                    status_comments_count += 1
                    num_processed += 1
                    if record2.find({'comment_id': entry['comment_id']}).count() > 0:
                        record2.update_one({'comment_id': entry['comment_id']}, {"$set": entry}, upsert=False)
                    else:
                        record2.insert(entry)

                # output progress occasionally to make sure code is not stalling
                if num_processed % 100 == 0:
                    print("{} Comments Processed: {}".format(num_processed, datetime.datetime.now()))

                if status_comments_count > limit_comments_count_per_status:
                    print("==============Scrape Status Break 1 {} Comments {}====================".format(
                        status['status_id'], status_comments_count))
                    break

            if 'paging' in comments:
                if 'next' in comments['paging']:
                    after = comments['paging']['cursors']['after']
                else:
                    has_next_page = False
            else:
                has_next_page = False

            if status_comments_count > limit_comments_count_per_status:
                print("==============Scrape Status Break 2 {} Comments {}====================".format(
                    status['status_id'], status_comments_count))
                break

        print("==============Scrape Status Finish {} Comments {}====================".format(status['status_id'],
                                                                                             status_comments_count))

    print("\nDone!\n{} Comments Processed in {}".format(
        num_processed, datetime.datetime.now() - scrape_starttime))


if __name__ == '__main__':
    scrapeFacebookPageFeedComments('jairmessias.bolsonaro')
    # scrapeFacebookPageFeedComments('LuisMirandaUSA')
    # scrapeFacebookPageFeedComments('RogerioLisboaOFICIAL')
    # scrapeFacebookPageFeedComments('jairmessias.bolsonaro')
