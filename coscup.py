#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import traceback
import copy

import pymongo
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
from db.userdatalog import UserDataLog

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
        if is_correct_passwd(account['passwd'], passwd, config.SALT):
            expired_time = datetime.now() + timedelta(hours=1)
            message = { 'user': account['id'], 'expired': expired_time.strftime('%Y-%m-%d %H:%M:%S') }
            
            return jsonify({ 'token': generate_token(message, config.TOKEN_SECRET, config.TOKEN_ALGO), 
                    'role': account['role'], 'data': account['data'] })
    
    return jsonify({ 'exception': 'wrong id or password' })


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
POST/GET/PUT /user/<target_user>
if there is no target_user, this endpoint would GET/POST/PUT the his/her own data
'''
@app.route('/user', methods=['GET', 'POST', 'PUT'], defaults={ 'target_user': '' })
@app.route('/user/<target_user>', methods=['GET', 'POST', 'PUT'])
def userInfo(target_user):
    try:
        user = get_user_from_token(request.headers['Token'], config.TOKEN_SECRET, config.TOKEN_ALGO)
    except:
        return jsonify({ 'execption': 'token error' })

    self = False

    if target_user == '' or target_user == user:
        target_user = user
        self = True
        
    connection = Connection()
    connection.register([Permission, UserData, Account, UserDataLog])

    if request.method == 'GET':
        response = {}
        # get my user information
        try:
            userdata = connection.UserData.find_one({ 'id': user })
            target_userdata = connection.UserData.find_one({ 'id': target_user })
            permission = get_permission(target_userdata['role'])

            for key in permission:
                if key in target_userdata:
                    if check_read_permission(userdata['role'], permission[key]['read'], self):
                        response[key] = target_userdata[key]

        except Exception as e:
            print traceback.format_exc()
            return jsonify({ 'exception': 'user not found' })

        return jsonify(response)

    elif request.method == 'POST':
        # POST method only deals with 'self' data, instead of target_user
        # insert my user information
        try:
            account = connection.Account.find_one({ 'id': user })
            new_userdata = connection.UserData()
            
            permission = get_permission(['self'])

            for key in permission:
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
            print traceback.format_exc()
            return jsonify({ 'exception': 'system error' })
        
        # celery: deferred send mail to admin
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
        if r is None:
            return jsonify({ 'msg': 'ok', 'exception': 'cannot send welcome mail' })


        return jsonify({ 'msg': 'ok' })

    elif request.method == 'PUT':
        # update my user information
        try:
            userdata = connection.UserData.find_one({ 'id': user })
            target_userdata = connection.UserData.find_one({ 'id': target_user })
            old_target_userdata = copy.deepcopy(target_userdata)

            permission = get_permission(target_userdata['role'])

            log_entry = connection.UserDataLog()
            log_entry['who'] = user
            log_entry['id'] = target_user
            log_entry['modified'] = list()

            for key in permission:
                if check_write_permission(userdata['role'], permission[key]['write'], self) and key in request.json:
                    target_userdata[key] = request.json[key]
                    if target_userdata[key] != old_target_userdata[key]:
                        modified = { key: {'old': old_target_userdata[key], 'new': target_userdata[key]} }
                        log_entry['modified'].append(modified)
            
            target_userdata.save()
            log_entry['datetime'] = datetime.now()
            if log_entry['modified']:
                log_entry.save()
            
        except:
            print traceback.format_exc()
            return jsonify({ 'exception': 'system error' })

        return jsonify({ 'msg': 'ok' })


'''
Reset password
POST
'''
@app.route('/resetpasswd', methods=['POST'], defaults={ 'token': None })
@app.route('/resetpasswd/<token>', methods=['POST'])
def resetPassword(token):

    connection = Connection()
    connection.register([Account, UserData])

    if token is not None:
        # reset password 
        try:
            user = get_user_from_reset_passwd(token, config.TOKEN_SECRET, config.TOKEN_ALGO)
        except Exception as e:
            return jsonify({ 'exception': e })

        try:
            new_passwd = request.json['passwd']
        except:
            return jsonify({ 'exception': 'missing field(s)' })

        print user
        user_account = connection.Account.find_one({ 'id': user })
        user_account['passwd'] = hash_passwd(new_passwd, config.SALT)

        user_account.save()

        return jsonify({ 'msg': 'ok' })

    else:
        # send mail for resetting password
        try:
            user = request.json['user']
            #email = request.json['email']
        except:
            return jsonify({ 'exception': 'missing field(s)' })

        try:
            #user_account = connection.Account.find_one({ 'id': user })
            user_data = connection.UserData.find_one({ 'id': user })
            expired_time = datetime.now() + timedelta(hours=1)
            #token_data = { 'id': user_account['id'], 'email': user_account['email'], 
            #        'reset': 1, 'expired': expired_time.strftime('%Y-%m-%d %H:%M:%S') }
            token_data = { 'id': user_data['id'], 'email': user_data['email'], 
                    'reset': 1, 'expired': expired_time.strftime('%Y-%m-%d %H:%M:%S') }

            # celery: send mail to user
            notify_info = {
                    'user': user_data['id'],
                    'email': user_data['email'],
                    'url': config.BASEURL + '/?r=' + generate_token(token_data, config.TOKEN_SECRET, config.TOKEN_ALGO) + '#reset'
            }

            forget_passwd(notify_info)

            return jsonify({ 'msg': 'ok' })

        except:
            print traceback.format_exc()
            return jsonify({ 'exception': 'cannot find user' })

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
        print traceback.format_exc()
        return jsonify({ 'exception': 'system error' })

    return jsonify(response)


'''
Users
GET
'''
@app.route('/users/', methods=['GET'], defaults={ 'team': '' })
@app.route('/users/<team>', methods=['GET'])
def users(team):
    try:
        user = get_user_from_token(request.headers['Token'], config.TOKEN_SECRET, config.TOKEN_ALGO)
    except:
        return jsonify({ 'exception': 'token error' })

    connection = Connection()
    connection.register([UserData])

    response = { 'msg': 'ok', 'users': [] }

    if team == '':
        # get all users
        for user in connection.UserData.find():
            response['users'].append({ 'id': user['id'], 'team': user['team'] })

    else:
        # get for a certain team
        for user in connection.UserData.find({ 'team': team }):
            response['users'].append({ 'id': user['id'], 'team': user['team'] })

    return jsonify(response)

'''
Search
GET /search/?<type>=<value>
if value is empty, that means "" or not existed
'''
@app.route('/search/', methods=['GET'])
def search():
    try:
        user = get_user_from_token(request.headers['Token'], config.TOKEN_SECRET, config.TOKEN_ALGO)
    except:
        return jsonify({ 'exception': 'token error' })

    search_dict = {}
    search_list = []
    response = { 'users': [], 'msg': 'ok' }

    connection = Connection()
    connection.register([Permission, UserData])

    # get the role of current user
    try:
        userdata = connection.UserData.find_one({ 'id': user })
        role = userdata['role']
    except:
        jsonify({ 'exception': 'user not found'})

    # get the query parameters
    for key in request.args.keys():
        tmp_value = request.args.get(key, '')

        # workaround
        if key == 'team':
            # parse this value to list
            if tmp_value != '':
                search_dict.update({ key: {'$all': tmp_value.split(',')}})
                search_list.append(key)
            break;

        if tmp_value == 'null':
            search_dict.update({ '$or': [{key: {'$exists': False}}, {key: ''}]})
            search_list.append(key)
        elif tmp_value == 'true':
            search_dict.update({ key: true })
            search_list.append(key)
        elif tmp_value == 'false':
            search_dict.update({ key: false })
            search_list.append(key)
        elif tmp_value != '':
            search_dict.update({ key: tmp_value })
            search_list.append(key)

    try:
        result = connection.UserData.find(search_dict).sort('id', 1)
        for user_result in result:
            print user_result
            temp_userdata = {}

            if user_result['id'] == user:
                self = True
            else:
                self = False

            permission = get_permission(user_result['role'])

            if all(check_read_permission(userdata['role'], permission[search_key]['read'], self) for search_key in search_list):
                for key in permission:
                    if check_read_permission(userdata['role'], permission[key]['read'], self):
                        temp_userdata.update({ key: user_result.get(key, '') })
                
                response['users'].append(temp_userdata)

    except Exception as e:
       print traceback.format_exc()
       return jsonify({ 'exception': 'error' })

    return jsonify(response)

    '''
    try:
        user = get_user_from_token(request.headers['Token'], config.TOKEN_SECRET, config.TOKEN_ALGO)
    except:
        return jsonify({ 'exception': 'token error' })

    search_type = request.args.get('type', '')
    search_value = request.args.get('value', '')

    for test in request.args:
        print request.args[test]
    print search_type
    print search_value

    response = { 'result': [], 'msg': 'ok' }

    connection = Connection()
    connection.register([Permission, UserData])

    try:
        userdata = connection.UserData.find_one({ 'id': user })

        for user_result in connection.UserData.find({ search_type: search_value }):
            temp_userdata = {}
            self = False
            if user_result['id'] == user:
                self = True

            permission = get_permission(user_result['role'])

            if check_read_permission(userdata['role'], permission[search_type]['read'], self):
                for key in permission:
                    if check_read_permission(userdata['role'], permission[key]['read'], self):
                        if key in user_result:
                            temp_userdata[key] = user_result[key]
                        
                response['result'].append(temp_userdata)
    except Exception as e:
        print traceback.format_exc()
        return jsonify({ 'exception': 'error' })

    return jsonify(response)
    '''

'''
Permission
GET /perm/<role>
'''
@app.route('/perm/<role>', methods=['GET'])
def perm(role):
    response = {}

    connection = Connection()
    connection.register([Permission])

    try:
        permission = connection.Permission.find_one({ 'role': role })
        response = permission['fields']
        
    except Exception as e:
        print traceback.format_exc()
        return jsonify({ 'exception': 'error' })
    
    return jsonify(response)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

