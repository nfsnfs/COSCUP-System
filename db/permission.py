# -*- coding: utf-8 -*-
''' The ORM of permission collection which contains fields and collection

'collection' is the name of collection.

'fields' is the fields in this collection.
'fields' is a dict with the permission related to the fields.
For example, 'team-admin' means it can be read
    
'''
from mongokit import Document

class Permission(Document):
    __collection__ = 'permission'
    __database__ = 'coscup2015'
    use_schemaless = True
    structure = { 'role': basestring, 'fields': dict }

