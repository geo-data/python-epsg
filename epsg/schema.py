"""
Classes representing the EPSG data schema
"""

from sqlalchemy.ext.declarative import declarative_base, declared_attr, DeclarativeMeta
from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey
from sqlalchemy.orm import relationship, validates
import datetime

# see http://stackoverflow.com/questions/4460830/enhance-sqlalchemy-syntax-for-polymorphic-identity
class MetaBase(DeclarativeMeta):
    """
    A metaclass underpinning all classes in the schema object model

    This ensures each class created by this metaclass will have a
    polymorphic identity of it's own, allowing joined table
    inheritance in SQLAlchemy.

    It also adds an `__eq__()` method to all classes that checks all
    public attributes for equality.
    """

    def __new__(cls, name, bases, dct):

        # Add the equality operator
        def eq(self, other):
            def compareAttrs():
                for attr in (key for key in self.__dict__.keys() if not key.startswith('_')):
                    if getattr(self, attr) != getattr(other, attr):
                        return False
                return True

            return (
                self.__class__ == other.__class__ and
                compareAttrs()
                )
        dct['__eq__'] = eq

        # Add the polymorphic identity, based on the class name
        if '_decl_class_registry' not in dct:
            mapper_args = {'polymorphic_identity': name}
            if '__mapper_args__' in dct:
                dct['__mapper_args__'].update(mapper_args)
            else:
                dct['__mapper_args__'] = mapper_args

        return super(MetaBase, cls).__new__(cls, name, bases, dct)

# Create a SQLAlchemy declarative base class using our metaclass
Base = declarative_base(metaclass=MetaBase)

# Mixins

class TypeMixin(object):
    """
    Added to classes that require a type
    """

    @declared_attr
    def type(cls):
        return Column(String(255), nullable=False)

class ScopeMixin(object):
    """
    Added to classes that require a scope
    """

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

class DescriptionMixin(object):
    """
    Added to classes that require a description attribute
    """
    @declared_attr
    def description(cls):
        return Column(String)

def IdentifierJoinMixin(join_class):
    """
    Add an `identifier` column that relates to another class

    This is a factory function that generates a mixin. `join_class` is
    the name of the other class specified in the foreign key
    relationship.
    """

    class Mixin(object):
        @declared_attr
        def identifier(cls):
            fk = '%s.identifier' % join_class
            return Column(String(255), ForeignKey(fk), primary_key=True)

    return Mixin


# Classes

class Identifier(Base):
    """
    An abstract base class that contains an EPSG identifier

    This also sets up SQLAlchemy polymorphism for derived classes.
    """
    identifier = Column(String(255), primary_key=True)

    discriminator = Column('class', String(50))
    __mapper_args__ = {'polymorphic_on': discriminator}

    @declared_attr
    def __tablename__(cls):
        """
        Automatically generate the table name
        """
        return cls.__name__

    def __init__(self, identifier):
        self.identifier = identifier

    def __repr__(self):
        return "<%s('%s')>" % (self.__class__.__name__, self.identifier)

class DictionaryEntry(IdentifierJoinMixin('Identifier'), Identifier):
    name = Column(String(255), nullable=False)
    remarks = Column(String)
    informationSource = Column(String)
    anchorDefinition = Column(String)

    def __init__(self, identifier, name):
        super(DictionaryEntry, self).__init__(identifier)
        self.name = name

    def __repr__(self):
        return "<%s('%s','%s')>" % (self.__class__.__name__, self.identifier, self.name)

class PrimeMeridian(IdentifierJoinMixin('DictionaryEntry'), DictionaryEntry):
    greenwichLongitude = Column(Float)

class AreaOfUse(DescriptionMixin, IdentifierJoinMixin('DictionaryEntry'), DictionaryEntry):
    westBoundLongitude = Column(Float)
    eastBoundLongitude = Column(Float)
    southBoundLatitude = Column(Float)
    northBoundLatitude = Column(Float)

class Ellipsoid(IdentifierJoinMixin('DictionaryEntry'), DictionaryEntry):
    semiMajorAxis = Column(Float, nullable=False)
    semiMinorAxis = Column(Float)
    inverseFlattening = Column(Float)
    isSphere = Column(String(50))

