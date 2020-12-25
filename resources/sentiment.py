from flask_restful import Resource
from flask import jsonify, request, Response
from bson.json_util import dumps
import pymongo
from config import config

connection = config.initdb()
db = connection.scope_db


class SentimentPostsListAPI(Resource):
    def get(self):
        data = request.args

        if not data:
            data = {"response": "ERROR"}
            return jsonify(data)
        else:
            candidate = data.get("name")
            sns_type = data.get("type")

            relation = db.sns_relation.find_one({"$and": [{"user_id": candidate}, {"type": sns_type}]},
                                                no_cursor_timeout=True)
            user_list = relation['user_list']

            tweets_total = 0
            positive_total = 0
            negative_total = 0
            positive_posts = []
            negative_posts = []

            if sns_type == 'twitter':
                tweets_total = db.twitter_tweets.find(
                    {'user': {"$in": user_list}, 'tweet': {"$exists": True, "$ne": ""}}, no_cursor_timeout=True).count()
                positive_total = db.twitter_tweets.find(
                    {'user': {"$in": user_list}, 'has_sentiment': True, 'sentiment_value': 1},
                    no_cursor_timeout=True).count()
                positive_posts = db.twitter_tweets.find(
                    {'user': {"$in": user_list}, 'has_sentiment': True, 'sentiment_value': 1}, {'tweet': 1, '_id': 0},
                    no_cursor_timeout=True).limit(10)
                negative_total = db.twitter_tweets.find(
                    {'user': {"$in": user_list}, 'has_sentiment': True, 'sentiment_value': 0},
                    no_cursor_timeout=True).count()
                negative_posts = db.twitter_tweets.find(
                    {'user': {"$in": user_list}, 'has_sentiment': True, 'sentiment_value': 0}, {'tweet': 1, '_id': 0},
                    no_cursor_timeout=True).limit(10)
            elif sns_type == 'facebook':
                tweets_total = db.fb_posts.find(
                    {'page_id': {"$in": user_list}, 'status_message': {"$exists": True, "$ne": ""}},
                    no_cursor_timeout=True).count()
                positive_total = db.fb_posts.find(
                    {'page_id': {"$in": user_list}, 'has_sentiment': True, 'sentiment_value': 1},
                    no_cursor_timeout=True).count()
                positive_posts = db.fb_posts.find(
                    {'page_id': {"$in": user_list}, 'has_sentiment': True, 'sentiment_value': 1},
                    {'status_message': 1, '_id': 0},
                    no_cursor_timeout=True, limit=10)
                negative_total = db.fb_posts.find(
                    {'page_id': {"$in": user_list}, 'has_sentiment': True, 'sentiment_value': 0},
                    no_cursor_timeout=True).count()
                negative_posts = db.fb_posts.find(
                    {'page_id': {"$in": user_list}, 'has_sentiment': True, 'sentiment_value': 0},
                    {'status_message': 1, '_id': 0},
                    no_cursor_timeout=True, limit=10)

            result = {'tweets_total': tweets_total, 'positive_total': positive_total, 'negative_total': negative_total,
                      'positive_posts': positive_posts, 'negative_posts': negative_posts}

            return Response(dumps(result))


class SentimentCommentsListAPI(Resource):
    def get(self):
        data = request.args
        candidate = data['candidate']
        type = data['type']
        limit = int(data['limit'])

        relation = db.sns_relation.find_one({"$and": [{"user_id": candidate}, {"type": type}]},
                                            no_cursor_timeout=True)
        user_list = relation['user_list']

        if limit != -1:
            if type == 'facebook':
                posts = db.fb_comments.find(
                    {'page_id': {"$in": user_list}, 'comment_message': {"$exists": True, "$ne": ""}},
                    {'comment_id': 1, 'comment_message': 1, 'status_id': 1, 'comment_published': 1, 'page_id': 1,
                     'has_sentiment': 1, 'sentiment_value': 1},
                    limit=limit, no_cursor_timeout=True).sort('comment_published', pymongo.DESCENDING)
            else:
                posts = db.twitter_replies.find(
                    {'user': {"$in": user_list}, 'tweet': {"$exists": True, "$ne": ""}},
                    {'id': 1, 'tweet': 1, 'tweet_id': 1, 'date': 1, 'time': 1, 'has_sentiment': 1,
                     'sentiment_value': 1}, limit=limit, no_cursor_timeout=True).sort('date', pymongo.DESCENDING).sort(
                    'time',
                    pymongo.DESCENDING)
        else:
            if type == 'facebook':
                posts = db.fb_comments.find(
                    {'page_id': {"$in": user_list}, 'comment_message': {"$exists": True, "$ne": ""}},
                    {'comment_id': 1, 'comment_message': 1, 'status_id': 1, 'comment_published': 1, 'page_id': 1,
                     'has_sentiment': 1, 'sentiment_value': 1}, no_cursor_timeout=True).sort('comment_published',
                                                                                             pymongo.DESCENDING)
            else:
                posts = db.twitter_replies.find(
                    {'user': {"$in": user_list}, 'tweet': {"$exists": True, "$ne": ""}},
                    {'id': 1, 'tweet': 1, 'tweet_id': 1, 'date': 1, 'time': 1, 'has_sentiment': 1,
                     'sentiment_value': 1}, no_cursor_timeout=True).sort('date', pymongo.DESCENDING).sort('time',
                                                                                                          pymongo.DESCENDING)

        return Response(dumps(posts))
