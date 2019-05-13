"Test the DbShare API db endpoint."

import http.client

from dbshare.test.base import *


class Db(Base):
    "Test the DbShare API db endpoint."

    def test_create_scratch(self):
        "Test creation of a database from scratch, and its deletion."
        dbname = 'test'
        url = f"{CONFIG['root']}/db/{dbname}"
        response = self.session.put(url)
        self.assertEqual(response.status_code, http.client.OK)
        response = self.session.delete(url)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)

    def test_create_file(self):
        "Test creation of a database from file content, and its deletion."
        # XXX create a Sqlite3 file and upload
        dbname = 'test'
        url = f"{CONFIG['root']}/db/{dbname}"
        response = self.session.put(url)
        self.assertEqual(response.status_code, http.client.OK)
        response = self.session.delete(url)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)


if __name__ == '__main__':
    unittest.main()