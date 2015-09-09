# Python EPSG

[![Build Status](https://secure.travis-ci.org/geo-data/python-epsg.png)](http://travis-ci.org/geo-data/python-epsg)

## Overview

This package provides an API for accessing the data in the
[EPSG registry](http://www.epsg-registry.org). The `epsg.schema`
module provides an object model that closely maps to the GML available
as an export from the online registry.

> Note that this package does *not* provide any functionality for
> performing reprojections or coordinate transformations: its sole
> purpose is to act as an API to access the data available at the EPSG
> registry.

The object model builds on [SQLAlchemy](http://sqlalchemy.org) to
provide persistence and querying of the object model from within a SQL
database.

## Usage

The `epsg.Registry` class represents a local database copy of the
online EPSG registry. The default is an in-memory sqlite database if
no other database engine is passed in using the `engine` constructor
argument. e.g.

    >>> from epsg import Registry
    >>> registry = Registry()   # use in-memory database

This can take a while as data is retrieved from the online EPSG
registry at <http://www.epsg-registry.org>.

`epsg.Registry` implements the Python
[`MutableMapping`](http://docs.python.org/library/collections.html#collections.MutableMapping)
interface. Keys represent EPSG identifiers and the values are the
objects themselves:

    >>> epsg4326 = registry['urn:ogc:def:crs:EPSG::4326']
    >>> print epsg4326
    <GeodeticCRS('urn:ogc:def:crs:EPSG::4326','WGS 84')>

These objects can be introspected to provide access to the EPSG
information:

    >>> epsg4326.name
    u'WGS 84'
    >>> epsg4326.geodeticDatum.realizationEpoch
    datetime.date(1984, 1, 1)

The object model is defined in `epsg.schema` but closely mirrors the
EPSG GML format. The GML can be obtained from the online EPSG registry
as follows:

    >>> from epsg.service import Service
    >>> service = Service()
    >>> service.connect() # open an HTTP connection to the online registry
    >>> gml = service.export() # get the GML as a string

The following classes compose the object model:

    >>> set((type(v) for v in registry.itervalues()))
    set([<class 'epsg.schema.PrimeMeridian'>,
         <class 'epsg.schema.AreaOfUse'>,
         <class 'epsg.schema.Ellipsoid'>,
         <class 'epsg.schema.GeodeticDatum'>,
         <class 'epsg.schema.VerticalDatum'>,
         <class 'epsg.schema.EngineeringDatum'>,
         <class 'epsg.schema.GeodeticCRS'>,
         <class 'epsg.schema.EllipsoidalCS'>,
         <class 'epsg.schema.CartesianCS'>,
         <class 'epsg.schema.VerticalCS'>,
         <class 'epsg.schema.SphericalCS'>,
         <class 'epsg.schema.EngineeringCRS'>,
         <class 'epsg.schema.CoordinateSystemAxis'>,
         <class 'epsg.schema.AxisName'>,
         <class 'epsg.schema.ProjectedCRS'>,
         <class 'epsg.schema.VerticalCRS'>,
         <class 'epsg.schema.CompoundCRS'>])

Changes to the instances are persisted in the registry (and its
underlying database):

    >>> name = 'World Geodetic System 1984'
    >>> epsg4326.name = name
    >>> del epsg4326
    >>> assert registry['urn:ogc:def:crs:EPSG::4326'] == name

### Querying the registry

Complex registry queries can be performed by using the SQLAlchemy API,
based on objects in the `schema` module. This is done using the
`Repository.session` property which is a `sqlalchemy.orm.Session`
instance.

* Obtain all `Ellipsoid` objects containing the case insensitive substring
  `airy`:

    >>> from epsg import schema
    >>> registry.session.query(schema.Ellipsoid).filter(schema.Ellipsoid.name.ilike('%airy%')).all()

* Get a particular projected coordinate reference system:

    >>> registry.session.query(schema.ProjectedCRS).filter_by(identifier = 'urn:ogc:def:crs:EPSG::6594').first()

* Find out how many coordinate reference systems are contained within the
  longitudes of -76 and -75:

    >>> registry.session.query(schema.ProjectedCRS).join(schema.ProjectedCRS.domainOfValidity).filter(schema.AreaOfUse.eastBoundLongitude.between(-76,-75), schema.AreaOfUse.westBoundLongitude.between(-76,-75)).count()

See
[querying in SQLAlchemy](http://docs.sqlalchemy.org/en/latest/orm/tutorial.html#querying)
for further details.

### Loading registry data

Registries can be initialised with specific data by using specific
`Loader` instances. `Registry.getLoader` provides a shortcut for
creating a loader from the latest data in the online registry: the
following statements are equivalent:

    # using the default loader upon initialisation
    >>> registry2 = Registry()

    # using `getloader` with the constructor
    >>> loader = registry.getLoader()
    >>> registry2 = Registry(loader=loader)

The `init` method can be used to completely re-create and re-populate
a registry database:

    >>> registry2.init() # use the default loader
    >>> registry2.init(loader)  # specify a loader
    >>> registry2.init(loader=False) # re-create but don't populate

Loaders can be created from XML files...

    >>> from epsg.load import XML, XMLLoader
    >>> xml = XML.FromFile('./tests/test.xml')
    >>> loader = XMLLoader(xml)
    >>> loader.load() # create the objects from the XML

...or from XML strings...

    >>> xml = XML.FromString(gml)
    >>> loader = XMLLoader(xml)
    >>> loader.load()

...which is equivalent to:

    >>> loader = registry.getLoader(gml)

### Updating registries

`Registry` objects implement the `MutableMapping` interface which
means they can be updated from other dictionary like objects that
contain appropriate `epsg.schema` instances. `Registry` objects
themselves provide the correct interface...

    >>> registry2 = Registry(loader=false) # create an empty registry
    >>> registry2.update(registry) # copy the registry
    >>> assert len(registry2) == len(registry) # they are the same

...as do `Loader` objects:

    >>> registry2.update(loader)

### Copying registries

Copying registries is simply a case of initialising a registry with
another registry or loader:

    >>> registry2 = Registry(loader=registry)
    >>> registry2 = Registry(loader=loader)

### Persisting registries

For efficiency reasons an application will most likely not want to
obtain its data from the online EPSG registry every time it needs to
access the data. The solution is to use a SQLAlchemy database engine
attached to a local, persistent database. The local database acts as a
cache which can be updated as required:

    >>> from sqlalchemy import create_engine
    >>> engine = create_engine('sqlite:///./epsg-registry.sqlite')
    >>> registry = Registry(engine)
    >>> registry.init() # refresh as required

## Requirements

- [Python](http://www.python.org) == 2.{6,7}
- [SQLAlchemy](http://www.sqlalchemy.org) >= 0.7.5

## Installation

### From PyPI

    pip install python-epsg

### From source

Download the source from either <http://github.com/geo-data/python-epsg/tags> or
<http://pypi.python.org/pypi/python-epsg>, then run the following from the root
distribution directory:

    python setup.py install

It is recommended that you also run:

    python setup.py test

This exercises the comprehensive package test suite. Note that the
tests require an internet connection to access the EPSG registry web
service.

## Limitations

- This is a new and immature package: please treat it as beta quality
  software and report any bugs in the github issue tracker.

- The implementation of the GML object model in python is
  incomplete. See the `TODO.md` file for a list of GML elements that
  are currently not present within the python object model.
