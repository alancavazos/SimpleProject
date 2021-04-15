# -*- coding: utf-8 -*-

import requests
import requests.exceptions
import hashlib
import os
import sys
import argparse
import subprocess

parser = argparse.ArgumentParser(description='Testing REST API.')
parser.add_argument('--host', dest='HOSTNAME', default='DOCKER_HOST', help='Specify the hostname for the API (default: DOCKER_HOST)')
parser.add_argument('--port', dest='PORT', default='5000', help='Specify port on the API host (default: 5000)')
args = parser.parse_args()

HOSTNAME = args.HOSTNAME
PORT = args.PORT

if HOSTNAME == 'DOCKER_HOST':
    HOSTNAME = subprocess.check_output(["/sbin/ip route | awk '/default/ { print $3 }'"], shell=True).strip()

try:
    r = requests.get('http://' + HOSTNAME + ':' + PORT + '/md5/test')
except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.InvalidURL):
    print "Unable to reach API at address: %s:%s...\n" % (HOSTNAME, PORT)
    print "You can change the host or port using the --host and --port flags. Use -h for more info.\n"
    sys.exit(1)
else:
    print "Testing REST API on %s:%s...\n" % (HOSTNAME, PORT)

HASH_1 = '098f6bcd4621d373cade4e832627b4f6'   # 'test'
HASH_2 = '5eb63bbbe01eeed093cb22bb8f5acdc3'   # 'hello world'
FIB_SEQ = [0,1,1,2,3,5,8,13,21,34]
HTTP_ENCODE = "This%20is%20a%20longer%20string.%0D%0AIt%20even%20includes%20a%20newline..."

print "Testing API\n"

tests = [
    ('/md5/test',                 'GET',  [200], HASH_1),
    ('/md5/hello%20world',        'GET',  [200], HASH_2),
    ('/md5',                      'GET',  [400,404,405], None),
    ('/factorial/4',              'GET',  [200], 24),
    ('/factorial/5',              'GET',  [200], 120),
    ('/factorial/test',           'GET',  [400,404,405], None),
    ('/factorial/0',              'GET',  [200], 1),
    ('/fibonacci/8',              'GET',  [200], FIB_SEQ[:7]),
    ('/fibonacci/35',             'GET',  [200], FIB_SEQ),
    ('/fibonacci/test',           'GET',  [400,404,405], None),
    ('/fibonacci/1',              'GET',  [200], FIB_SEQ[:3]),
    ('/is-prime/1',               'GET',  [200], False),
    ('/is-prime/2',               'GET',  [200], True),
    ('/is-prime/5',               'GET',  [200], True),
    ('/is-prime/6',               'GET',  [200], False),
    ('/is-prime/37',              'GET',  [200], True),
    ('/slack-alert/test',         'GET',  [200], True),
    ('/slack-alert/'+HTTP_ENCODE, 'GET',  [200], True),
    ('/kv-retrieve/test1',        'GET',  [400,404,405], False),
    ('/kv-record/test1',          'POST', [200], True, 'test1', 'foobar'),
    ('/kv-retrieve/test1',        'GET',  [200], 'foobar'),
    ('/kv-record/test1',          'POST', [400,404,405,409], False, 'test1', 'foobaz'),
    ('/kv-record/test2',          'POST', [200], True, 'test2', '42'),
    ('/kv-record/test1',          'PUT',  [200], True, 'test1', 'lorem ipsum'),
    ('/kv-retrieve/test1',        'GET',  [200], 'lorem ipsum'),
    ('/kv-record/test3',          'PUT',  [400,404,405,409], False, 'test3', '84')
]

FAILED = 0
PASSED = 0
for t in tests:

    ENDPOINT = t[0]
    URL = 'http://' + HOSTNAME + ':' + PORT + ENDPOINT
    METHOD = t[1]
    STATUS = t[2]
    EXP_RESULT = t[3]

    if METHOD == 'GET':
        resp = requests.get(URL)
    else:
        JSON_PAYLOAD = {'key': t[4], 'value': t[5]}
        if METHOD == 'POST':
            resp = requests.post(URL, json=JSON_PAYLOAD)
        else:
            resp = requests.put(URL, json=JSON_PAYLOAD)

    print " * ", ENDPOINT[:28], "... ".ljust(35-len(ENDPOINT[:28])),

    if resp.status_code in STATUS:

        _no_json = "Cannot read JSON payload (failed to locate 'output' key)!"
        try:
            JSON_RESULT = resp.json().get('output', _no_json)
        except:
            JSON_RESULT = False

        if EXP_RESULT == None or JSON_RESULT == EXP_RESULT:
            print "Pass"
            PASSED += 1
        else:
            print "Fail"
            print "          - Expected output: '%s'" % str(EXP_RESULT)
            print "          - Actual output:   '%s'" % str(JSON_RESULT)
            print " DEBUG -- %s" % resp.json()
            FAILED += 1

    else:
        print "Fail"
        print "          - Expected HTTP status: %s" % flatten(STATUS)
        print "          - Actual HTTP status:   %i" % resp.status_code
        FAILED += 1

sys.exit(FAILED)
