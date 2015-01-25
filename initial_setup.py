#!/usr/bin/env python
# -*- coding: utf-8 -*-import sys

from pymongo import MongoClient

from db.permission import Permission
import permission_setting

db = MongoClient().coscup2015

def init_permission():
    db.permission.insert(permission_setting.self_permission)
    db.permission.insert(permission_setting.admin_permission)
    db.permission.insert(permission_setting.team_admin_permission)
    db.permission.insert(permission_setting.team_committee_permission)
    db.permission.insert(permission_setting.team_field_permission)
    db.permission.insert(permission_setting.team_sales_permission)
    db.permission.insert(permission_setting.team_cpr_permission)
    db.permission.insert(permission_setting.team_marketing_permission)
    db.permission.insert(permission_setting.team_accountant_permission)
    db.permission.insert(permission_setting.cashier_permission)
    db.permission.insert(permission_setting.team_archiving_permission)

if __name__ == '__main__':
    db.user_account.ensure_index('id', unique=True)
    db.user_data.ensure_index('id', unique=True)
    db.permission.ensure_index('role', unique=True)
    init_permission()
