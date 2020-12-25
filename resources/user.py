import json

from bson.json_util import dumps
from flask_restful import Resource
from flask import jsonify, request, Response
from bson.objectid import ObjectId
from werkzeug.security import check_password_hash, generate_password_hash
from config import config

connection = config.initdb()
db = connection.scope_db


class UserAPI(Resource):
    def get(self):
        data = db.user.find({})
        return Response(dumps(data))

    def post(self):
        data = request.get_json()

        if not data:
            data = {"response": "ERROR"}
            return jsonify(data)
        else:
            entry = {
                'name': data['name'],
                'password': generate_password_hash(data['password']),
            }

            user = db.user.find_one({"name": data['name']})

            if user and check_password_hash(user['password'], data['password']):
                return json.dumps("This user already exist")
            else:
                db.user.insert_one(entry)
                return json.dumps("Database Inserted. New User Inserted (%s)." % (data['name']))

    def put(self):
        data = request.get_json()

        if not data:
            data = {"response": "ERROR"}
            return jsonify(data)
        else:
            try:
                entry = {
                    'name': data['update']['name'],
                    'password': generate_password_hash(data['update']['password']),
                }

                user = db.user.find_one({"_id": ObjectId(data['id'])})

                if user:
                    db.user.update_one({"_id": ObjectId(data["id"])}, {"$set": entry})
                    return json.dumps("Database Updated (%s)." % user['name'])
                else:
                    return json.dumps("This User doesn't exist")
            except Exception as e:
                print("Response Error: %s" % e)
                return json.dumps("Wrong Request")

    def delete(self):
        data = request.get_json()
        print(data)
        if not data:
            data = {"response": "ERROR"}
            return jsonify(data)
        else:
            try:
                user = db.user.find_one({"_id": ObjectId(data['id'])})

                if user:
                    db.user.delete_one({"_id": ObjectId(data["id"])})
                    return json.dumps("Database User Deleted (%s)." % user['name'])
                else:
                    return json.dumps("This User doesn't exist")
            except Exception as e:
                print("Response Error: %s" % e)
                return json.dumps("Wrong Request")
