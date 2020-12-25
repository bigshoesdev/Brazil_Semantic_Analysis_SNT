from flask_restful import Resource
from config import config
from bson.json_util import dumps
from flask import request, Response
import pymongo

connection = config.initdb()
db = connection.scope_db


class FacebookPostListAPI(Resource):
    def get(self):
        data = request.args
        candidate = data['candidate']
        limit = int(data['limit'])

        relation = db.sns_relation.find_one({"$and": [{"user_id": candidate}, {"type": 'facebook'}]},
                                            no_cursor_timeout=True)
        user_list = relation['user_list']

        if limit != -1:
            posts = db.fb_posts.find({'page_id': {"$in": user_list}, 'status_message': {"$exists": True, "$ne": ""}},
                                     {'status_message': 1, 'status_id': 1, 'status_published': 1, 'page_id': 1},
                                     limit=limit, no_cursor_timeout=True).sort('status_published', pymongo.DESCENDING)
        else:
            posts = db.fb_posts.find({'page_id': {"$in": user_list}, 'status_message': {"$exists": True, "$ne": ""}},
                                     {'status_message': 1, 'status_id': 1, 'status_published': 1, 'page_id': 1},
                                     no_cursor_timeout=True).sort('status_published', pymongo.DESCENDING)

        return Response(dumps(posts))
