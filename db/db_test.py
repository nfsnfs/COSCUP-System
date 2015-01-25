from mongokit import *
from permission import Permission

if __name__ == '__main__':

    connection = Connection()
    connection.register(Permission)
    permission = connection.Permission()

    for test in connection.Permission.find():
        print "====" + test['collection'] + "===="
        for test1 in test['fields']:
            print test1
            print '\t', "read", test['fields'][test1]['read']
            print '\t', "write", test['fields'][test1]['write']

    print connection.Permission.find_one({'collection': 'hello'})
    
