#!/usr/bin/env python
# -*- coding: utf-8 -*-
''' UserData
    
'''
from mongokit import Document

class UserData(Document):
    __collection__ = 'user_data'
    __database__ = 'coscup2015'
    use_schemaless = True

    structure = { 
        'id': basestring,
        'team': list,
        'team-lead': list,
        'last_name': unicode,
        'first_name': unicode,
        'nickname': unicode,
        'gender': basestring,
        'email': basestring,
        'phone': basestring,
        't-shirt': basestring,
        'food': unicode,
        'certificate': bool,
        'accommodation': bool,
        'traffic': bool,
        'origin': unicode,
        'birthday': int,
        'new': bool,
        'language': list,
        'skill': list,
        'others': unicode,
        'project': list,
        'role': list,
        'redmine': basestring,
        'comment': unicode
    }
    
    required_fields = [ 'id', 'team', 'last_name', 'first_name',
        'nickname', 'gender', 'email', 'phone', 't-shirt', 'food', 'certificate',
        'accommodation', 'traffic', 'origin', 'birthday', 'new', 'language', 
        'skill', 'others', 'redmine' ]
