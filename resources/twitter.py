import tweepy as tweepy
from flask_restful import Resource
from config import config
from flask import request, Response
from bson.json_util import dumps

connection = config.initdb()
db = connection.scope_db
tweet_data = db.twitter_tweets

auth = tweepy.OAuthHandler(config.twitter_api['consumer_key'], config.twitter_api['consumer_secret'])
auth.set_access_token(config.twitter_api['access_token'], config.twitter_api['access_token_secret'])
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)


class TwitterProfilePhotoAPI(Resource):
    def get(self):
        data = request.args
        name = data['name']
        users = api.lookup_users(screen_names=[name])
        if len(users) > 0:
            user = users[0]
            return Response(dumps({'url': user.profile_image_url}))
        else:
            return Response(dumps({'url': ''}))


if __name__ == "__main__":
    screen_name = 'RogerioMLisboa'
    users = api.lookup_users(screen_names=[screen_name])
    user = users[0]
    print(user.profile_image_url)
