"""
Classes representing the EPSG data schema
"""

from sqlalchemy.ext.declarative import declarative_base, declared_attr, DeclarativeMeta
from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey
from sqlalchemy.orm import relationship, validates
import datetime

# see http://stackoverflow.com/questions/4460830/enhance-sqlalchemy-syntax-for-polymorphic-identity
class MetaPolymorphicBase(DeclarativeMeta):
    """
    A metaclass for assigning a polymorphic identity to its classes

    This ensures each class created by this metaclass will have a
    polymorphic identity of it's own, allowing joined table
    inheritance in SQLAlchemy.
    """

    def __init__(cls, *args, **kw):
        if getattr(cls, '_decl_class_registry', None) is None:
            return # they use this in the docs, so maybe its not a bad idea
        cls.__mapper_args__ = {'polymorphic_identity': cls.__name__}
        return super(MetaPolymorphicBase, cls).__init__(*args, **kw)

# Create a SQLAlchemy declarative base class using our metaclass
Base = declarative_base(metaclass=MetaPolymorphicBase)

# Mixins

class TypeMixin(object):
    """
    Added to classes that require a type and a scope
    """

    @declared_attr
    def type(cls):
        return Column(String(255), nullable=False)

    @declared_attr
    def scope(cls):
        return Column(String(255), nullable=False)

class DomainOfValidityMixin(object):
    """
    Added to classes that require domainOfValidity
    """
    @declared_attr
    def domainOfValidity_id(cls):
        return Column(String(255), ForeignKey('AreaOfUse.identifier'))

    @declared_attr
    def domainOfValidity(cls):
        return relationship(
            "AreaOfUse",
            primaryjoin = '%s.domainOfValidity_id==AreaOfUse.identifier' % cls.__name__,
            uselist=False
            )

# Classes

class DictionaryEntry(Base):

    identifier = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False)
    remarks = Column(String)
    informationSource = Column(String)
    anchorDefinition = Column(String)

    discriminator = Column('class', String(50))
    __mapper_args__ = {'polymorphic_on': discriminator}

    @declared_attr
    def __tablename__(cls):
        """
        Automatically generate the table name
        """
        return cls.__name__

    def __init__(self, identifier, name):
        self.identifier = identifier
        self.name = name

    def __repr__(self):
        return "<%s('%s','%s')>" % (self.__class__.__name__, self.identifier, self.name)

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            self.identifier == other.identifier and
            self.name == other.name and
            self.remarks == other.remarks and
            self.informationSource == other.informationSource and
            self.anchorDefinition == other.anchorDefinition
            )

class PrimeMeridian(DictionaryEntry):

    identifier = Column(String(255), ForeignKey('DictionaryEntry.identifier'), primary_key=True)
    greenwichLongitude = Column(Float)

    def __eq__(self, other):
        return (
            super(PrimeMeridian, self).__eq__(other) and
            self.greenwichLongitude == other.greenwichLongitude
            )

class AreaOfUse(DictionaryEntry):

    identifier = Column(String(255), ForeignKey('DictionaryEntry.identifier'), primary_key=True)
    description = Column(String)
    westBoundLongitude = Column(Float)
    eastBoundLongitude = Column(Float)
    southBoundLatitude = Column(Float)
    northBoundLatitude = Column(Float)

    def __eq__(self, other):
        return (
            super(AreaOfUse, self).__eq__(other) and
            self.description == other.description and
            self.westBoundLongitude == other.westBoundLongitude and
            self.eastBoundLongitude == other.eastBoundLongitude and
            self.southBoundLatitude == other.southBoundLatitude and
            self.northBoundLatitude == other.northBoundLatitude
            )

class Ellipsoid(DictionaryEntry):

    identifier = Column(String(255), ForeignKey('DictionaryEntry.identifier'), primary_key=True)
    semiMajorAxis = Column(Float)
    semiMinorAxis = Column(Float)
    inverseFlattening = Column(Float)
    isSphere = Column(String(50))

    def __eq__(self, other):
        return (
            super(Ellipsoid, self).__eq__(other) and
            self.semiMajorAxis == other.semiMajorAxis and
            self.semiMinorAxis == other.semiMinorAxis and
            self.inverseFlattening == other.inverseFlattening and
            self.isSphere == other.isSphere
            )

class GeodeticDatum(TypeMixin, DomainOfValidityMixin, DictionaryEntry):

    identifier = Column(String(255), ForeignKey('DictionaryEntry.identifier'), primary_key=True)
    realizationEpoch = Column(Date)

    primeMeridian_id = Column(String(255), ForeignKey('PrimeMeridian.identifier'))
    primeMeridian = relationship(
        "PrimeMeridian",
        primaryjoin = 'GeodeticDatum.primeMeridian_id==PrimeMeridian.identifier',
        uselist=False
        )

    ellipsoid_id = Column(String(255), ForeignKey('Ellipsoid.identifier'))
    ellipsoid = relationship(
        "Ellipsoid",
        primaryjoin = 'GeodeticDatum.ellipsoid_id==Ellipsoid.identifier',
        uselist=False
        )

    @validates('realizationEpoch')
    def validateDate(self, key, date):
        """
        Ensure a date is in the correct format

        Strings and datetime objects are converted to a date
        object. Dates strings should be in the format 'YYYY-MM-DD'.
        """

        if isinstance(date, (datetime.date, type(None))):
            return date
        if isinstance(date, (str, unicode)):
            return datetime.datetime.strptime(date, '%Y-%m-%d').date()
        elif isinstance(date, datetime.datetime):
            return date.date()
        else:
            raise TypeError('Expected a date or datetime instance or a date string: %s' % date)

    def __eq__(self, other):
        return (
            super(GeodeticDatum, self).__eq__(other) and
            self.scope == other.scope and
            self.realizationEpoch == other.realizationEpoch and
            self.type == other.type and
            self.informationSource == other.informationSource and
            self.primeMeridian == other.primeMeridian
            )

class CoordinateReferenceSystem(TypeMixin, DomainOfValidityMixin, DictionaryEntry):
    """
    A Base class for a coordinate reference system

    This should not be instantiated directly as it has not
    corresponding GML entity.
    """

    identifier = Column(String(255), ForeignKey('DictionaryEntry.identifier'), primary_key=True)

    geodeticDatum_id = Column(String(255), ForeignKey('GeodeticDatum.identifier'))
    geodeticDatum = relationship(
        "GeodeticDatum",
        primaryjoin = 'CoordinateReferenceSystem.geodeticDatum_id==GeodeticDatum.identifier',
        uselist=False
        )

    def __eq__(self, other):
        return (
            super(CoordinateReferenceSystem, self).__eq__(other) and
            self.geodeticDatum == other.geodeticDatum
            )

class GeodeticCRS(CoordinateReferenceSystem):

    identifier = Column(String(255), ForeignKey('CoordinateReferenceSystem.identifier'), primary_key=True)
