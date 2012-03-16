# Python EPSG

## Overview

This package provides an API for accessing the data in the
[EPSG registry](http://www.epsg-registry.org). The `epsg.schema`
module provides an object model that closely maps to the GML which
available as an export from the registry.

The object model builds on [SQLAlchemy](http://sqlalchemy.org) to
provide persistence and querying of the object model from within a SQL
database.

The `epsg.Registry` class provides functionality to import the online
EPSG registry to a local SQL database: you can then query the database
to return the objects you are interested in. See the `Registry` class
for more information.

## Example

The `epsg.Registry` class represents a local database copy of the
online EPSG registry. Objects in the GML representation of the EPSG
export are mapped to their Python representatives and persisted in the
database. The SQLAlchemy package is used to interact with the database
and as such any database supported by SQLAlchemy can be used for a
registry. The default is an in-memory sqlite database if no other
database engine is passed in using the `engine` constructor
argument. e.g.

    >>> from epsg import Registry
    >>> registry = Registry()   # use in-memory database

The registry can be populated from the online EPSG registry at
<http://www.epsg-registry.org>.

    >>> registry.create()       # this can take a while!

An existing database can be reset, which drops and updates it from the
registry again:

    >>> registry.reset()

Objects with specific ids can be retrieved:

    >>> registry.queryByIdentifier('urn:ogc:def:crs:EPSG::27700')

Along with whole classes of objects:

    >>> from epsg import schema
    >>> registry.queryByClass(schema.GeodeticDatum)

More complex queries can be performed by using the SQLAlchemy queries,
based on objects in the `schema` module. This is done using the
`Repository.session` property which is a `sqlalchemy.orm.Session`
instance e.g.

    >>> registry.session.query(schema.Ellipsoid).filter_by(name='Airy 1830').first()

## Requirements

- [Python](http://www.python.org): tested with Python 2.7.2
- [SQLAlchemy](http://www.sqlalchemy.org): tested with SQLAlchemy 0.7.5

## Installation

Download and unpack the source, then run the following from the root
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
