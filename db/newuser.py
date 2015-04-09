# -*- coding: utf-8 -*-
''' NewUser
    
'''
from mongokit import Document

class NewUser(Document):
    __collection__ = 'new_user'
    __database__ = 'coscup2015'
    use_schemaless = False

    structure = { 
        'id': unicode,
    }
    
    required_fields = [ 'id' ]
