# -*- coding: utf-8 -*-

from db.permission import Permission
from mongokit import *

'''
Get the permission of the target data
get_permission(roles)
- roles: list field of the target UserData
'''
def get_permission(roles):
    
    connection = Connection()
    connection.register([Permission])

    permission = {}
    for role in roles:
        temp_perm = connection.Permission.find_one({ 'role': role })['fields']

        for key in temp_perm:
            try:
                assert key in permission

            except AssertionError:
                permission[key] = { 'read': [], 'write': [] }

            finally:
                permission[key]['read'].extend(temp_perm[key]['read'])
                permission[key]['write'].extend(temp_perm[key]['write'])

    print permission
    return permission
