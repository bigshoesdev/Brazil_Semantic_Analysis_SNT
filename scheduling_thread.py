import uuid
import time
import datetime
import pymongo

from config import config

connection = config.initdb()
db = connection.scope_db

STR_NEW = "new"
STR_PROGRESS = "progress"


def scheduling_job():
    jobID = uuid.uuid4()
    print("===================Run Scheduling Job ID (%s)=====================" % jobID)
    limit = 0
    sns_relation_data = db.sns_relation.find({'$and': [{'scrap_status': {'$ne': STR_PROGRESS}},
                                                       {'sentiment_status': {'$ne': STR_PROGRESS}},
                                                       {'tokenize_status': {'$ne': STR_PROGRESS}},
                                                       {'lda_status': {'$ne': STR_PROGRESS}},
                                                       {'comments_scrap_status': {'$ne': STR_PROGRESS}},
                                                       {'comments_sentiment_status': {'$ne': STR_PROGRESS}},
                                                       {'lock': False}]}).sort('end_time', pymongo.ASCENDING)

    for idx, snsJob in enumerate(sns_relation_data):
        current_time = time.time()
        current_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time))
        if 'end_time' in snsJob.keys():
            end_time = time.mktime(snsJob['end_time'].timetuple())
            end_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))
            print("Scheduling Job User (%s) Current Time (%s) End Time (%s)" % (
                snsJob['user_id'], current_date, end_date))
            print("Delta Time: (%s)" % ((current_time - end_time) / 60))
            if limit >= config.num_job:
                break

            if (current_time - end_time) / 60 >= config.delta_time:
                limit += 1
                print("=================== User: (%s) SNS: (%s) =====================" % (
                    snsJob['user_id'], snsJob['type']))
                db.sns_relation.update_one({'_id': snsJob['_id']},
                                           {"$set": {"scrap_status": STR_NEW,
                                                     "sentiment_status": STR_NEW,
                                                     "tokenize_status": STR_NEW,
                                                     "lda_status": STR_NEW,
                                                     "comments_scrap_status": STR_NEW,
                                                     "comments_sentiment_status": STR_NEW}})

    print("===================Finish Scheduling Job ID (%s)=====================" % jobID)


if __name__ == '__main__':
    scheduling_job()
