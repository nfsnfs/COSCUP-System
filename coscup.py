#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

from flask import Flask, jsonify, request, abort
from mongokit import *
from datetime import datetime, timedelta
from pymongo.errors import DuplicateKeyError

from util.crypto import *
from util.userperm import *
from tasks import *
from db.permission import Permission
from db.account import Account
from db.userdata import UserData

import ses.awsses
import config

app = Flask(__name__)
api_ver = r'0.1'

sys.stdout = sys.stderr

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
            
            return jsonify({ 'token': generate_token(message, config.TOKEN_SECRET, config.TOKEN_ALGO), 
                    'role': account['role'], 'data': account['data'] })
    
    return jsonify({ 'exception': 'something went wrong' })

''' 
Apply account
POST /apply
'''
@app.route('/apply/<temp_token>', methods=['POST', 'GET'])
def apply(temp_token):
    # decrypt the token and get the email 
    try:
        user_temp = decrypt_token(temp_token, config.TOKEN_SECRET, config.TOKEN_ALGO)
    except:
        return jsonify({ 'exception': 'token error' })

    if request.method == 'POST':
        if not request.json or not all (key in request.json for key in ('user', 'passwd', 'email')):
            abort(400)

        connection = Connection()
        connection.register([Account])
        # check if the token is used
        if connection.Account.find_one({ 'email': user_temp['email'] }):
            return jsonify({ 'exception': 'token was used' })

        user = request.json['user']
        passwd = request.json['passwd']
        email = user_temp['email']
        role = user_temp['team']
        data = False

        
        if not connection.Account.find_one({ 'id': user }):
            new_account = connection.Account()

            new_account['id'] = user
            new_account['passwd'] = hash_passwd(passwd, config.SALT)
            new_account['email'] = email
            new_account['role'] = role
            new_account['data'] = data
            new_account.save()

            return jsonify({ 'msg': 'ok' })
        else:
            return jsonify({ 'exception': 'account existed' })

    elif request.method == 'GET':
        return jsonify({ 'email': user_temp['email'], 'team': user_temp['team'] })

'''
User personal information detail
POST/GET/PUT /user
'''
@app.route('/user', methods=['GET', 'POST', 'PUT'])
def userInfo():
    try:
        user = get_user_from_token(request.headers['Token'], config.TOKEN_SECRET, config.TOKEN_ALGO)
    except:
        return jsonify({ 'execption': 'token error' })

    connection = Connection()
    connection.register([Permission, UserData, Account])

    if request.method == 'GET':
        # get my user information
        try:
            response = {}
            userdata = connection.UserData.find_one({ 'id': user })
            permission = get_permission(userdata['role'])
            #print userdata

            for key in permission:
                if not permission[key]['read'] or 'self' in set(permission[key]['read']):
                    #print key, userdata[key]
                    if key in userdata:
                        response[key] = userdata[key]

        except Exception as e:
            print e
            return jsonify({ 'exception': 'user not found' })

        return jsonify(response)

    elif request.method == 'POST':
        # insert my user information
        try:
            account = connection.Account.find_one({ 'id': user })
            new_userdata = connection.UserData()
            
            permission = get_permission(['self'])

            for key in permission:
                print key
                if 'self' in permission[key]['write'] and key in request.json:
                    new_userdata[key] = request.json[key]

            role = list(set(account['role'] + request.json['team']))

            new_userdata['id'] = user
            new_userdata['role'] = role
            new_userdata.save()

            account['role'] = role
            account['data'] = True
            account.save()

        except RequireFieldError:
            return jsonify({ 'exception': 'missing field(s)' })
        except SchemaTypeError:
            return jsonify({ 'exception': 'field(s) type error' })
        except DuplicateKeyError:
            return jsonify({ 'exception': 'user existed' })
        except Exception as e:
            print e
            import traceback
            print traceback.format_exc()
            return jsonify({ 'exception': 'system error' })
        
        # deferred send mail to admin
        notify_info = {
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'id': user,
            'target_email': new_userdata['email'],
            'redmine': new_userdata['redmine'],
            'team': new_userdata['team'],
            'first_name': new_userdata['first_name'],
            'last_name': new_userdata['last_name']
        }

        for mail in config.ADMIN_EMAIL:
            notify_info['email'] = mail
            notify_new_user_to_admin.delay(notify_info)

        # send welcome mail
        info = { 'email': new_userdata['email'], 'nickname': new_userdata['nickname'] }
        r = ses.awsses.send_welcome(info)
        if r == None:
            return jsonify({ 'msg': 'ok', 'exception': 'cannot send welcome mail' })

        return jsonify({ 'msg': 'ok' })

    elif request.method == 'PUT':
        # update my user information
        try:
            userdata = connection.UserData.find_one({ 'id': user })

            permission = get_permission(['self'])

            for key in permission:
                if 'self' in permission[key]['write'] and key in request.json:
                   userdata[key] = request.json[key]
            
            userdata.save()
            
        except Exception:
            return jsonify({ 'exception': 'system error' })

        return jsonify({ 'msg': 'ok' })


'''
Reset password
POST
'''
@app.route('/resetpasswd', methods=['POST'])
def resetPassword():
    try:
        user = request.json['user']
        email = request.json['email']
    except:
        return jsonify({ 'exception': 'missing field(s)' })

    connection = Connection()
    connection.register([UserData])
    connection.UserData.find({ 'user': user, 'email': email })

    # todo: send mail to user

    return jsonify({ 'msg': 'ok'})

    
'''
Send First Mail
POST
'''
@app.route('/invite', methods=['POST'])
def send_checkin_mail():
    try:
        user = get_user_from_token(request.headers['Token'], config.TOKEN_SECRET, config.TOKEN_ALGO)
    except:
        return jsonify({ 'exception': 'token error' })

    response = {'msg': 'ok', 'email': []}

    # only admin can do this !
    connection = Connection()
    connection.register([Account])
    account = connection.Account.find_one({ 'id': user })

    try:
        if 'admin' in account['role']:
            for tmp in request.json:
                #print tmp
                url = config.BASEURL + '/?apply=' 
                url += generate_token(tmp, config.TOKEN_SECRET, config.TOKEN_ALGO)
                url += '#apply'
                tmp['url'] = url
                r = ses.awsses.send_first(tmp)
                if r != None:
                    response['email'].append(tmp['email'])
                else:
                    raise Exception('something error')

    except Exception as e:
        print e
        return jsonify({ 'exception': 'system error' })

    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

