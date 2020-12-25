import datetime
import json
import uuid

import pymongo
from bson.json_util import dumps
from bson.objectid import ObjectId
from flask import request, Response, jsonify
from flask_restful import Resource

from config import config
from scrapping.facebook_posts_page import scrapeFacebookPageFeedStatus
from scrapping.facebook_comments import scrapeFacebookPageFeedComments
from scrapping.twitter_tweets import run_twitter_scraper
from scrapping.twitter_replies import run_twitter_comments
from sentiment_analysis.eval_pos_neg_api import sentimetal_analysis, sentimetal_analysis_comments
from topic_modeling.tm_lda import run_lda
from topic_modeling.tm_tokenize import tokenize

connection = config.initdb()
db = connection.scope_db

STR_NEW = "new"
STR_PROGRESS = "progress"
STR_SUCCESS = "completed"
STR_FAILED = "failed"


def scraping_thread(candidate, sns_name):
    current_date = datetime.datetime.now()
    since = current_date.replace(year=current_date.year - config.timedelta_facebook).strftime("%Y-%m-%d")
    until = datetime.datetime.now().strftime("%Y-%m-%d")
    user_list = db.sns_relation.find_one({"$and": [{'user_id': candidate}, {'type': sns_name}]}, {'user_list'})[
        'user_list']

    db.sns_relation.update_one({"$and": [{'user_id': candidate}, {'type': sns_name}]},
                               {"$set": {'lock': True, 'scrap_status': STR_PROGRESS}})

    if sns_name == 'facebook':
        idx = 0
        for idx in range(len(user_list)):
            user = user_list[idx]

            try:
                scrapeFacebookPageFeedStatus(user, since, until)
            except SystemExit:
                db.sns_relation.update_one({"$and": [{'user_id': candidate}, {'type': sns_name}]},
                                           {"$set": {'scrap_status': STR_FAILED, 'lock': False,
                                                     'end_time': datetime.datetime.now()}})
                print("Facebook Scraping System Exit Error")
                return
            except Exception as e:
                db.sns_relation.update_one({"$and": [{'user_id': candidate}, {'type': sns_name}]},
                                           {"$set": {'scrap_status': STR_FAILED, 'lock': False,
                                                     'end_time': datetime.datetime.now()}})
                print("Facebook Scraping Error: %s" % e)
                return

        if idx == len(user_list) - 1:
            db.sns_relation.update_one({"$and": [{'user_id': candidate}, {'type': sns_name}]},
                                       {"$set": {'scrap_status': STR_SUCCESS, 'lock': False,
                                                 'end_time': datetime.datetime.now()}})
    else:
        idx = 0
        for idx in range(len(user_list)):
            user = user_list[idx]

            try:
                run_twitter_scraper(user)
            except SystemExit:
                db.sns_relation.update_one({"$and": [{'user_id': candidate}, {'type': sns_name}]},
                                           {"$set": {'scrap_status': STR_FAILED, 'lock': False,
                                                     'end_time': datetime.datetime.now()}})
                print("Twitter Scraping System Exit Error")
                return

            except Exception as e:
                db.sns_relation.update_one({"$and": [{'user_id': candidate}, {'type': sns_name}]},
                                           {"$set": {'scrap_status': STR_FAILED, 'lock': False,
                                                     'end_time': datetime.datetime.now()}})
                print("Twitter Scraping Error: %s" % e)
                return

        if idx == len(user_list) - 1:
            db.sns_relation.update_one({"$and": [{'user_id': candidate}, {'type': sns_name}]},
                                       {"$set": {'scrap_status': STR_SUCCESS, 'lock': False,
                                                 'end_time': datetime.datetime.now()}})


def sentiment_thread(candidate, sns_name):
    if db.sns_relation.find_one(
            {"$and": [{'user_id': candidate}, {'type': sns_name}, {'scrap_status': STR_SUCCESS}]}) is None:
        print("Sorry. Scraping Failed. Can't Continue Sentimentalize.")
        return

    db.sns_relation.update_one({"$and": [{'user_id': candidate}, {'type': sns_name}]},
                               {"$set": {'lock': True, 'sentiment_status': STR_PROGRESS}})

    try:
        if not config.debug:
            sentimetal_analysis(candidate, sns_name)
        db.sns_relation.update_one({"$and": [{'user_id': candidate}, {'type': sns_name}]},
                                   {"$set": {'sentiment_status': STR_SUCCESS, 'lock': False,
                                             'end_time': datetime.datetime.now()}})
    except Exception as e:
        db.sns_relation.update_one({"$and": [{'user_id': candidate}, {'type': sns_name}]},
                                   {"$set": {'sentiment_status': STR_FAILED, "lock": False,
                                             'end_time': datetime.datetime.now()}})
        print("Sentimentalize Error: %s" % e)
        return


