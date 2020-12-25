import requests
import json
from config import config

STR_NEW = "new"
STR_PROGRESS = "progress"
STR_SUCCESS = "completed"
STR_FAILED = "failed"

connection = config.initdb()
db = connection.scope_db

# Get the documents from the DB
def get_posts(user, sns):
    relation = db.sns_relation.find_one({"$and": [{"user_id": user}, {"type": sns}]}, no_cursor_timeout=True)
    user_list = relation['user_list']

    if sns == 'twitter':
        posts = db.twitter_tweets.find({'user': {"$in": user_list}, 'tweet': {"$exists": True, "$ne": ""}},
                                       no_cursor_timeout=True)
    elif sns == 'facebook':
        posts = db.fb_posts.find({'page_id': {"$in": user_list}, 'status_message': {"$exists": True, "$ne": ""}},
                                 no_cursor_timeout=True)
    else:
        posts = []

    return posts


def get_access_token(page_id):
    candidate_url = '{}/?pg={}'.format(config.access_token_api_url, page_id)
    res = requests.get(candidate_url,
                       headers={'contentType': 'text/html; charset=utf-8',
                                'Authorization': 'Token {}'.format(config.access_token_api_token)})

    if res.status_code == 200:
        result = json.loads(res.text)
        if len(result) > 0:
            access_token = result[0]['page_access_token']
        else:
            access_token = config.access_token
    else:
        access_token = config.access_token

    return access_token


def make_all_candidate_new():
    db.sns_relation.update_many({},
                                {"$set": {'scrap_status': STR_NEW, 'sentiment_status': STR_NEW,
                                          'tokenize_status': STR_NEW, 'lda_status': STR_NEW,
                                          'comments_scrap_status': STR_NEW,
                                          'comments_sentiment_status': STR_NEW}})


def make_all_candidate_complete():
    db.sns_relation.update_many({},
                                {"$set": {'scrap_status': STR_SUCCESS,
                                          'sentiment_status': STR_SUCCESS,
                                          'tokenize_status': STR_SUCCESS,
                                          'lda_status': STR_SUCCESS,
                                          'comments_scrap_status': STR_SUCCESS,
                                          'comments_sentiment_status': STR_SUCCESS}})


if __name__ == '__main__':
    make_all_candidate_complete()
