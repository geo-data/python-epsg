# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from epsg import schema
import unittest

class SchemaBuilder(object):
    """
    Creates schema objects for use in the tests
    """

    def buildObject(self, class_, properties):
        instance = class_(properties['identifier'], properties['name'])
        for attr in [attr for attr in properties if attr not in ('name', 'identifier')]:
            setattr(instance, attr, properties[attr])

        return instance

    def buildDictionaryEntry(self):
        return self.buildObject(schema.DictionaryEntry, {
                'identifier': 'unique:urn',
                'name': 'Test object'
                })

    def buildPrimeMeridian(self):
        return self.buildObject(schema.PrimeMeridian, {
                'identifier': 'urn:ogc:def:meridian:EPSG::8901',
                'name': 'Greenwich',
                'greenwichLongitude': '0'
                })

    def buildAreaOfUse(self):
        return self.buildObject(schema.AreaOfUse, {
                'identifier': 'urn:ogc:def:area:EPSG::1264',
                'name': 'UK - Great Britain; Isle of Man',
                'description': 'United Kingdom (UK) - Great Britain - England and Wales onshore, Scotland onshore and Western Isles nearshore; Isle of Man onshore.',
                'westBoundLongitude': '-8.73',
                'eastBoundLongitude': '1.83',
                'southBoundLatitude': '49.81',
                'northBoundLatitude': '60.89'
                })

    def buildGeodeticDatum(self):
        obj = self.buildObject(schema.GeodeticDatum, {
                'identifier': 'urn:ogc:def:datum:EPSG::6277',
                'name': 'OSGB 1936',
                'scope': 'Topographic mapping.',
                'realizationEpoch': '1936-01-01',
                'remarks': 'The average accuracy of OSTN02 compared to the old triangulation network (down to 3rd order) is 0.1m.',
                'anchorDefinition': u"""From April 2002 the datum is defined through the application of the OSTN02 transformation (tfm code 1039) to ETRS89. Prior to 2002, fundamental point: Herstmonceux, Latitude: 50°51'55.271"N, longitude: 0°20'45.882"E (of Greenwich).""",
                'type': 'geodetic'
                })

        obj.primeMeridian = self.buildPrimeMeridian()
        return obj

class TestDictionaryEntry(unittest.TestCase):
    """
    A base class used for testing schema objects
    """

    def setUp(self):
        # get the class name we are testing
        class_name = self.__class__.__name__[4:] # e.g. 'TestPrimeMeridian' -> 'PrimeMeridian'

        # set up the database engine and the database schema
        self.engine = create_engine('sqlite:///:memory:')
        self.Session = sessionmaker(self.engine)
        self.createDbSchema()

        # create an instance of the class to test
        builder = SchemaBuilder()
        self.obj = getattr(builder, 'build' + class_name)()

    def createDbSchema(self):
        session = self.Session()
        session.begin(subtransactions=True)

        conn = session.connection()
        schema.Base.metadata.create_all(conn)

        session.commit()

    def testInsert(self):
        session = self.Session()
        session.begin(subtransactions=True)
        session.add(self.obj)
        session.commit()

        obj = session.query(self.obj.__class__).filter_by(identifier=self.obj.identifier)[0]

        self.assertEqual(self.obj, obj)

class TestPrimeMeridian(TestDictionaryEntry):
    pass

class TestAreaOfUse(TestDictionaryEntry):
    pass

class TestGeodeticDatum(TestDictionaryEntry):
    pass

if __name__ == '__main__':
    unittest.main(verbosity=2)