def tokenize_thread(candidate, sns_name):
    if db.sns_relation.find_one(
            {"$and": [{'user_id': candidate}, {'type': sns_name}, {'sentiment_status': STR_SUCCESS}]}) is None:
        print("Sorry. Sentimentalize Failed. Can't Continue Tokenize.")
        return

    db.sns_relation.update_one({"$and": [{'user_id': candidate}, {'type': sns_name}]},
                               {"$set": {'lock': True, 'tokenize_status': STR_PROGRESS}})

    try:
        tokenize(candidate, sns_name)
        db.sns_relation.update_one({"$and": [{'user_id': candidate}, {'type': sns_name}]},
                                   {"$set": {'tokenize_status': STR_SUCCESS, 'lock': False,
                                             'end_time': datetime.datetime.now()}})
    except Exception as e:
        db.sns_relation.update_one({"$and": [{'user_id': candidate}, {'type': sns_name}]},
                                   {"$set": {'tokenize_status': STR_FAILED, "lock": False,
                                             'end_time': datetime.datetime.now()}})
        print("Tokenize Error: %s" % e)
        return


def run_lda_thread(candidate, sns_name):
    if db.sns_relation.find_one(
            {"$and": [{'user_id': candidate}, {'type': sns_name}, {'tokenize_status': STR_SUCCESS}]}) is None:
        print("Sorry. Tokenize Failed. Can't Continue LDA progress.")
        return

    db.sns_relation.update_one({"$and": [{'user_id': candidate}, {'type': sns_name}]},
                               {"$set": {'lock': True, 'lda_status': STR_PROGRESS, 'lock': False}})

    try:
        data = {
            'name': candidate,
            'type': sns_name
        }

        run_lda(data)
        db.sns_relation.update_one({"$and": [{'user_id': candidate}, {'type': sns_name}]},
                                   {"$set": {'lda_status': STR_SUCCESS, "lock": False,
                                             'end_time': datetime.datetime.now()}})
    except Exception as e:
        db.sns_relation.update_one({"$and": [{'user_id': candidate}, {'type': sns_name}]},
                                   {"$set": {'lda_status': STR_FAILED, "lock": False,
                                             'end_time': datetime.datetime.now()}})
        print("Run LDA Error: %s" % e)
        return


