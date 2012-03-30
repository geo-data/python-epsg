"""
Classes representing the EPSG data schema
"""

from sqlalchemy.ext.declarative import declarative_base, declared_attr, DeclarativeMeta
from sqlalchemy import Table, Column, Integer, String, Date, Float, ForeignKey, event
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
                compareAttrs() is True
                )
        dct['__eq__'] = eq

        # Add the inequality operator
        def ne(self, other):
            return not eq(self, other)
        dct['__ne__'] = ne

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

# Attribute Event Validators
#
# See <http://docs.sqlalchemy.org/en/latest/orm/events.html> for
# details.
def _validate_date(target, value, oldvalue, initiator):
    """
    Ensure a date is in the correct format

    Strings and datetime objects are converted to a date
    object. Dates strings should be in the format 'YYYY-MM-DD'.
    """

    if isinstance(value, datetime.datetime):
        return value.date()
    elif isinstance(value, (datetime.date, type(None))):
        return value
    elif isinstance(value, (str, unicode)):
        return datetime.datetime.strptime(value, '%Y-%m-%d').date()
    else:
        raise TypeError('Expected a date or datetime instance or a date string: %s' % value)

def _validate_float(target, value, oldvalue, initiator):
    """
    Ensure a value is a float
    """
    try:
        return float(value)
    except TypeError, e:
        if value is None:
            return value
        raise

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
    def _domainOfValidity_id(cls):
        return Column(String(255), ForeignKey('AreaOfUse.identifier'))

    @declared_attr
    def domainOfValidity(cls):
        return relationship(
            "AreaOfUse",
            primaryjoin = '%s._domainOfValidity_id==AreaOfUse.identifier' % cls.__name__,
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

    _discriminator = Column('class', String(50))
    __mapper_args__ = {'polymorphic_on': _discriminator}

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
    greenwichLongitude = Column(Float, nullable=False)
event.listen(PrimeMeridian.greenwichLongitude, 'set', _validate_float, propagate=True, retval=True)

class AreaOfUse(DescriptionMixin, IdentifierJoinMixin('DictionaryEntry'), DictionaryEntry):
    westBoundLongitude = Column(Float)
    eastBoundLongitude = Column(Float)
    southBoundLatitude = Column(Float)
    northBoundLatitude = Column(Float)
event.listen(AreaOfUse.westBoundLongitude, 'set', _validate_float, propagate=True, retval=True)
event.listen(AreaOfUse.eastBoundLongitude, 'set', _validate_float, propagate=True, retval=True)
event.listen(AreaOfUse.southBoundLatitude, 'set', _validate_float, propagate=True, retval=True)
event.listen(AreaOfUse.northBoundLatitude, 'set', _validate_float, propagate=True, retval=True)

class Ellipsoid(IdentifierJoinMixin('DictionaryEntry'), DictionaryEntry):
    semiMajorAxis = Column(Float, nullable=False)
    semiMinorAxis = Column(Float)
    inverseFlattening = Column(Float)
    isSphere = Column(String(50))
event.listen(Ellipsoid.semiMajorAxis, 'set', _validate_float, propagate=True, retval=True)
event.listen(Ellipsoid.semiMinorAxis, 'set', _validate_float, propagate=True, retval=True)
event.listen(Ellipsoid.inverseFlattening, 'set', _validate_float, propagate=True, retval=True)

class Datum(TypeMixin, ScopeMixin, DomainOfValidityMixin, IdentifierJoinMixin('DictionaryEntry'), DictionaryEntry):
    realizationEpoch = Column(Date)
event.listen(Datum.realizationEpoch, 'set', _validate_date, propagate=True, retval=True)

class GeodeticDatum(IdentifierJoinMixin('Datum'), Datum):
    _primeMeridian_id = Column(String(255), ForeignKey('PrimeMeridian.identifier'))
    primeMeridian = relationship(
        "PrimeMeridian",
        primaryjoin = 'GeodeticDatum._primeMeridian_id==PrimeMeridian.identifier',
        uselist=False
        )

    _ellipsoid_id = Column(String(255), ForeignKey('Ellipsoid.identifier'))
    ellipsoid = relationship(
        "Ellipsoid",
        primaryjoin = 'GeodeticDatum._ellipsoid_id==Ellipsoid.identifier',
        uselist=False
        )

class VerticalDatum(IdentifierJoinMixin('Datum'), Datum):
    pass

class EngineeringDatum(IdentifierJoinMixin('Datum'), Datum):
    pass

class CoordinateReferenceSystem(TypeMixin, ScopeMixin, DomainOfValidityMixin, IdentifierJoinMixin('DictionaryEntry'), DictionaryEntry):
    """
    A Base class for a coordinate reference system

    This should not be instantiated directly as it has no
    corresponding GML entity.
    """

class GeodeticCRS(IdentifierJoinMixin('CoordinateReferenceSystem'), CoordinateReferenceSystem):
    _ellipsoidalCS_id = Column(String(255), ForeignKey('EllipsoidalCS.identifier'))
    ellipsoidalCS = relationship(
        "EllipsoidalCS",
        primaryjoin = 'GeodeticCRS._ellipsoidalCS_id==EllipsoidalCS.identifier',
        uselist=False
        )

    _geodeticDatum_id = Column(String(255), ForeignKey('GeodeticDatum.identifier'))
    geodeticDatum = relationship(
        "GeodeticDatum",
        primaryjoin = 'GeodeticCRS._geodeticDatum_id==GeodeticDatum.identifier',
        uselist=False
        )

# Many to Many association between `CoordinateSystem` and
# `CoordinateSystemAxis`
_axes_association_table = Table('axes_association', Base.metadata,
    Column('left_id', String(255), ForeignKey('CoordinateSystem.identifier')),
    Column('right_id', String(255), ForeignKey('CoordinateSystemAxis.identifier'))
)

class CoordinateSystem(TypeMixin, IdentifierJoinMixin('DictionaryEntry'), DictionaryEntry):
    axes = relationship(
        "CoordinateSystemAxis",
        secondary=_axes_association_table,
        uselist=True
        )

class EllipsoidalCS(IdentifierJoinMixin('CoordinateSystem'), CoordinateSystem):
    pass

class CartesianCS(IdentifierJoinMixin('CoordinateSystem'), CoordinateSystem):
    pass

class VerticalCS(IdentifierJoinMixin('CoordinateSystem'), CoordinateSystem):
    pass

class SphericalCS(IdentifierJoinMixin('CoordinateSystem'), CoordinateSystem):
    pass

class CoordinateSystemAxis(IdentifierJoinMixin('Identifier'), Identifier):
    axisAbbrev = Column(String(50), nullable=False)
    axisDirection = Column(String(50), nullable=False)

    _descriptionReference_id = Column(String(255), ForeignKey('AxisName.identifier'))
    descriptionReference = relationship(
        "AxisName",
        primaryjoin = 'CoordinateSystemAxis._descriptionReference_id==AxisName.identifier',
        uselist=False
        )

class AxisName(DescriptionMixin, IdentifierJoinMixin('DictionaryEntry'), DictionaryEntry):
    pass

class ProjectedCRS(IdentifierJoinMixin('CoordinateReferenceSystem'), CoordinateReferenceSystem):
    #conversion is not yet implemented
    _baseGeodeticCRS_id = Column(String(255), ForeignKey('GeodeticCRS.identifier'))
    baseGeodeticCRS = relationship(
        "CoordinateReferenceSystem",
        primaryjoin = 'ProjectedCRS._baseGeodeticCRS_id==CoordinateReferenceSystem.identifier',
        foreign_keys = [_baseGeodeticCRS_id],
        uselist=False
        )

    _cartesianCS_id = Column(String(255), ForeignKey('CartesianCS.identifier'))
    cartesianCS = relationship(
        "CartesianCS",
        primaryjoin = 'ProjectedCRS._cartesianCS_id==CartesianCS.identifier',
        foreign_keys = [_cartesianCS_id],
        uselist=False
        )

class VerticalCRS(IdentifierJoinMixin('CoordinateReferenceSystem'), CoordinateReferenceSystem):

    _verticalDatum_id = Column(String(255), ForeignKey('VerticalDatum.identifier'))
    verticalDatum = relationship(
        "VerticalDatum",
        primaryjoin = 'VerticalCRS._verticalDatum_id==VerticalDatum.identifier',
        foreign_keys = [_verticalDatum_id],
        uselist=False
        )

    _verticalCS_id = Column(String(255), ForeignKey('VerticalCS.identifier'))
    verticalCS = relationship(
        "VerticalCS",
        primaryjoin = 'VerticalCRS._verticalCS_id==VerticalCS.identifier',
        foreign_keys = [_verticalCS_id],
        uselist=False
        )

class EngineeringCRS(IdentifierJoinMixin('CoordinateReferenceSystem'), CoordinateReferenceSystem):

    _coordinateSystem_id = Column(String(255), ForeignKey('CoordinateSystem.identifier'))
    coordinateSystem = relationship(
        "CoordinateSystem",
        primaryjoin = 'EngineeringCRS._coordinateSystem_id==CoordinateSystem.identifier',
        foreign_keys = [_coordinateSystem_id],
        uselist=False
        )

    _engineeringDatum_id = Column(String(255), ForeignKey('EngineeringDatum.identifier'))
    engineeringDatum = relationship(
        "EngineeringDatum",
        primaryjoin = 'EngineeringCRS._engineeringDatum_id==EngineeringDatum.identifier',
        foreign_keys = [_engineeringDatum_id],
        uselist=False
        )

# Many to Many association between `CompoundCRS` and
# `CoordinateReferenceSystem`
_compoundcrs_association_table = Table('compoundcrs_association', Base.metadata,
    Column('left_id', String(255), ForeignKey('CompoundCRS.identifier')),
    Column('right_id', String(255), ForeignKey('CoordinateReferenceSystem.identifier'))
)

class CompoundCRS(IdentifierJoinMixin('CoordinateReferenceSystem'), CoordinateReferenceSystem):
    componentReferenceSystems = relationship(
        "CoordinateReferenceSystem",
        secondary=_compoundcrs_association_table,
        uselist=True
        )
