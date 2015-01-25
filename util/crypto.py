#!/usr/bin/env python
# -*- coding: utf-8 -*-
import hashlib
import jwt
import json
from base64 import b64encode, b64decode
from datetime import datetime

PADDING = r'%'

def hash_passwd(passwd, salt):
    return hashlib.sha512(salt.encode() + passwd.encode()).hexdigest()

def generate_token(json_dict, secret, algo):
    token = jwt.encode(json_dict, secret, algo)
    return token

def decrypt_token(token, secret, algo):
    json_dict = jwt.decode(token, secret, algo)
    return json_dict

def get_user_from_token(token, secret, algo):
    json_dict = decrypt_token(token, secret, algo)
    user = json_dict['user']
    expired_time = datetime.strptime(json_dict['expired'], "%Y-%m-%d %H:%M:%S")

    if datetime.now() > expired_time:
        return None

    return user