def comments_scraping_thread(candidate, sns_name):
    if db.sns_relation.find_one(
            {"$and": [{'user_id': candidate}, {'type': sns_name}, {'lda_status': STR_SUCCESS}]}) is None:
        print("Sorry. Run LDA Failed. Can't Continue Comments Scraping.")
        return

    user_list = db.sns_relation.find_one({"$and": [{'user_id': candidate}, {'type': sns_name}]}, {'user_list'})[
        'user_list']

    db.sns_relation.update_one({"$and": [{'user_id': candidate}, {'type': sns_name}]},
                               {"$set": {'lock': True, 'comments_scrap_status': STR_PROGRESS}})

    if sns_name == 'facebook':
        idx = 0
        for idx in range(len(user_list)):
            user = user_list[idx]

            try:
                print("Facebook Comment Scraping")
                scrapeFacebookPageFeedComments(user)
            except SystemExit:
                db.sns_relation.update_one({"$and": [{'user_id': candidate}, {'type': sns_name}]},
                                           {"$set": {'comments_scrap_status': STR_FAILED, 'lock': False,
                                                     'end_time': datetime.datetime.now()}})
                print("Facebook Comments Scraping System Exit Error")
                return
            except Exception as e:
                db.sns_relation.update_one({"$and": [{'user_id': candidate}, {'type': sns_name}]},
                                           {"$set": {'comments_scrap_status': STR_FAILED, 'lock': False,
                                                     'end_time': datetime.datetime.now()}})
                print("Facebook Comments Scraping Error: %s" % e)
                return

        if idx == len(user_list) - 1:
            db.sns_relation.update_one({"$and": [{'user_id': candidate}, {'type': sns_name}]},
                                       {"$set": {'comments_scrap_status': STR_SUCCESS, 'lock': False,
                                                 'end_time': datetime.datetime.now()}})
    else:
        idx = 0
        for idx in range(len(user_list)):
            user = user_list[idx]

            try:
                print("Twitter Comments Scraping")
                run_twitter_comments(user)
            except SystemExit:
                db.sns_relation.update_one({"$and": [{'user_id': candidate}, {'type': sns_name}]},
                                           {"$set": {'comments_scrap_status': STR_FAILED, 'lock': False,
                                                     'end_time': datetime.datetime.now()}})
                print("Twitter Comments Scraping System Exit Error")
                return

            except Exception as e:
                db.sns_relation.update_one({"$and": [{'user_id': candidate}, {'type': sns_name}]},
                                           {"$set": {'comments_scrap_status': STR_FAILED, 'lock': False,
                                                     'end_time': datetime.datetime.now()}})
                print("Twitter Comments Scraping Error: %s" % e)
                return

        if idx == len(user_list) - 1:
            db.sns_relation.update_one({"$and": [{'user_id': candidate}, {'type': sns_name}]},
                                       {"$set": {'comments_scrap_status': STR_SUCCESS, 'lock': False,
                                                 'end_time': datetime.datetime.now()}})


def comments_sentiment_thread(candidate, sns_name):
    if db.sns_relation.find_one(
            {"$and": [{'user_id': candidate}, {'type': sns_name}, {'comments_scrap_status': STR_SUCCESS}]}) is None:
        print("Sorry. Comments Scraping Failed. Can't Continue Comments Sentimentalize.")
        return

    db.sns_relation.update_one({"$and": [{'user_id': candidate}, {'type': sns_name}]},
                               {"$set": {'lock': True, 'comments_sentiment_status': STR_PROGRESS}})

    try:
        if not config.debug:
            sentimetal_analysis_comments(candidate, sns_name)
        db.sns_relation.update_one({"$and": [{'user_id': candidate}, {'type': sns_name}]},
                                   {"$set": {'comments_sentiment_status': STR_SUCCESS, 'lock': False,
                                             'end_time': datetime.datetime.now()}})
    except Exception as e:
        db.sns_relation.update_one({"$and": [{'user_id': candidate}, {'type': sns_name}]},
                                   {"$set": {'comments_sentiment_status': STR_FAILED, "lock": False,
                                             'end_time': datetime.datetime.now()}})
        print("Comments Sentimentalize Error: %s" % e)
        return


