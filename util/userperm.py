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

    return permission

def check_read_permission(roles, target_perm, self):
    roles_set = set(roles)
    target_set = set(target_perm)

    if self:
        return 'self' in target_set or not target_set
    else:
        return roles_set.intersection(target_set) or not target_set

def check_write_permission(roles, target_perm, self):
    roles_set = set(roles)
    target_set = set(target_perm)

    if self:
        roles_set.add('self')

    return roles_set.intersection(target_set)

