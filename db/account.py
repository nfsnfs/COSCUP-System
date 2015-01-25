#!/usr/bin/env python
# -*- coding: utf-8 -*-
''' The ORM of account collection which contains fields and collection

'id'
'passwd'

'''
from mongokit import Document

class Account(Document):
    __collection__ = 'user_account'
    __database__ = 'coscup2015'
    #use_schemaless = True
    structure = { 'id': basestring, 'passwd': basestring, 'role': list }