def main_job():
    jobID = uuid.uuid4()
    print("===================Run Main Job ID (%s)  Scrapping, Tokenize, LDA=====================" % jobID)

    snsLockedJobCount = db.sns_relation.find({'lock': True}, no_cursor_timeout=True).count()

    if snsLockedJobCount > config.num_job:
        print('===================Can not run Job because currently there are many jobs========================')
        return

    snsJob = db.sns_relation.find_one(
        {"$and": [
            {"$or": [{"$and": [{"scrap_status": STR_NEW}, {"sentiment_status": STR_NEW}, {"tokenize_status": STR_NEW},
                               {"lda_status": STR_NEW}, {"comments_scrap_status": STR_NEW},
                               {"comments_sentiment_status": STR_NEW}]},
                     {"$and": [{"scrap_status": STR_SUCCESS}, {"sentiment_status": STR_NEW},
                               {"tokenize_status": STR_NEW}, {"lda_status": STR_NEW},
                               {"comments_scrap_status": STR_NEW}, {"comments_sentiment_status": STR_NEW}]},
                     {"$and": [{"scrap_status": STR_SUCCESS}, {"sentiment_status": STR_SUCCESS},
                               {"tokenize_status": STR_NEW}, {"lda_status": STR_NEW},
                               {"comments_scrap_status": STR_NEW}, {"comments_sentiment_status": STR_NEW}]},
                     {"$and": [{"scrap_status": STR_SUCCESS}, {"sentiment_status": STR_SUCCESS},
                               {"tokenize_status": STR_SUCCESS}, {"lda_status": STR_NEW},
                               {"comments_scrap_status": STR_NEW}, {"comments_sentiment_status": STR_NEW}]},
                     {"$and": [{"scrap_status": STR_SUCCESS}, {"sentiment_status": STR_SUCCESS},
                               {"tokenize_status": STR_SUCCESS}, {"lda_status": STR_SUCCESS},
                               {"comments_scrap_status": STR_NEW}, {"comments_sentiment_status": STR_NEW}]},
                     {"$and": [{"scrap_status": STR_SUCCESS}, {"sentiment_status": STR_SUCCESS},
                               {"tokenize_status": STR_SUCCESS}, {"lda_status": STR_SUCCESS},
                               {"comments_scrap_status": STR_SUCCESS}, {"comments_sentiment_status": STR_NEW}]},
                     ]}, {'lock': False}]}, sort=[('end_time', pymongo.ASCENDING)], no_cursor_timeout=True)

    if not snsJob:
        print("===================No SNS Candidate From Main Job (%s) ========================" % jobID)
        return

    db.sns_relation.update_one({"$and": [{'user_id': snsJob['user_id']}, {'type': snsJob['type']}]},
                               {"$set": {"lock": True, "start_time": datetime.datetime.now()}})

    if snsJob['scrap_status'] == STR_NEW:
        print("============Run Main Job ID (%s) Scraping Started (%s - %s)============" % (
            jobID, snsJob['user_id'], snsJob['type']))
        scraping_thread(snsJob['user_id'], snsJob['type'])
        print("============Run Main Job ID (%s) Scraping Finished (%s - %s)============" % (
            jobID, snsJob['user_id'], snsJob['type']))

    if snsJob['sentiment_status'] == STR_NEW:
        print("============Run Main Job ID (%s) Run Main Job ID (%s - %s) Sentimentalize============" % (
            jobID, snsJob['user_id'], snsJob['type']))
        sentiment_thread(snsJob['user_id'], snsJob['type'])
        print('============Run Main Job ID (%s) Sentimentalize Finished (%s - %s)============' % (
            jobID, snsJob['user_id'], snsJob['type']))

    if snsJob['tokenize_status'] == STR_NEW:
        print("============Run Main Job ID (%s) Run Main Job ID (%s - %s) Tokenize============" % (
            jobID, snsJob['user_id'], snsJob['type']))
        tokenize_thread(snsJob['user_id'], snsJob['type'])
        print('============Run Main Job ID (%s) Tokenize Finished (%s - %s)============' % (
            jobID, snsJob['user_id'], snsJob['type']))

    if snsJob['lda_status'] == STR_NEW:
        print("=================Run Main Job ID (%s) Run Main Job ID (%s - %s) Run LDA============" % (
            jobID, snsJob['user_id'], snsJob['type']))
        run_lda_thread(snsJob['user_id'], snsJob['type'])
        print("=================Run Main Job ID (%s) Run LDA Finished (%s - %s)============" % (
            jobID, snsJob['user_id'], snsJob['type']))

    if snsJob['comments_scrap_status'] == STR_NEW:
        print("=================Run Main Job ID (%s) Run Main Job ID (%s - %s) Run Comments Scrape============" % (
            jobID, snsJob['user_id'], snsJob['type']))
        comments_scraping_thread(snsJob['user_id'], snsJob['type'])
        print("=================Run Main Job ID (%s) Run Comments Scrape Finished (%s - %s)============" % (
            jobID, snsJob['user_id'], snsJob['type']))

    if snsJob['comments_sentiment_status'] == STR_NEW:
        print("=================Run Main Job ID (%s) Run Main Job ID (%s - %s) Run Comments Sentiment============" % (
            jobID, snsJob['user_id'], snsJob['type']))
        comments_sentiment_thread(snsJob['user_id'], snsJob['type'])
        print("=================Run Main Job ID (%s) Run Comments Sentiment Finished (%s - %s)============" % (
            jobID, snsJob['user_id'], snsJob['type']))


