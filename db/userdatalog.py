# -*- coding: utf-8 -*-
from mongokit import Document
import datetime

class UserDataLog(Document):
    __collection__ = 'user_data_log'
    __database__ = 'coscup2015'
    #use_schemaless = True

    structure = { 
        'who': unicode,
        'id': unicode,
        'modified': list,
        'datetime': datetime.datetime
    }

    required_fields = [ 'who', 'id', 'modified', 'datetime' ]
