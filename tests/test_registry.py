# -*- coding: utf-8 -*-

import unittest
from epsg import Registry, schema, load
from util import getTestFile, SchemaBuilder

class TestRegistryInit(unittest.TestCase):

    def setUp(self):
        self.registry = Registry(loader=False)
        xml = load.XML.FromFile(getTestFile())
        self.loader = load.XMLLoader(xml)
        self.loader.load()

    def testInit(self):
        registry = self.registry
        # perform the update
        registry.init(self.loader)

        # check there are the expected number of entries in the database
        entries = registry.session.query(schema.Identifier).all()
        # session.query(schema.DictionaryEntry).count() seems to fail when using `setup.py test`
        self.assertTrue(len(entries) == len(self.loader))

        # check the polymorphism is working
        geodetic_datum = registry.session.query(schema.DictionaryEntry).filter_by(identifier='urn:ogc:def:datum:EPSG::6277')[0]
        self.assertIsInstance(geodetic_datum, schema.GeodeticDatum)

        # check the loading of children is working
        self.assertIsInstance(geodetic_datum.domainOfValidity, schema.AreaOfUse)

class TestRegistry(unittest.TestCase):

    def setUp(self):
        xml = load.XML.FromFile(getTestFile())
        loader = load.XMLLoader(xml)
        loader.load()
        self.registry = Registry(loader=loader)

    def testGetItem(self):
        value = self.registry['urn:ogc:def:crs:EPSG::27700']
        self.assertIsInstance(value, schema.ProjectedCRS)

        with self.assertRaises(TypeError):
            self.registry[42]

        with self.assertRaises(KeyError):
            self.registry['bad key']

    def testSetItem(self):
        builder = SchemaBuilder()
        key = 'urn:ogc:def:area:EPSG::0001'
        value = builder.buildAreaOfUse()
        value.identifier = key  # replace the id with one not in the test database

        self.registry[key] = value
        self.assertEqual(value, self.registry[key])

    def testDelItem(self):
        del self.registry['urn:ogc:def:crs:EPSG::27700']
        with self.assertRaises(KeyError):
            self.registry['urn:ogc:def:crs:EPSG::27700']

    def testLen(self):
        self.assertEqual(45, len(self.registry))

    def testUpdate(self):
        registry2 = Registry(loader=False)
        registry2.update(self.registry)
        self.assertEqual(len(self.registry), len(registry2))

    def testContains(self):
        self.assertIn('urn:ogc:def:crs:EPSG::27700', self.registry)
        self.assertNotIn('invalid key', self.registry)

    def testIter(self):
        count = 0
        for key in self.registry:
            self.assertIsInstance(key, (str, unicode))
            count += 1
        self.assertEqual(45, count)

    def testItervalues(self):
        count = 0
        for value in self.registry.itervalues():
            self.assertIsInstance(value, schema.Identifier)
            count += 1
        self.assertEqual(45, count)

    def testIteritems(self):
        count = 0
        for item in self.registry.iteritems():
            self.assertIsInstance(item, tuple)
            self.assertEqual(2, len(item))
            key, value = item
            self.assertIsInstance(key, (str, unicode))
            self.assertIsInstance(value, schema.Identifier)
            count += 1
        self.assertEqual(45, count)

if __name__ == '__main__':
    unittest.main(verbosity=2)
