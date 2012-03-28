"""
# Python EPSG

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

This represents a blank database: it needs to have the schema created
and populated. A blank registry will usually be populated from the
online EPSG registry at <http://www.epsg-registry.org>. This is done
using the following code, which replaces the database schema, connects
to the remote EPSG registry to download the latest version in GML
format and updates the local registry with that data:

    >>> registry.init()         # this can take a while!

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

The following obtains all `Ellipsoid` objects containing the case
insensitive substring `airy`:

    >>> from epsg import schema
    >>> registry.session.query(schema.Ellipsoid).filter(schema.Ellipsoid.name.ilike('%airy%')).all()

See
[querying in SQLAlchemy](http://docs.sqlalchemy.org/en/latest/orm/tutorial.html#querying)
for further details.

### Loading registry data

Registries can be initialised with specific data by using specific
`Loader` instances. `Registry.getLoader` provides a shortcut for
creating a loader from the latest data in the online registry: the
following statements are equivalent:

    # using the default `init`
    >>> registry.init()

    # using `getloader`
    >>> loader = registry.getLoader()
    >>> registry.init(loader)

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

### Copying registries

`Registry` objects implement the `MutableMapping` interface which
means they can be updated from other dictionary like objects that
contain appropriate `epsg.schema` instances. `Registry` objects
themselves provide the correct interface...

    >>> registry2 = Registry()
    >>> registry2.init(loader=False) # just the schema without any objects
    >>> registry2.update(registry) # copy the registry
    >>> assert len(registry2) == len(registry) # they are the same

...as do `Loader` objects:

    >>> registry2.update(loader)

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
"""

__version__ = '0.1.0'

import schema, load, service
from collections import MutableMapping
from sqlalchemy.exc import InvalidRequestError

class Registry(MutableMapping):
    """
    An interface to the EPSG Registry

    This represents a local database copy of the online EPSG
    registry. Objects in the GML representation of the EPSG export are
    mapped to their Python representatives and persisted in the
    database. The SQLAlchemy package is used to interact with the
    database and as such any database supported by SQLAlchemy can be
    used for a registry. The default is an in-memory sqlite database
    if no other database engine is passed in using the `engine`
    constructor argument. e.g.

    >>> from epsg import Registry
    >>> registry = Registry()   # use in-memory database
    >>> registry.init()         # populate the registry
    """

    def __init__(self, engine=None):
        from sqlalchemy.orm import sessionmaker

        if engine is None:
            from sqlalchemy import create_engine
            # create an in-memory sqlite database as default
            self.engine = create_engine('sqlite:///:memory:')
        else:
            self.engine = engine

        Session = sessionmaker(self.engine, autocommit=True)
        self.session = Session()

    def __repr__(self):
        return '<Registry(%s)>' % repr(str(self.engine.url))

    # Implement the MutableMapping/Mapping abstract methods. The
    # MutableMapping ABC provides the other methods implementing the
    # mapping interface.

    def __getitem__(self, key):
        """
        Retrieve an item by its identifier

        e.g.
        >>> registry['urn:ogc:def:crs:EPSG::27700']
        """
        if not isinstance(key, (str, unicode)):
            raise TypeError('String expected for key, found: %s' % type(key))

        value = self.session.query(schema.Identifier).filter_by(identifier=key).first()
        if isinstance(value, schema.CompoundCRS):
            # a workaround due to a failure of the above to query the
            # `CompoundCRS` object. This is due to some bug in the
            # declaration and mapping of `schema.CompoundCRS`. Once
            # this is sorted out `iteritems` and `itervalues` can be
            # overridden with more performant implementations that
            # query the session directly, rather than indirectly using
            # this fix.
            value = self.session.query(schema.CoordinateReferenceSystem).filter_by(identifier=key).first()

        if not value:
            raise KeyError(key)

        return value

    def __setitem__(self, key, value):
        if not isinstance(key, (str, unicode)):
            raise TypeError('String expected for key, found: %s' % type(key))

        if not isinstance(value, schema.Identifier):
            raise ValueError('Expected subclass of `schema.Identifier`, found: %s' % type(value))

        with self.session.begin(subtransactions=True):
            self.pop(key, None) # overwrite the existing key if any

            # refresh the value's attributes in case it has been
            # lazily loaded in another session. This doesn't work for
            # `schema.CompoundCRS` objects due to a bug (probably in
            # how it is mapped using sqlalchemy).
            session = self.session.object_session(value)
            if session and session != self.session and not isinstance(value, schema.CompoundCRS):
                session.refresh(value)

            # use `merge` instead of `add` in case the value comes
            # from another session
            self.session.merge(value, load=True)

    def __delitem__(self, key):
        value = self[key]
        self.session.delete(value)
        self.session.flush()
        self.session.expunge(value)

    def __len__(self):
        return self.session.query(schema.Identifier).count()

    def __iter__(self):
        for key in self.session.query(schema.Identifier.identifier):
            yield key[0]

    # a more performant override of the default MutableMapping
    # `__contains__` implementation
    def __contains__(self, key):
        return self.session.query(schema.Identifier).filter_by(identifier=key).count() == 1

    # a more performant override of the default MutableMapping `clear`
    # implementation
    def clear(self):
        self.session.query(schema.Identifier).delete()

    def init(self, loader=None):
        """
        Drop and recreate the repository database schema

        This replaces the current schema, removing any existing
        objects and, unless `loader=False`, re-populates the database
        from the specified registry object loader. If `loader=None`
        (the default) then a default loader is generated from the
        latest version of the online EPSG registry.
        """

        if loader is None:
            loader = self.getLoader()

        with self.session.begin(subtransactions=True):
            conn = self.session.connection()
            schema.Base.metadata.drop_all(conn)
            schema.Base.metadata.create_all(conn)

            if loader is not False:
                self.update(loader)

    def getLoader(self, gml=None):
        """
        Create a loader for EPSG objects

        By default the loader is created from GML returned by the EPSG
        web service but a custom GML string can be passed in using the
        `gml` parameter.
        """

        if gml is None:
            # connect to the epsg service and retrieve the gml
            svc = service.Service()
            svc.connect()
            gml = svc.export()
            svc.close()

        # load the gml into the EPSG object structure
        xml = load.XML.FromString(gml)
        loader = load.XMLLoader(xml)
        loader.load()

        return loader
