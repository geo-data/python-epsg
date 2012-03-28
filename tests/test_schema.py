# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from epsg import schema
import unittest
from util import SchemaBuilder

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

        results = list(session.query(schema.Identifier).filter_by(identifier=self.obj.identifier))
        self.assertEqual(len(results), 1)
        obj = results[0]
        self.assertEqual(self.obj, obj)

class TestPrimeMeridian(TestDictionaryEntry):
    pass

class TestAreaOfUse(TestDictionaryEntry):
    pass

class TestEllipsoid(TestDictionaryEntry):
    pass

class TestGeodeticDatum(TestDictionaryEntry):
    pass

class TestVerticalDatum(TestDictionaryEntry):
    pass

class TestEngineeringDatum(TestDictionaryEntry):
    pass

class TestGeodeticCRS(TestDictionaryEntry):
    pass

class TestEllipsoidalCS(TestDictionaryEntry):
    pass

class TestCartesianCS(TestDictionaryEntry):
    pass

class TestVerticalCS(TestDictionaryEntry):
    pass

class TestSphericalCS(TestDictionaryEntry):
    pass

class TestCoordinateSystemAxis(TestDictionaryEntry):
    pass

class TestAxisName(TestDictionaryEntry):
    pass

class TestProjectedCRS(TestDictionaryEntry):
    pass

class TestVerticalCRS(TestDictionaryEntry):
    pass

class TestEngineeringCRS(TestDictionaryEntry):
    pass

class TestCompoundCRS(TestDictionaryEntry):
    pass

if __name__ == '__main__':
    unittest.main(verbosity=2)
