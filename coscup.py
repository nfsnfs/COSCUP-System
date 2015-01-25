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
            return jsonify({ 'token': generate_token(message, config.TOKEN_SECRET, config.TOKEN_ALGO) })
    
    return jsonify({ 'exception': 'something went wrong' })

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
        return jsonify({ 'exception': 'something went wrong' })

@app.route('/user', methods=['GET', 'POST', 'PUT'])
def UserInfo():
    # get user id from token
    user = get_user_from_token(request.headers['Authorization'], config.TOKEN_SECRET, config.TOKEN_ALGO)
    connection = Connection()
    connection.register([Permission, UserData])

    if not user:
        return jsonify({ 'exception': 'token expired' }) 

    if request.method == 'GET':
        # get my user information
        try:
            response = {}
            userdata = connection.UserData.find_one({ 'id': user })
            
            permission = {}
            for role in userdata['role']:
                temp_perm = connection.Permission.find_one({ 'role': role })['fields']

                for key in temp_perm:
                    permission[key]['read'].append(temp_perm[key]['read'])
                    permission[key]['write'].append(temp_perm[key]['write'])

            for key in permission:
                if not permission[key]['read'] or 'self' in set(permission[key]['read']):
                    print key, userdata[key]
                    response[key] = userdata[key]
        except:
            jsonify({ 'exception': 'user not found' })

        return jsonify(response)

    elif request.method == 'POST':
        # insert my user information
        try:
            new_userdata = connection.UserData()
            
            permission = connection.Permission.find_one({ 'role': 'self' })['fields']

            for key in permission:
                if 'self' in permission[key]['write'] and key in request.json:
                    print key, request.json[key], type(request.json[key])
                    new_userdata[key] = request.json[key]

            new_userdata['id'] = user
            new_userdata['role'] = request.json['team']
            new_userdata.save()

        except RequireFieldError:
            return jsonify({ 'exception': 'missing field(s)' })
        except SchemaTypeError as e:
            return jsonify({ 'exception': 'field(s) type error' })
        except DuplicateKeyError:
            return jsonify({ 'exception': 'user existed' })
        except Exception:
            return jsonify({ 'exception': 'system error' })
        
        return jsonify({ 'msg': 'ok' })

    elif request.method == 'PUT':
        # update my user information
        try:
            userdata = connection.UserData.find_one({ 'id': user })

            permission = connection.Permission.find_one({ 'role': 'self' })['fields']

            for key in permission:
                if 'self' in permission[key]['write'] and key in request.json:
                    print key, request.json[key]
                    userdata[key] = request.json[key]
            
            userdata.save()
            
        except Exception as e:
            print e
            return jsonify({ 'exception': 'system error' })

        return jsonify({ 'msg': 'ok' })

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

