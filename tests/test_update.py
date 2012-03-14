# -*- coding: utf-8 -*-

from epsg import update, load, schema
from util import getTestFile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import unittest

class TestUpdate(unittest.TestCase):

    def setUp(self):
        xml = load.XML.FromFile(getTestFile())
        self.loader = load.Loader(xml)
        self.loader.load()
        self.engine = create_engine('sqlite:///:memory:')
        self.Session = sessionmaker(self.engine)

    def testUpdate(self):
        # perform the update
        update.update(self.loader.values(), self.engine)

        # start a session for testing
        session = self.Session()
        session.begin(subtransactions=True)

        # check there are the correct number of entries in the database
        entries = session.query(schema.DictionaryEntry).all()
        # session.query(schema.DictionaryEntry).count() seems to fail when using `setup.py test`
        self.assertEqual(len(entries), len(self.loader))

        # check the polymorphism is working
        geodetic_datum = session.query(schema.DictionaryEntry).filter_by(identifier='urn:ogc:def:datum:EPSG::6277')[0]
        self.assertIsInstance(geodetic_datum, schema.GeodeticDatum)

        # check the loading of children is working
        self.assertIsInstance(geodetic_datum.domainOfValidity, schema.AreaOfUse)

        # all done
        session.commit()

if __name__ == '__main__':
    unittest.main(verbosity=2)
