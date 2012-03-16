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
        self.assertEqual(len(keys), 17)

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

    def testAreaOfUse(self):
        obj = self.loader['urn:ogc:def:area:EPSG::1264']
        self.assertIsInstance(obj, schema.AreaOfUse)

    def testEllipsoid(self):
        obj = self.loader['urn:ogc:def:ellipsoid:EPSG::7001']
        self.assertIsInstance(obj, schema.Ellipsoid)

    def testGeodeticCRS(self):
        obj = self.loader['urn:ogc:def:crs:EPSG::4277']
        self.assertIsInstance(obj, schema.GeodeticCRS)

    def _testCoordinateSystem(self, urn, class_):
        obj = self.loader[urn]
        self.assertIsInstance(obj, class_)
        self.assertIsInstance(obj.axes, list)
        self.assertEqual(len(obj.axes), 2)
        for axis in obj.axes:
            self.assertIsInstance(axis, schema.CoordinateSystemAxis)
        
    def testEllipsoidalCS(self):
        self._testCoordinateSystem('urn:ogc:def:cs:EPSG::6422', schema.EllipsoidalCS)

    def testCartesianCS(self):
        self._testCoordinateSystem('urn:ogc:def:cs:EPSG::4400', schema.CartesianCS)
        
    def testCoordinateSystemAxis(self):
        obj = self.loader['urn:ogc:def:axis:EPSG::106']
        self.assertIsInstance(obj, schema.CoordinateSystemAxis)

    def testAxisName(self):
        obj = self.loader['urn:ogc:def:axis-name:EPSG::9901']
        self.assertIsInstance(obj, schema.AxisName)

    def testProjectedCRS(self):
        obj = self.loader['urn:ogc:def:crs:EPSG::27700']
        self.assertIsInstance(obj, schema.ProjectedCRS)
        self.assertIsInstance(obj.baseGeodeticCRS, schema.CoordinateReferenceSystem)
        self.assertIsInstance(obj.cartesianCS, schema.CartesianCS)

    def testLoad(self):
        expected_length = 16
        self.loader.load()
        self.assertEqual(len(self.loader.keys()), expected_length)
        self.assertEqual(len(self.loader.values()), expected_length)

if __name__ == '__main__':
    unittest.main(verbosity=2)