def getThreadData():
    result = []
    resData = {}
    sns_relation_data = db.sns_relation.find({})

    for idx, data in enumerate(sns_relation_data):
        posts = []
        comments = []
        for complement in data['user_list']:
            if data['type'] == 'twitter':
                tweets = db.twitter_tweets.find({'user': complement}, no_cursor_timeout=True)
                tweet_replies = db.twitter_replies.find({'user': complement}, no_cursor_timeout=True)
                postCounts = tweets.count()
                commentCounts = tweet_replies.count()
                posts.append({'user': complement, 'posts': postCounts})
                comments.append({'user': complement, 'comments': commentCounts})

            elif data['type'] == 'facebook':
                fposts = db.fb_posts.find({'page_id': complement}, no_cursor_timeout=True)
                fcomments = db.fb_comments.find({'page_id': complement}, no_cursor_timeout=True)
                postCounts = fposts.count()
                commentCounts = fcomments.count()
                posts.append({'user': complement, 'posts': postCounts})
                comments.append({'user': complement, 'comments': commentCounts})

        data.update({'posts': posts})
        data.update({'comments': comments})
        result.append(data)

    resData.update({'data': result, 'authorization_token': config.access_token_api_token})
    return resData


class ThreadUpdateAPI(Resource):
    def post(self):
        user_list = []
        data = request.get_json()

        if not data:
            data = {"response": "ERROR"}
            return jsonify(data)
        else:
            try:
                snsJob = db.sns_relation.find_one({"_id": ObjectId(data["id"])})
                if snsJob:
                    if 'user_list' in data['update'].keys():
                        user_list.append(data['update']['user_id'])
                        if data['update']:
                            for x in data['update']['user_list'].split(','):
                                if x.strip() != '':
                                    user_list.append(x.strip())
                                else:
                                    pass
                            data['update']['user_list'] = user_list
                        db.sns_relation.update_one({"_id": ObjectId(data["id"])}, {"$set": data['update']})
                    else:
                        db.sns_relation.update_one({"_id": ObjectId(data["id"])}, {"$set": data['update']})
                    return Response(dumps(getThreadData()))
                else:
                    return Response(dumps(getThreadData()))
            except Exception as e:
                print("Response Error: %s" % e)
                return Response(dumps(getThreadData()))


class ThreadMainAPI(Resource):
    def get(self):
        return Response(dumps(getThreadData()))

    def post(self):
        user_list = []
        data = request.get_json()

        if not data:
            data = {"response": "ERROR"}
            return jsonify(data)
        else:
            user_list.append(data['name'])
            if data['complements']:
                for x in data['complements'].split(','):
                    if x.strip() != '':
                        user_list.append(x.strip())
                    else:
                        pass

            entry = {
                'type': data['type'],
                'user_id': data['name'],
                'user_list': user_list,
                'scrap_status': STR_NEW,
                'sentiment_status': STR_NEW,
                'tokenize_status': STR_NEW,
                'lda_status': STR_NEW,
                "comments_scrap_status": STR_NEW,
                "comments_sentiment_status": STR_NEW,
                "lock": False
            }

            if not db.sns_relation.find_one({"$and": [{'user_id': data['name']}, {'type': data['type']}]}):
                db.sns_relation.insert(entry)
                return Response(dumps(getThreadData()))
            else:
                return Response(dumps(getThreadData()))


class ThreadAddFromAPI(Resource):
    def post(self):
        user_list = []
        data = request.get_json()

        if not data:
            data = {"response": "ERROR"}
            return jsonify(data)
        else:
            user_list.append(data['name'])
            if data['complements']:
                for complement in data['complements']:
                    user_list.append(complement)

            entry = {
                'type': data['type'],
                'user_id': data['name'],
                'user_list': user_list,
                'scrap_status': STR_NEW,
                'sentiment_status': STR_NEW,
                'tokenize_status': STR_NEW,
                'lda_status': STR_NEW,
                "comments_scrap_status": STR_NEW,
                "comments_sentiment_status": STR_NEW,
                "lock": False
            }

            if not db.sns_relation.find_one({"$and": [{'user_id': data['name']}, {'type': data['type']}]}):
                db.sns_relation.insert(entry)
                return Response(dumps({'success': True}))
            else:
                return Response(dumps({'success': False, 'message': 'Already existed'}))


if __name__ == '__main__':
    # scraping_thread("RogerioMLisboa", "twitter")
    # scraping_thread("LuisMirandaUSA", "twitter")
    comments_scraping_thread('jairbolsonaro', 'twitter')
