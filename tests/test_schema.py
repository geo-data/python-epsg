# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from epsg import schema
import unittest

class SchemaBuilder(object):
    """
    Creates schema objects for use in the tests
    """

    def buildObject(self, class_, constructor_args, properties):
        instance = class_(*[properties[arg] for arg in constructor_args])
        for attr in [attr for attr in properties if attr not in constructor_args]:
            setattr(instance, attr, properties[attr])

        return instance

    def buildDictionaryEntry(self, class_=schema.DictionaryEntry, properties=None):
        if properties is None:
            properties = {
                'identifier': 'unique:urn',
                'name': 'Test object'
                }
        return self.buildObject(class_, ['identifier', 'name'], properties)

    def buildPrimeMeridian(self):
        return self.buildDictionaryEntry(schema.PrimeMeridian, {
                'identifier': 'urn:ogc:def:meridian:EPSG::8901',
                'name': 'Greenwich',
                'greenwichLongitude': '0'
                })

    def buildEllipsoid(self):
        return self.buildDictionaryEntry(schema.Ellipsoid, {
                'identifier': 'urn:ogc:def:ellipsoid:EPSG::7001',
                'name': 'Airy 1830',
                'informationSource': 'Ordnance Survey of Great Britain.',
                'remarks': u'Original definition is a=20923713, b=20853810 feet of 1796. 1/f is given to 7 decimal places. For the 1936 retriangulation OSGB defines the relationship of 10 feet of 1796 to the International metre through ([10^0.48401603]/10) exactly = 0.3048007491...',
                'semiMajorAxis': '6377563.396',
                'inverseFlattening': '299.3249646'
                })

    def buildAreaOfUse(self):
        return self.buildDictionaryEntry(schema.AreaOfUse, {
                'identifier': 'urn:ogc:def:area:EPSG::1264',
                'name': 'UK - Great Britain; Isle of Man',
                'description': 'United Kingdom (UK) - Great Britain - England and Wales onshore, Scotland onshore and Western Isles nearshore; Isle of Man onshore.',
                'westBoundLongitude': '-8.73',
                'eastBoundLongitude': '1.83',
                'southBoundLatitude': '49.81',
                'northBoundLatitude': '60.89'
                })

    def buildGeodeticDatum(self):
        obj = self.buildDictionaryEntry(schema.GeodeticDatum, {
                'identifier': 'urn:ogc:def:datum:EPSG::6277',
                'name': 'OSGB 1936',
                'scope': 'Topographic mapping.',
                'realizationEpoch': '1936-01-01',
                'remarks': 'The average accuracy of OSTN02 compared to the old triangulation network (down to 3rd order) is 0.1m.',
                'anchorDefinition': u"""From April 2002 the datum is defined through the application of the OSTN02 transformation (tfm code 1039) to ETRS89. Prior to 2002, fundamental point: Herstmonceux, Latitude: 50°51'55.271"N, longitude: 0°20'45.882"E (of Greenwich).""",
                'type': 'geodetic'
                })

        obj.primeMeridian = self.buildPrimeMeridian()
        obj.domainOfValidity = self.buildAreaOfUse()
        return obj

    def buildVerticalDatum(self):
        obj = self.buildDictionaryEntry(schema.VerticalDatum, {
                'identifier': 'urn:ogc:def:datum:EPSG::1027',
                'name': 'EGM2008 geoid',
                'scope': 'Geodesy.',
                'realizationEpoch': '2008-01-01',
                'anchorDefinition': u"""WGS 84 ellipsoid.""",
                'type': 'vertical',
                'informationSource': 'http://earth-info.nga.mil/GandG/wgs84/gravitymod/egm2008/egm08_wgs84.html'
                })
        return obj

    def buildEngineeringDatum(self):
        obj = self.buildDictionaryEntry(schema.EngineeringDatum, {
                'identifier': 'urn:ogc:def:datum:EPSG::9300',
                'name': 'Astra Minas',
                'scope': 'Oil industry mapping.',
                'anchorDefinition': u"""Origin at 45°59'54.79"S, 67°34'38.94"W (of Greenwich).""",
                'type': 'engineering'
                })
        return obj

    def buildGeodeticCRS(self):
        obj = self.buildDictionaryEntry(schema.GeodeticCRS, {
                'identifier': 'urn:ogc:def:crs:EPSG::4277',
                'name': 'OSGB 1936',
                'scope': 'Geodetic survey.',
                'type': 'geographic 2D'
                })

        obj.geodeticDatum = self.buildGeodeticDatum()
        obj.domainOfValidity = obj.geodeticDatum.domainOfValidity
        obj.ellipsoidalCS = self.buildEllipsoidalCS()
        return obj

    def buildEllipsoidalCS(self):
        properties = {
            'identifier': 'urn:ogc:def:cs:EPSG::6422',
            'name': 'Ellipsoidal 2D CS. Axes: latitude, longitude. Orientations: north, east. UoM: degree',
            'type': 'ellipsoidal',
            'remarks': 'Coordinates referenced to this CS are in degrees. Any degree representation (e.g. DMSH, decimal, etc.) may be used but that used must be declared for the user by the supplier of data. Used in geographic 2D coordinate reference systems.',
            'informationSource': 'OGP',
            'axes': [{
                    'identifier': 'urn:ogc:def:axis:EPSG::107',
                    'axisAbbrev': 'Long',
                    'axisDirection': 'east',
                    'descriptionReference': {
                        'identifier': 'urn:ogc:def:axis-name:EPSG::9902',
                        'name': 'Geodetic longitude',
                        'remarks': 'Used in geographic 2D and geographic 3D coordinate reference systems.',
                        'description': 'Angle from the prime meridian plane to the meridian plane passing through the given point, eastwards usually treated as positive.',
                        'informationSource': 'OGP'
                        }
                    }, {
                    'identifier': 'urn:ogc:def:axis:EPSG::106',
                    'axisAbbrev': 'Lat',
                    'axisDirection': 'north'
                    }
                     ]
            }

        return self.buildCoordinateSystem(schema.EllipsoidalCS, properties)

    def buildCartesianCS(self):
        properties = {
            'identifier': 'urn:ogc:def:cs:EPSG::4400',
            'name': 'Cartesian 2D CS. Axes: easting, northing (E,N). Orientations: east, north. UoM: m',
            'type': 'Cartesian',
            'remarks': 'Used in projected and engineering coordinate reference systems.',
            'informationSource': 'OGP',
            'axes': [{
                    'identifier': 'urn:ogc:def:axis:EPSG::1',
                    'axisAbbrev': 'E',
                    'axisDirection': 'east',
                    'descriptionReference': {
                        'identifier': 'urn:ogc:def:axis-name:EPSG::9906',
                        'name': 'Easting',
                        'description': 'East pointing axis used in 2D projected coordinate systems.',
                        'informationSource': 'OGP'
                        }
                    }, {
                    'identifier': 'urn:ogc:def:axis:EPSG::2',
                    'axisAbbrev': 'N',
                    'axisDirection': 'north',
                    'descriptionReference': {
                        'identifier': 'urn:ogc:def:axis-name:EPSG::9907',
                        'name': 'Northing',
                        'description': 'North pointing axis used in 2D projected coordinate systems.',
                        'informationSource': 'OGP'
                        }
                    }
                      ]
            }

        return self.buildCoordinateSystem(schema.CartesianCS, properties)

    def buildVerticalCS(self):
        properties = {
            'identifier': 'urn:ogc:def:cs:EPSG::6499',
            'name': 'Vertical CS. Axis: height (H). Orientation: up. UoM: m.',
            'type': 'vertical',
            'remarks': 'Used in vertical coordinate reference systems.',
            'informationSource': 'OGP',
            'axes': [{
                    'identifier': 'urn:ogc:def:axis:EPSG::114',
                    'axisAbbrev': 'H',
                    'axisDirection': 'up',
                    'descriptionReference': {
                        'identifier': 'urn:ogc:def:axis-name:EPSG::9904',
                        'name': 'Gravity-related height',
                        'description': "Height influenced by the Earth's gravity field.  In particular, orthometric height or normal height which are both approximations of the distance of a point above sea level. Positive upwards.",
                        'informationSource': 'ISO 19111 "Geographical information - Spatial referencing by coordinates".',
                        'remarks': 'Used in a 1D vertical coordinate system.'
                        }
                    }
                      ]
            }

        return self.buildCoordinateSystem(schema.VerticalCS, properties)

    def buildSphericalCS(self):
        properties = {
            'identifier': 'urn:ogc:def:cs:EPSG::6404',
            'name': 'Spherical 3D CS. Axes: latitude, longitude, radius. Orientations: north, east, up. UoM: degrees, degrees, metres.',
            'type': 'spherical',
            'remarks': 'Used in geocentric 3D coordinate reference systems.',
            'informationSource': 'Open GIS Consortium',
            'axes': [{
                    'identifier': 'urn:ogc:def:axis:EPSG::60',
                    'axisAbbrev': 'Lat',
                    'axisDirection': 'north',
                    'descriptionReference': {
                        'identifier': 'urn:ogc:def:axis-name:EPSG::9926',
                        'name': 'Spherical latitude',
                        'description': "Angle from the equatorial plane to the geocentric point vector, northwards usually treated as positive.",
                        'informationSource': 'Open GIS Consortium'
                        }
                    },{
                    'identifier': 'urn:ogc:def:axis:EPSG::61',
                    'axisAbbrev': 'Long',
                    'axisDirection': 'east',
                    'descriptionReference': {
                        'identifier': 'urn:ogc:def:axis-name:EPSG::9927',
                        'name': 'Spherical longitude',
                        'description': "Angle from the prime meridian plane to the meridian plane passing through a point, eastwards usually treated as positive.",
                        'informationSource': 'Open GIS Consortium'
                        }
                    },{
                    'identifier': 'urn:ogc:def:axis:EPSG::62',
                    'axisAbbrev': 'R',
                    'axisDirection': 'up',
                    'descriptionReference': {
                        'identifier': 'urn:ogc:def:axis-name:EPSG::9928',
                        'name': 'Geocentric radius',
                        'description': "The distance from the (geocentric) coordinate system origin to a point. The third axis of a spherical coordinate system.",
                        'informationSource': 'Open GIS Consortium',
                        'remarks': 'Used to avoid the singularity when the two angles in a 3D polar coordinate system lie in the same plane.'
                        }
                    }
                      ]
            }

        return self.buildCoordinateSystem(schema.SphericalCS, properties)

    def buildCoordinateSystem(self, class_, properties):
        axesProperties = properties.pop('axes')

        obj = self.buildDictionaryEntry(class_, properties)

        # add the axes
        axes = []
        for axisProperties in axesProperties:
            axes.append(self.buildCoordinateSystemAxis(axisProperties))
        obj.axes = axes

        return obj

    def buildCoordinateSystemAxis(self, properties=None):
        default_properties = {
            'identifier': 'urn:ogc:def:axis:EPSG::106',
            'axisAbbrev': 'Lat',
            'axisDirection': 'north'
            }
        if properties:
            default_properties.update(properties)

        descriptionReference = default_properties.pop('descriptionReference', None)

        obj = self.buildObject(schema.CoordinateSystemAxis, ['identifier'], default_properties)
        obj.descriptionReference = self.buildAxisName(descriptionReference)
        return obj

    def buildAxisName(self, properties=None):
        default_properties = {
            'identifier': 'urn:ogc:def:axis-name:EPSG::9901',
            'name': 'Geodetic latitude',
            'description': 'Angle from the equatorial plane to the perpendicular to the ellipsoid through a given point, northwards usually treated as positive.',
            'remarks': 'Used in geographic 2D and geographic 3D coordinate reference systems.',
            'informationSource': 'OGP'
            }
        if properties:
            default_properties.update(properties)

        return self.buildDictionaryEntry(schema.AxisName, properties)

    def buildProjectedCRS(self):
        obj = self.buildDictionaryEntry(schema.ProjectedCRS, {
                'identifier': 'urn:ogc:def:crs:EPSG::27700',
                'name': 'OSGB 1936 / British National Grid',
                'scope': 'Large and medium scale topographic mapping and engineering survey.',
                'type': 'projected',
                'informationSource': 'Ordnance Survey of Great Britain.'
                })

        obj.baseGeodeticCRS = self.buildGeodeticCRS()
        obj.cartesianCS = self.buildCartesianCS()
        obj.domainOfValidity = obj.baseGeodeticCRS.domainOfValidity
        return obj

    def buildVerticalCRS(self):
        obj = self.buildDictionaryEntry(schema.VerticalCRS, {
                'identifier': 'urn:ogc:def:crs:EPSG::3855',
                'name': 'EGM2008 geoid height',
                'remarks': 'Height surface resulting from the application of the EGM2008 geoid model to the WGS 84 ellipsoid. Replaces EGM96 geoid (CRS code 5773).',
                'scope': 'Geodesy.',
                'type': 'vertical',
                'informationSource': 'http://earth-info.nga.mil/GandG/wgs84/gravitymod/egm2008/egm08_wgs84.html'
                })
        obj.verticalDatum = self.buildVerticalDatum()
        obj.domainOfValidity = obj.verticalDatum.domainOfValidity
        obj.verticalCS = self.buildVerticalCS()

        return obj

    def buildEngineeringCRS(self):
         obj = self.buildDictionaryEntry(schema.EngineeringCRS, {
                'identifier': 'urn:ogc:def:crs:EPSG::5800',
                'name': 'Astra Minas Grid',
                'scope': 'Oil exploration.',
                'type': 'engineering'
                })
         obj.coordinateSystem = self.buildCartesianCS()
         obj.engineeringDatum = self.buildEngineeringDatum()
         obj.domainOfValidity = obj.engineeringDatum.domainOfValidity

         return obj

    def buildCompoundCRS(self):
         obj = self.buildDictionaryEntry(schema.CompoundCRS, {
                'identifier': 'urn:ogc:def:crs:EPSG::7423',
                'name': 'ETRS89 + EVRF2007 height',
                'scope': 'For pan-European products and services.',
                'type': 'compound',
                'informationSource': 'IAG subcommission for Europe',
                'remarks': 'Replaces ETRS89 + EVRF2000 height (CRS code 7409).'
                })
         obj.componentReferenceSystems = [ self.buildGeodeticCRS(), self.buildVerticalCRS() ]
         obj.domainOfValidity = obj.componentReferenceSystems[0].domainOfValidity

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
