from celery import Celery
from mongokit import *

import ses.awsses

celery = Celery('tasks', backend='mongodb', broker='mongodb://localhost:27017/jobs')

@celery.task
def test(a, b):
    return a + b

@celery.task
def notify_new_user_to_admin(info):
    r = ses.awsses.send_new_user_to_admin(info)

    return r

@celery.task
def forget_passwd(info):
    r = ses.awsses.send_forget_passwd(info)

    return r
