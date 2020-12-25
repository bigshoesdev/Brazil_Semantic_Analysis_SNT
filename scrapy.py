import argparse
import asyncio
import datetime

from scrapping.facebook_comments import scrapeFacebookPageFeedComments
from scrapping.facebook_posts_page import scrapeFacebookPageFeedStatus
from scrapping.twitter_tweets import run_twitter_scraper
from config import config


def main():
    if arg.t == 'facebook':
        page_id = arg.p
        current_date = datetime.datetime.now()
        since = current_date.replace(year=current_date.year - config.timedelta_facebook).strftime("%Y-%m-%d")
        until = datetime.datetime.now().strftime("%Y-%m-%d")

        if arg.since:
            since = arg.since

        if arg.until:
            until = arg.until

        if arg.k == 'post':
            scrapeFacebookPageFeedStatus(page_id, since, until)
        else:
            scrapeFacebookPageFeedComments(page_id)

    elif arg.t == 'twitter':
        run_twitter_scraper(arg.u)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(prog="scrapy.py", usage="python3 %(prog)s [options]",
                                 description="scrapy.py - An Advanced Scraping Tool")
    ap.add_argument("-t", help="type of SNS: facebook, twitter")
    ap.add_argument("-p", help="page id of candidate's facebook")
    ap.add_argument("-u", help="User's Tweets you want to scrape.")
    ap.add_argument("-s", help="Search for Tweets containing this word or phrase.")
    ap.add_argument("-k", help="kind of facebook scraping: post, comment")
    ap.add_argument("-l", help="Serch for Tweets in a specific language")
    ap.add_argument("-g", help="Search for geocoded tweets.")
    ap.add_argument("--followers", help="Scrape a person's followers", action="store_true")
    ap.add_argument("--following", help="Scrape who a person follows.", action="store_true")
    ap.add_argument("--favorites", help="Scrape Tweets a user has liked.", action="store_true")
    ap.add_argument("--since", help="Filter Tweets sent since date (Example: 2017-12-27).")
    ap.add_argument("--until", help="Filter Tweets sent until date (Example: 2017-12-27).")
    ap.add_argument("--timedelta", help="Time intervall for every request")
    ap.add_argument("--limit", help="Number of Tweets to pull (Increments of 20).")
    ap.add_argument("--tweets", help="Display Tweets only.", action="store_true")
    ap.add_argument("--year", help="Filter Tweets before specified year.")
    ap.add_argument("--fruit", help="Display 'low-hanging-fruit' Tweets.", action="store_true")
    ap.add_argument("--count", help="Display number Tweets scraped at the end of session.", action="store_true")
    ap.add_argument("--verified", help="Display Tweets only from verified users (Use with -s).", action="store_true")
    ap.add_argument("--to", help="Search Tweets to a user")
    ap.add_argument("--all", help="Search all Tweets associated with a user")
    ap.add_argument("-es", "--elasticsearch", help="Index to Elasticsearch")
    ap.add_argument("--debug", help="Debug mode", action="store_true")
    ap.add_argument("--users", help="Display users only (Use with -s).", action="store_true")
    ap.add_argument("--hashtags", help="Output hashtags in seperate column.", action="store_true")
    ap.add_argument("--stats", help="Show number of replies, retweets, and likes", action="store_true")
    ap.add_argument("-o", help="Save output to a file.")

    arg = ap.parse_args()

    main()
