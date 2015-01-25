#!/usr/bin/env python
# -*- coding: utf-8 -*-import sys

from flask import Flask, jsonify, request, abort
from mongokit import *
from datetime import datetime, timedelta
from pymongo.errors import DuplicateKeyError

from util.crypto import *
from db.permission import Permission
from db.account import Account
from db.userdata import UserData

import config

app = Flask(__name__)
api_ver = r'0.1'

'''
Welcome
'''
@app.route('/')
def hello_coscup():
    return jsonify({ 'msg': 'Hello COSCUP', 'ver': api_ver })

'''
Login 
POST /login
'''
@app.route('/login', methods=['POST'])
def login():
    if not request.json or not all (key in request.json for key in ('user', 'passwd')):
        abort(400)

    user = request.json['user']
    passwd = request.json['passwd']

    connection = Connection()
    connection.register([Account])

    account = connection.Account.find_one({'id': user})
    if account:
        # check password
        if hash_passwd(passwd, config.SALT) == account['passwd']:
            expired_time = datetime.now() + timedelta(hours=1)
            message = { 'user': account['id'], 'expired': expired_time.strftime('%Y-%m-%d %H:%M:%S') }
            return jsonify({ 'token': generate_token(message, config.SECRET, config.ALGO) })
    
    return jsonify({ 'msg': 'something went wrong' })

''' 
Apply account
POST /apply
'''
@app.route('/apply', methods=['POST'])
def apply():
    if not request.json or not all (key in request.json for key in ('user', 'passwd')):
        abort(400)
    
    user = request.json['user']
    passwd = request.json['passwd']

    connection = Connection()
    connection.register([Account])
    
    if not connection.Account.find_one({ 'id': user }):
        new_account = connection.Account()
        new_account['id'] = user
        new_account['passwd'] = hash_passwd(passwd, config.SALT)
        new_account.save()

        return jsonify({ 'msg': 'ok' })
    else:
        return jsonify({ 'msg': 'something went wrong' })

@app.route('/user', methods=['GET', 'POST', 'PUT'])
def UserInfo():
    # get user id from token
    user = get_user_from_token(request.headers['Authorization'], config.SECRET, config.ALGO)
    connection = Connection()
    connection.register([Permission, UserData])
    permission = connection.Permission.find_one({ 'collection': 'user_data' })['fields']

    if not user:
        return jsonify({ 'msg': 'token expired' }) 

    if request.method == 'GET':
        # get my user information
        try:
            response = {}
            userdata = connection.UserData.find_one({ 'id': user })

            for key in permission:
                if not permission[key]['read'] or 'self' in permission[key]['read']:
                    print key, userdata[key]
                    response[key] = userdata[key]
        except:
            jsonify({ 'msg': 'user not found' })

        return jsonify(response)

    elif request.method == 'POST':
        # insert my user information
        try:
            new_userdata = connection.UserData()

            for key in permission:
                if 'self' in permission[key]['write']:
                    print key, request.json[key]
                    new_userdata[key] = request.json[key]

            new_userdata['id'] = user
            new_userdata['team-admin'] = [ ]
            new_userdata.save()

        except RequireFieldError:
            return jsonify({ 'msg': 'missing field(s)' })
        except SchemaTypeError:
            return jsonify({ 'msg': 'field(s) type error' })
        except DuplicateKeyError:
            return jsonify({ 'msg': 'user existed' })
        except Exception:
            return jsonify({ 'msg': 'system error' })
        
        return jsonify({ 'msg': 'ok' })

    elif request.method == 'PUT':
        # update my user information
        try:
            userdata = connection.UserData.find_one({ 'id': user })

            for key in permission:
                if 'self' in permission[key]['write']:
                    print key, request.json[key]
                    userdata[key] = request.json[key]
            
            userdata.save()
            
        except Exception as e:
            print e
            return jsonify({ 'msg': 'system error' })

        return jsonify({ 'msg': 'ok' })

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

