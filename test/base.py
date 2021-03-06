"Base class for tests using unittest."

import argparse
import http.client
import json
import logging
import os
import re
import sqlite3
import sys
import unittest
import urllib

import jsonschema
import requests

SCHEMA_LINK_RX = re.compile(r'<([^>])+>; rel="([^"]+)')

JSON_MIMETYPE    = 'application/json'

DEFAULT_SETTINGS = {
    'base_url': 'http://127.0.0.1:5000', # DbShare server base url.
    'username': None,           # Needs to be set! Must have admin privileges.
    'apikey': None,             # Needs to be set! For the above user.
    'filename': '/tmp/test.sqlite3', # Sqlite3 file
    'dbname': 'test'
}

# The actual configuration values to use.
SETTINGS = {}

def process_args(filepath=None):
    """Process command-line arguments for this test suite.
    Reset the settingsuration and read the given settings file.
    Return the unused arguments.
    """
    if filepath is None:
        parser = argparse.ArgumentParser()
        parser.add_argument('-S', '--settings', dest='settings',
                            metavar='FILE', default='settings.json',
                            help='Settings file')
        parser.add_argument('unittest_args', nargs='*')
        options, args = parser.parse_known_args()
        filepath = options.settings
        args = [sys.argv[0]] + args
    else:
        args = sys.argv
    SETTINGS.update(DEFAULT_SETTINGS)
    with open(filepath) as infile:
        SETTINGS.update(json.load(infile))
    # Add API root url.
    SETTINGS['root_url'] = SETTINGS['base_url'] + '/api'
    return args

def run():
    argv = process_args()
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    logging.info(f"Root URL {SETTINGS['root_url']}")
    unittest.main(argv=argv)


class Base(unittest.TestCase):
    "Base class for DbShare test cases."

    def setUp(self):
        self.schemas = {}
        self.session = requests.Session()
        self.session.headers.update({'x-apikey': SETTINGS['apikey']})
        self.addCleanup(self.close_session)

    def close_session(self):
        self.session.close()

    @property
    def root(self):
        "Return the API root data."
        try:
            return self._root
        except AttributeError:
            response = self.session.get(SETTINGS['root_url'])
            self.assertEqual(response.status_code, http.client.OK)
            self._root = self.check_schema(response)
            return self._root

    def check_schema(self, response):
        """Check that there is a schema linked in the response headers,
        and that the response JSON data matches that schema.
        Return the response JSON.
        """
        self.assertEqual(response.status_code, http.client.OK)
        url = response.links['schema']['url']
        try:
            schema = self.schemas[url]
        except KeyError:
            r = self.session.get(url)
            self.assertEqual(r.status_code, http.client.OK)
            schema = r.json()
            self.schemas[url] = schema
        result = response.json()
        self.validate_schema(result, schema)
        return result

    def validate_schema(self, instance, schema):
        "Validate the JSON instance versus the given JSON schema."
        jsonschema.validate(instance=instance,
                            schema=schema,
                            format_checker=jsonschema.draft7_format_checker)

    def create_database(self):
        "Create an empty database."
        dbops = self.root['operations']['database']
        self.assertTrue('variables' in dbops['create'])
        self.assertTrue('dbname' in dbops['create']['variables'])
        url = dbops['create']['href'].format(dbname=SETTINGS['dbname'])
        response = self.session.put(url)
        self.assertEqual(response.status_code, http.client.OK)
        self.db_url = response.url
        self.addCleanup(self.cleanup)
        return response

    def upload_file(self):
        "Create a local Sqlite3 file and upload it."
        # Create the database in a local file.
        cnx = sqlite3.connect(SETTINGS['filename'])
        self.addCleanup(self.cleanup)
        # Create a table in the database.
        cnx.execute("CREATE TABLE t1 ("
                    "i INTEGER PRIMARY KEY,"
                    "r REAL,"
                    "t TEXT NOT NULL)")
        cnx.execute(f"CREATE VIEW v1"
                    f" AS SELECT r, t FROM t1"
                    " WHERE i>=2")
        with cnx:
            cnx.execute("INSERT INTO t1 (i,r,t)"
                        " VALUES (?,?,?)", (1, 2.1, 'a'))
            cnx.execute("INSERT INTO t1 (i,r,t)"
                        " VALUES (?,?,?)", (2, 0.5, 'b'))
            cnx.execute("INSERT INTO t1 (i,r,t)"
                        " VALUES (?,?,?)", (3, -1.5, 'c'))
        cnx.close()
        # Upload the database file.
        dbops = self.root['operations']['database']
        url = dbops['create']['href'].format(dbname=SETTINGS['dbname'])
        headers = {'Content-Type': 'application/x-sqlite3'}
        with open(SETTINGS['filename'], 'rb') as infile:
            response = self.session.put(url, data=infile, headers=headers)
            self.assertEqual(response.status_code, http.client.OK)
            self.db_url = response.url
        return response

    def cleanup(self):
        try:
            os.remove(SETTINGS['filename'])
        except OSError:
            pass
        try:
            self.session.delete(self.db_url)
        except AttributeError:
            pass
