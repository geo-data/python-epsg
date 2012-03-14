# -*- coding: utf-8 -*-

from epsg import load, schema
import unittest
from util import getTestFile

class TestXML(unittest.TestCase):

    def setUp(self):
        self.xml = load.XML.FromFile(getTestFile())

    def testKeys(self):
        keys = self.xml.keys()
        self.assertIsInstance(keys, list)
        self.assertEqual(len(keys), 5)

    def testContains(self):
        self.assertTrue('urn:ogc:def:datum:EPSG::6277' in self.xml)

    def testGetItem(self):
        from xml.dom.minidom import Element
        value = self.xml['urn:ogc:def:datum:EPSG::6277']
        self.assertIsInstance(value, Element)

class TestLoader(unittest.TestCase):

    def setUp(self):
        xml = load.XML.FromFile(getTestFile())
        self.loader = load.Loader(xml)

    def testPrimeMeridian(self):
        obj = self.loader['urn:ogc:def:meridian:EPSG::8901']
        self.assertIsInstance(obj, schema.PrimeMeridian)

    def testGeodeticDatum(self):
        obj = self.loader['urn:ogc:def:datum:EPSG::6277']
        self.assertIsInstance(obj, schema.GeodeticDatum)
    
    def testLoad(self):
        expected_length = 2
        self.loader.load()
        self.assertEqual(len(self.loader.keys()), expected_length)
        self.assertEqual(len(self.loader.values()), expected_length)
    
if __name__ == '__main__':
    unittest.main(verbosity=2)
