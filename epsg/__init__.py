"""
An API to the EPSG registry

This package provides an API for accessing the data in the EPSG
registry (http://www.epsg-registry.org). An object model is provided
that maps to the GML available as an export from the registry,
available in the `epsg.schema` module.

The `epsg.Registry` class provides a functionality to import the
online EPSG registry to a local SQL database: you can then query the
database to return the objects you are interested in. See the
`Registry` class for more information.
"""

__version__ = '0.0.1'

import schema, load, service

class Registry(object):
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

    The registry can be populated from the online EPSG registry at
    <http://www.epsg-registry.org>.

    >>> registry.create()       # this can take a while!

    An existing database can be reset, which drops and updates it from
    the registry again:

    >>> registry.reset()

    Objects with specific ids can be retrieved:

    >>> registry.queryByIdentifier('urn:ogc:def:crs:EPSG::27700')

    Along with whole classes of objects:

    >>> from epsg import schema
    >>> registry.queryByClass(schema.GeodeticDatum)

    More complex queries can be performed by using the SQLAlchemy
    queries, based on objects in the `schema` module. This is done
    using the `Repository.session` property which is a
    `sqlalchemy.orm.Session` instance e.g.

    >>> registry.session.query(schema.Ellipsoid).filter_by(name='Airy 1830').first()
    """

    def __init__(self, engine=None):
        from sqlalchemy.orm import sessionmaker

        if engine is None:
            from sqlalchemy import create_engine
            # create an in-memory sqlite database as default
            self.engine = create_engine('sqlite:///:memory:')
        else:
            self.engine = engine

        Session = sessionmaker(self.engine)
        self.session = Session()

    def __repr__(self):
        return '<Registry(%s)>' % repr(str(self.engine.url))

    def drop(self, useTransaction=True):
        """
        Drop the database schema

        This happens within a transaction unless
        `useTransaction=False`.
        """

        if useTransaction:
            self.session.begin(subtransactions=True)

        conn = self.session.connection()
        schema.Base.metadata.drop_all(conn)
        
        if useTransaction:
            self.session.commit()

    def reset(self, useTransaction=True, update=True):
        """
        Drop and recreate the database schema
        """

        if useTransaction:
            self.session.begin(subtransactions=True)

        self.drop(useTransaction=False)
        self.create(useTransaction=False, update=update)
        
        if useTransaction:
            self.session.commit()
        
    def create(self, loader=None, useTransaction=True, update=True):
        """
        Create the repository database schema

        This deletes all objects in the database and, unless
        `update=False`, re-populates the database from the online EPSG
        repository, or from the data in the loader if it is specified
        using the `loader` parameter.
        """

        if useTransaction:
            self.session.begin(subtransactions=True)

        conn = self.session.connection()
        schema.Base.metadata.create_all(conn)

        if update:
            self.update(loader, useTransaction=False)
        
        if useTransaction:
            self.session.commit()

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
        loader = load.Loader(xml)
        loader.load()

        return loader

    def update(self, loader=None, useTransaction=True):
        """
        Update the local repository database from the EPSG repository
        """

        if loader is None:
            loader = self.getLoader()
        
        # save the objects to the database
        if useTransaction:
            self.session.begin(subtransactions=True)

        self.session.add_all(loader.values())
            
        if useTransaction:
            self.session.commit()

    def queryByIdentifier(self, identifier):
        """
        Retrieve an item by its identifier

        e.g.
        >>> registry.queryByIdentifier('urn:ogc:def:crs:EPSG::27700')
        """
        return self.session.query(schema.DictionaryEntry).filter_by(identifier=identifier).first()

    def queryByClass(self, class_):
        """
        Retrieve items according to their schema class

        e.g.
        >>> from epsg import schema
        >>> registry.queryByClass(schema.GeodeticDatum)
        """
        return self.session.query(class_).all()