class Datum(TypeMixin, ScopeMixin, DomainOfValidityMixin, IdentifierJoinMixin('DictionaryEntry'), DictionaryEntry):
    realizationEpoch = Column(Date)
    
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

class GeodeticDatum(IdentifierJoinMixin('Datum'), Datum):
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

class VerticalDatum(IdentifierJoinMixin('Datum'), Datum):
    pass

class CoordinateReferenceSystem(TypeMixin, ScopeMixin, DomainOfValidityMixin, IdentifierJoinMixin('DictionaryEntry'), DictionaryEntry):
    """
    A Base class for a coordinate reference system

    This should not be instantiated directly as it has not
    corresponding GML entity.
    """

class GeodeticCRS(IdentifierJoinMixin('CoordinateReferenceSystem'), CoordinateReferenceSystem):
    ellipsoidalCS_id = Column(String(255), ForeignKey('EllipsoidalCS.identifier'))
    ellipsoidalCS = relationship(
        "EllipsoidalCS",
        primaryjoin = 'GeodeticCRS.ellipsoidalCS_id==EllipsoidalCS.identifier',
        uselist=False
        )

    geodeticDatum_id = Column(String(255), ForeignKey('GeodeticDatum.identifier'))
    geodeticDatum = relationship(
        "GeodeticDatum",
        primaryjoin = 'GeodeticCRS.geodeticDatum_id==GeodeticDatum.identifier',
        uselist=False
        )

class CoordinateSystem(TypeMixin, IdentifierJoinMixin('DictionaryEntry'), DictionaryEntry):
    axis_id = Column(String(255), ForeignKey('CoordinateSystemAxis.identifier'))
    axes = relationship(
        "CoordinateSystemAxis",
        primaryjoin = 'CoordinateSystem.axis_id==CoordinateSystemAxis.identifier',
        uselist=True
        )

class EllipsoidalCS(IdentifierJoinMixin('CoordinateSystem'), CoordinateSystem):
    pass

class CartesianCS(IdentifierJoinMixin('CoordinateSystem'), CoordinateSystem):
    pass

class VerticalCS(IdentifierJoinMixin('CoordinateSystem'), CoordinateSystem):
    pass

class CoordinateSystemAxis(IdentifierJoinMixin('Identifier'), Identifier):
    axisAbbrev = Column(String(50), nullable=False)
    axisDirection = Column(String(50), nullable=False)

    descriptionReference_id = Column(String(255), ForeignKey('AxisName.identifier'))
    descriptionReference = relationship(
        "AxisName",
        primaryjoin = 'CoordinateSystemAxis.descriptionReference_id==AxisName.identifier',
        uselist=False
        )

class AxisName(DescriptionMixin, IdentifierJoinMixin('DictionaryEntry'), DictionaryEntry):
    pass

class ProjectedCRS(IdentifierJoinMixin('CoordinateReferenceSystem'), CoordinateReferenceSystem):
    #conversion is not yet implemented
    baseGeodeticCRS_id = Column(String(255), ForeignKey('GeodeticCRS.identifier'))
    baseGeodeticCRS = relationship(
        "CoordinateReferenceSystem",
        primaryjoin = 'ProjectedCRS.baseGeodeticCRS_id==CoordinateReferenceSystem.identifier',
        foreign_keys = [baseGeodeticCRS_id],
        uselist=False
        )

class VerticalCRS(IdentifierJoinMixin('CoordinateReferenceSystem'), CoordinateReferenceSystem):

    verticalDatum_id = Column(String(255), ForeignKey('VerticalDatum.identifier'))
    verticalDatum = relationship(
        "VerticalDatum",
        primaryjoin = 'VerticalCRS.verticalDatum_id==VerticalDatum.identifier',
        foreign_keys = [verticalDatum_id],
        uselist=False
        )

    verticalCS_id = Column(String(255), ForeignKey('VerticalCS.identifier'))
    verticalCS = relationship(
        "VerticalCS",
        primaryjoin = 'VerticalCRS.verticalCS_id==VerticalCS.identifier',
        foreign_keys = [verticalCS_id],
        uselist=False
        )
