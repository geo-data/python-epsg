# -*- coding: utf-8 -*-

from epsg import service
import unittest

class TestService(unittest.TestCase):

    def setUp(self):
        self.service = service.Service()
        self.service.connect()

    def tearDown(self):
        self.service.close()

    def testGetLatestVersion(self):
        version = self.service.getLatestVersion()
        self.assertIsInstance(version, (str, unicode))
        self.assertTrue(version.startswith('urn:'))

    def testGetExportURL(self):
        url = self.service.getExportURL()
        self.assertIsInstance(url, (str, unicode))
        self.assertTrue(url.startswith('http'))

    def testExport(self):
        gml = self.service.export()
        self.assertIsInstance(gml, (str, unicode))
        self.assertTrue(gml.startswith('<?xml'))

if __name__ == '__main__':
    unittest.main(verbosity=2)
