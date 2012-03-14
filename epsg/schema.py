"""
Classes representing the EPSG data schema
"""

from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey
from sqlalchemy.orm import relationship, validates
import datetime

Base = declarative_base()

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
    __mapper_args__ = { "polymorphic_identity": 'PrimeMeridian' }

    identifier = Column(String(255), ForeignKey('DictionaryEntry.identifier'), primary_key=True)
    greenwichLongitude = Column(Float)

    def __eq__(self, other):
        return (
            super(PrimeMeridian, self).__eq__(other) and
            self.greenwichLongitude == other.greenwichLongitude
            )

class AreaOfUse(DictionaryEntry):
    __mapper_args__ = { "polymorphic_identity": 'AreaOfUse' }

    identifier = Column(String(255), ForeignKey('DictionaryEntry.identifier'), primary_key=True)
    description = Column(String)
    westBoundLongitude = Column(Float)
    eastBoundLongitude = Column(Float)
    southBoundLongitude = Column(Float)
    northBoundLongitude = Column(Float)

    def __eq__(self, other):
        return (
            super(AreaOfUse, self).__eq__(other) and
            self.description == other.description and
            self.westBoundLongitude == other.westBoundLongitude and
            self.eastBoundLongitude == other.eastBoundLongitude and
            self.southBoundLongitude == other.southBoundLongitude and
            self.northBoundLongitude == other.northBoundLongitude
            )

class Ellipsoid(DictionaryEntry):
    __mapper_args__ = { "polymorphic_identity": 'Ellipsoid' }

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

class GeodeticDatum(DictionaryEntry):
    __mapper_args__ = { "polymorphic_identity": 'GeodeticDatum' }

    identifier = Column(String(255), ForeignKey('DictionaryEntry.identifier'), primary_key=True)
    scope = Column(String(255), nullable=False)
    realizationEpoch = Column(Date)
    type = Column(String(255), nullable=False)

    primeMeridian_id = Column(String(255), ForeignKey('PrimeMeridian.identifier'))
    primeMeridian = relationship(
        "PrimeMeridian",
        primaryjoin = 'GeodeticDatum.primeMeridian_id==PrimeMeridian.identifier',
        uselist=False
        )

    domainOfValidity_id = Column(String(255), ForeignKey('AreaOfUse.identifier'))
    domainOfValidity = relationship(
        "AreaOfUse",
        primaryjoin = 'GeodeticDatum.domainOfValidity_id==AreaOfUse.identifier',
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

        if isinstance(date, datetime.date):
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
