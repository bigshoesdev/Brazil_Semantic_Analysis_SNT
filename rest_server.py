#!flask/bin/python
import datetime

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_restful import Api
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

from main_thread import main_job
from scheduling_thread import scheduling_job
from celery.schedules import crontab
from resources.topicmodeling import TopicModelingAPI
from resources.tagmodeling import TagModelingAPI
from resources.user import UserAPI
from resources.sentiment import SentimentPostsListAPI, SentimentCommentsListAPI
from resources.facebook import FacebookPostListAPI
from resources.twitter import TwitterProfilePhotoAPI
from resources.article import ArticleSearchAPI
from resources.article import CandidateSearchAPI
from main_thread import ThreadUpdateAPI, ThreadMainAPI, ThreadAddFromAPI
from config import config
from celery import Celery
from celery.utils.log import get_task_logger


def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )

    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


logger = get_task_logger(__name__)
app = Flask(__name__)
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['CELERY_BROKER_URL'] = 'amqp://guest:guest@localhost//'
app.config['CELERY_RESULT_BACKEND'] = 'amqp://guest:guest@localhost//'
app.config['CELERYBEAT_SCHEDULE'] = {
    # Executes every minute
    'main_job': {
        'task': 'main_job_task',
        'schedule': crontab(minute="*/5")
    },
    'scheduler_job': {
        'task': 'scheduler_job_task',
        'schedule': crontab(minute=5, hour="*/{0}".format(int(config.delta_time / 60)))
    }
}

api = Api(app)
cors = CORS(app)

celery = make_celery(app)
connection = config.initdb()
db = connection.scope_db

api.add_resource(TopicModelingAPI, '/topic_modeling/api/v1.0/posts', endpoint='topic')
api.add_resource(TagModelingAPI, '/tag_modeling/api/v1.0/posts', endpoint='tag')
api.add_resource(SentimentPostsListAPI, '/sentiment/api/v1.0/posts', endpoint='sentiment_posts_list')
api.add_resource(SentimentCommentsListAPI, '/sentiment/api/v1.0/comments', endpoint='sentiment_comments_list')
api.add_resource(ThreadUpdateAPI, '/thread/api/v1.0/update', endpoint='update_candidate')
api.add_resource(ThreadMainAPI, '/thread/api/v1.0/add', endpoint='add_candidate_from_sm_scopo')
api.add_resource(ThreadMainAPI, '/thread/api/v1.0/dashboard', endpoint='get_candidate_data')
api.add_resource(ThreadAddFromAPI, '/thread/api/v1.0/add_candidate', endpoint='add_candidate_from_api')
api.add_resource(UserAPI, '/thread/api/v1.0/user', endpoint='get_user_data')
api.add_resource(UserAPI, '/thread/api/v1.0/updateUser', endpoint='update_user')
api.add_resource(UserAPI, '/thread/api/v1.0/addUser', endpoint='add_user')
api.add_resource(UserAPI, '/thread/api/v1.0/deleteUser', endpoint='delete_user')
api.add_resource(FacebookPostListAPI, '/facebook/api/posts', endpoint='facebook_list')
api.add_resource(TwitterProfilePhotoAPI, '/twitter/api/profile/photo', endpoint='twitter_profile_photo')
api.add_resource(ArticleSearchAPI, '/article/api/search', endpoint='article_search')
api.add_resource(CandidateSearchAPI, '/article/api/candidate', endpoint='candidate_search')



@app.route('/')
def index():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    POST_USERNAME = str(request.form['loginId'])
    POST_PASSWORD = str(request.form['loginPass'])

    user = db.user.find_one({'name': POST_USERNAME})

    if user and check_password_hash(user['password'], POST_PASSWORD):
        session['logged_in'] = True
        return redirect(url_for('dashboard'))
    else:
        flash('wrong password!')
        return redirect(url_for('index'))


@app.route('/signup_form', methods=['POST'])
def signup_form():
    USERNAME = str(request.form['signupId'])
    PASSWORD = str(request.form['signupPass'])

    db.user.update_one({}, {'$set': {'name': USERNAME, 'password': generate_password_hash(PASSWORD)}})
    session['logged_in'] = False

    return redirect(url_for('index'))


@app.route("/logout")
def logout():
    session['logged_in'] = False
    return redirect(url_for('index'))


@app.route("/user")
def user():
    if not session.get('logged_in'):
        return render_template('login.html')
    return render_template('user.html')


@app.route('/dashboard')
def dashboard():
    data = {
        'current_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'schedule_period': config.delta_time,
        'concurrent_job_count': config.num_job,
        'comments_per_post': config.comments_per_page,
    }

    if not session.get('logged_in'):
        return render_template('login.html')
    return render_template('dashboard.html', data=data)


@celery.task(name="main_job_task")
def main_job_task():
    print('#####################Main Job Task##########################')
    main_job()


@celery.task(name="scheduler_job_task")
def scheduler_job_task():
    print('#####################Scheduler Job Task##########################')
    scheduling_job()


if __name__ == '__main__':
    app.run(host='0.0.0.0')
