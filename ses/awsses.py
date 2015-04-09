# -*- coding: utf-8 -*-

from jinja2 import Environment, FileSystemLoader
from boto.ses.connection import SESConnection
from config import AWSID, AWSKEY, TEMPLATE
from email.header import Header

conn = SESConnection(AWSID, AWSKEY)
env = Environment(loader=FileSystemLoader(TEMPLATE))

COSCUP_TEAM_ADMIN = u'COSCUP 行政組'
COSCUP_TEAM_ADMIN_MAIL = u'secretary@coscup.org'

def mail_header(name, mail):
    ''' Encode header to base64
    :param str name: user name
    :param str mail: user mail
    :rtype: string
    :returns: a string of "name <mail>" in base64.
    '''
    return '"%s" <%s>' % (Header(name, 'utf-8'), mail)

def send_first(info):

    try:
        template = env.get_template('coscup_first.html')

        r = conn.send_email(
                source=mail_header(COSCUP_TEAM_ADMIN, COSCUP_TEAM_ADMIN_MAIL),
                subject=u'COSCUP2015 請先完成資料登錄 - {nickname}'.format(**info),
                to_addresses='{email}'.format(**info),
                format='html',
                body=template.render(**info),
        )
	print r
    except Exception as e:
        print e
        return None
        
    return r

def send_welcome(info):
    
    try:
        template = env.get_template('coscup_welcome.html')
        r = conn.send_email(
                source=mail_header(COSCUP_TEAM_ADMIN, COSCUP_TEAM_ADMIN_MAIL),
                subject=u'COSCUP2015 歡迎你 - {nickname}'.format(**info),
                to_addresses='{email}'.format(**info),
                format='html',
                body=template.render(**info),
        )
        print r
    except Exception as e:
        print e
        return None

    return r

def send_new_user_to_admin(info):

    try:
        template = env.get_template('new_user_to_admin.html')

        r = conn.send_email(
                source=mail_header(COSCUP_TEAM_ADMIN, COSCUP_TEAM_ADMIN_MAIL),
                subject=u'新註冊會員 - {date}'.format(**info),
                to_addresses='{email}'.format(**info),
                format='html',
                body=template.render(**info),
        )
        print r
    except Exception as e:
        print e
        return None

    return r

def send_forget_passwd(info):

    try:
        template = env.get_template('forget_passwd.html')
        
        r = conn.send_email(
                source=u'忘記密碼',
                to_addresses='{email}'.format(**info),
                format='html',
                body=template.render(**info),
        )
        print r
    except Exception as e:
        print e
        return None
