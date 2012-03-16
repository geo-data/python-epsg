# -*- coding: utf-8 -*-

import unittest
from epsg import Registry, schema, load
from util import getTestFile

class TestRegistryCreate(unittest.TestCase):

    def setUp(self):
        self.registry = Registry()
        xml = load.XML.FromFile(getTestFile())
        self.loader = load.Loader(xml)
        self.loader.load()

    def testCreate(self):
        registry = self.registry
        # perform the update
        registry.create(self.loader)

        # check there are the expected number of entries in the database
        entries = registry.session.query(schema.Identifier).all()
        # session.query(schema.DictionaryEntry).count() seems to fail when using `setup.py test`
        self.assertTrue(len(entries) == len(self.loader))

        # check the polymorphism is working
        geodetic_datum = registry.session.query(schema.DictionaryEntry).filter_by(identifier='urn:ogc:def:datum:EPSG::6277')[0]
        self.assertIsInstance(geodetic_datum, schema.GeodeticDatum)

        # check the loading of children is working
        self.assertIsInstance(geodetic_datum.domainOfValidity, schema.AreaOfUse)

if __name__ == '__main__':
    unittest.main(verbosity=2)
