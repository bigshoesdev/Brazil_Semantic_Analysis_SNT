import argparse
import datetime
from time import gmtime, strftime, sleep

import tweepy as tweepy
from config import config

connection = config.initdb()
db = connection.scope_db
tweet_data = db.twitter_tweets

auth = tweepy.OAuthHandler(config.twitter_api['consumer_key'], config.twitter_api['consumer_secret'])
auth.set_access_token(config.twitter_api['access_token'], config.twitter_api['access_token_secret'])
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)


def run_twitter_scraper(candidate):
    global arg
    ap = argparse.ArgumentParser()
    ap.add_argument("-t", help="type of SNS: facebook, twitter")
    ap.add_argument("-u", help="User's Tweets you want to scrape.")
    ap.add_argument("--since", help="Filter Tweets sent since date (Example: 2017-12-27).")
    ap.add_argument("--until", help="Filter Tweets sent until date (Example: 2017-12-27).")

    arg, unknown = ap.parse_known_args()

    num_processed = 0
    timezone = strftime("%Z", gmtime())

    if arg.until:
        until = datetime.datetime.strptime(arg.until, '%Y-%m-%d')
    else:
        until = datetime.datetime.now()

    if arg.since:
        since = datetime.datetime.strptime(arg.since, '%Y-%m-%d')
    else:
        since = until.replace(year=until.year - config.timedelta_twitter)

    start_time = datetime.datetime.now()

    print("Scraping {} Twitter Page: {}\n".format(candidate, start_time))
    print('Scraping Since: ' + since.strftime("%Y-%m-%d %H:%M:%S") + ' Until: ' + until.strftime(
        "%Y-%m-%d %H:%M:%S") + ' \n')

    tweet_data.remove({'user': candidate})

    try:
        for pages in tweepy.Cursor(api.user_timeline, id=candidate).pages():
            # Time Limit Check
            minutes_diff = (datetime.datetime.now() - start_time).total_seconds() / 60
            if minutes_diff > (config.delta_time - config.offset_time):
                print('====================Time Limit Reached========================')
                break

            for tweet in pages:
                if tweet.in_reply_to_status_id_str is not None and tweet.in_reply_to_screen_name != candidate:
                    continue

                if until > tweet.created_at > since:
                    tweet_date = str(tweet.created_at).split(' ')[0]
                    tweet_time = str(tweet.created_at).split(' ')[1]

                    entry = {
                        'id': tweet.id,
                        'date': tweet_date,
                        'time': tweet_time,
                        'timezone': timezone,
                        'user': candidate,
                        'tweet': tweet.text.strip(),
                        'likes': tweet.favorite_count,
                        'retweets': tweet.retweet_count,
                        'hashtags': [tag['text'] for tag in tweet.entities['hashtags']],
                        'has_tokens': False,
                        'len_tokens': 0,
                        'tokens': []
                    }

                    if entry['tweet']:
                        num_processed += 1
                        if tweet_data.find({'id': tweet.id}).count() > 0:
                            tweet_data.update_one({'id': tweet.id}, {"$set": entry}, upsert=False)
                        else:
                            tweet_data.insert(entry)
                    else:
                        pass

                    if num_processed % 100 == 0:
                        print("================Scrapped Twitter Tweet Candidate: {}, Count: {}".format(candidate,
                                                                                                       num_processed))

        print("\nDone!\n{} Twitter Tweets Processed in {}".format(num_processed, datetime.datetime.now() - start_time))

    except BaseException as e:
        print('failed on_status,', str(e))
        sleep(3)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(prog="twitter_scraper.py", usage="python3 %(prog)s [options]",
                                 description="twitter_scraper.py - An Advanced Twitter Scraping Tool")
    ap.add_argument("-t", help="type of SNS: facebook, twitter")
    ap.add_argument("-u", help="User's Tweets you want to scrape.")
    ap.add_argument("--since", help="Filter Tweets sent since date (Example: 2017-12-27).")
    ap.add_argument("--until", help="Filter Tweets sent until date (Example: 2017-12-27).")

    arg = ap.parse_args()

    if arg.u:
        user = arg.u
    else:
        user = "RogerioMLisboa"

    run_twitter_scraper(user)
