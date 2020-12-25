import argparse
import datetime
from time import gmtime, strftime

import tweepy as tweepy
from config import config

connection = config.initdb()
db = connection.scope_db
tweet_data = db.twitter_tweets

auth = tweepy.AppAuthHandler(config.twitter_api['consumer_key'], config.twitter_api['consumer_secret'])
# auth.set_access_token(config.twitter_api['access_token'], config.twitter_api['access_token_secret'])
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)


def run_twitter_comments(candidate):
    start_time = datetime.datetime.now()
    print("Scraping {} Twitter Reply Page: {}\n".format(candidate, start_time))

    tweets = list(db.twitter_tweets.find({'user': candidate, 'tweet': {"$exists": True, "$ne": ""}},
                                         no_cursor_timeout=True))

    record = db.twitter_replies
    timezone = strftime("%Z", gmtime())

    record.remove({'user': candidate})

    for i in range(len(tweets)):
        reply_count = [0]
        tweet = tweets[i]
        print("Scraping Twitter Reply For Tweet: {} Progress {} %".format(tweet['id'], int(i * 100 / len(tweets))))

        # Time Limit Check
        minutes_diff = (datetime.datetime.now() - start_time).total_seconds() / 60
        if minutes_diff > (config.delta_time - config.offset_time):
            print('====================Time Limit Reached========================')
            break

        for reply in run_tweet_replies(tweet['user'], tweet['id'], reply_count):
            reply_date = str(reply.created_at).split(' ')[0]
            reply_time = str(reply.created_at).split(' ')[1]

            entry = {
                'id': reply.id,
                'date': reply_date,
                'time': reply_time,
                'timezone': timezone,
                'user': candidate,
                'tweet': reply.full_text.strip(),
                'tweet_id': tweet['id'],
                'likes': reply.favorite_count,
                'hashtags': [tag['text'] for tag in reply.entities['hashtags']],
            }

            if entry['tweet']:
                reply_count[0] += 1
                if record.find({'id': reply.id}).count() > 0:
                    record.update_one({'id': reply.id}, {"$set": entry}, upsert=False)
                else:
                    record.insert(entry)

        print("Scraping Twitter Finish For Tweet: {} Replies {}\n".format(tweet['id'], reply_count[0]))

    print("\nDone!\nScraping Twitter Reply Processed in {}".format(datetime.datetime.now() - start_time))


def run_tweet_replies(user_id, tweet_id, reply_count):
    replies = tweepy.Cursor(api.search, q='to:{}'.format('@' + user_id),
                            since_id=tweet_id, tweet_mode='extended').items(15)

    limit_comments_count_per_status = 15

    while True:
        try:
            reply = replies.next()
            if not hasattr(reply, 'in_reply_to_status_id_str'):
                continue

            if reply.in_reply_to_status_id == tweet_id and reply.full_text.strip():
                yield reply

                for reply_to_reply in run_tweet_replies(user_id, reply.id, reply_count):
                    yield reply_to_reply

                if reply_count[0] > limit_comments_count_per_status:
                    print("Scraping Twitter Break For Tweet: {} Replies {}\n".format(tweet_id, reply_count[0]))
                    break

        except tweepy.RateLimitError as e:
            print("Twitter api rate limit reached".format(e))
            break
        except tweepy.TweepError as e:
            print("Tweepy error occured:{}".format(e))
            break
        except StopIteration:
            break
        except Exception as e:
            print("Failed while fetching replies {}".format(e))
            break


if __name__ == "__main__":
    ap = argparse.ArgumentParser(prog="twitter_scraper.py", usage="python3 %(prog)s [options]",
                                 description="twitter_scraper.py - An Advanced Twitter Scraping Tool")
    ap.add_argument("-t", help="type of SNS: facebook, twitter")
    ap.add_argument("-u", help="User's Tweets you want to scrape.")

    arg = ap.parse_args()

    if arg.u:
        user = arg.u
    else:
        user = "RogerioMLisboa"

    run_twitter_comments(user)
