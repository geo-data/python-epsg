"""
Classes representing the EPSG data schema
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey
from sqlalchemy.orm import relationship, backref

Base = declarative_base()

class PrimeMeridian(Base):
    __tablename__ = 'PrimeMeridian'

    identifier = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False)
    remarks = Column(String)
    informationSource = Column(String)
    greenwichLongitude = Column(Float)

    def __init__(self, identifier, name):
        self.identifier = identifier
        self.name = name

    def __repr__(self):
        return "<PrimeMeridian('%s','%s')>" % (self.identifier, self.name)

class GeodeticDatum(Base):
    __tablename__ = 'GeodeticDatum'

    identifier = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False)
    scope = Column(String(255), nullable=False)
    remarks = Column(String)
    realizationEpoch = Column(Date)
    anchorDefinition = Column(String)
    type = Column(String(255), nullable=False)
    informationSource = Column(String)
    primeMeridian_id = Column(Integer, ForeignKey('PrimeMeridian.identifier'))
    primeMeridian = relationship("PrimeMeridian", backref=backref("PrimeMeridian", uselist=False))
    
    def __init__(self, identifier, name):
        self.identifier = identifier
        self.name = name

    def __repr__(self):
        return "<GeodeticDatum('%s','%s')>" % (self.identifier, self.name)
