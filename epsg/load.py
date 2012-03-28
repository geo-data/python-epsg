"""
Functionality for reading and manipulating EPSG XML data
"""

from datetime import datetime
from collections import Mapping
import schema

def getText(node, recurse=True):
    """
    Retrieve the text content of an XML node list
    """
    txt = []
    for child in node.childNodes:
        if child.nodeType == child.TEXT_NODE:
            txt.append(child.data)
        elif child.hasChildNodes():
            txt.append(getText(child, recurse))
    return ''.join(txt).strip()

class XML(Mapping):
    """
    This is a read-only dictionary type mapping URNs to XML objects
    """

    map = None
    ns = None

    def __init__(self, dom):
        self.dom = dom
        self.map = self.createMapping()
        self.ns = self.getNamespaces()

    def getNamespaces(self):
        return dict(((k[6:], v) for k, v in self.dom.firstChild.attributes.items() if k.startswith('xmlns:')))

    def createMapping(self):
        """
        Creates a mapping between URNs and XML objects
        """
        mapping = {}
        for element in self.dom.getElementsByTagName('identifier'):
            urn = getText(element)
            mapping[urn] = element.parentNode

        return mapping

    def __getitem__(self, key):
        return self.map[key]

    def __contains__(self, key):
        return key in self.map

    def __len__(self):
        return len(self.map)

    def __iter__(self):
        return iter(self.map)

    def keys(self):
        return self.map.keys()

    @classmethod
    def FromString(cls, xml_string):
        """
        Creates an object from an XML string
        """
        from xml.dom.minidom import parseString
        dom = parseString(xml_string)
        return cls(dom)

    @classmethod
    def FromFile(cls, xml_file):
        """
        Creates an object from an XML file handle or file name
        """
        from xml.dom.minidom import parse
        dom = parse(xml_file)
        return cls(dom)

# Decorators
#
# These add various attributes to created instances by extracting the
# data from the XML. They are synonymous with the Mixins in the schema
# module.

def addType(method):
    """
    Add the type attribute
    """
    def wrapper(self, element, *args, **kwargs):
        instance = method(self, element, *args, **kwargs)
        instance.type = self.getFirstChildNodeText(element, 'epsg:type')
        return instance
    return wrapper

def addScope(method):
    """
    Add the scope attribute
    """
    def wrapper(self, element, *args, **kwargs):
        instance = method(self, element, *args, **kwargs)
        instance.scope = self.getFirstChildNodeText(element, 'scope')
        return instance
    return wrapper

def addDomainOfValidity(method):
    """
    Add the domainOfValidity attribute
    """
    def wrapper(self, element, *args, **kwargs):
        instance = method(self, element, *args, **kwargs)
        instance.domainOfValidity = self[self.getFirstChildAttributeValue(element, 'domainOfValidity', 'xlink:href')]
        return instance
    return wrapper

class XMLLoader(Mapping):
    """
    Create EPSG schema objects from XML
    """
    xml = None
    objects = None

    def __init__(self, xml):
        self.xml = xml
        self.objects = {}

    def __getitem__(self, key):
        try:
            return self.objects[key]
        except KeyError:
            pass

        element = self.xml[key]
        obj = self.loadElement(element)
        if obj is None:
            raise KeyError('The element cannot be loaded: %s' % key)

        self.objects[key] = obj
        return obj

    def __len__(self):
        return len(self.objects)

    def __iter__(self):
        return iter(self.objects)

    def keys(self):
        return self.objects.keys()

    def values(self):
        return self.objects.values()

    def items(self):
        return self.objects.items()

    def getFirstChildNodeText(self, node, childName):
        try:
            return getText(node.getElementsByTagName(childName)[0])
        except IndexError:
            return None

    def getFirstChildAttributeValue(self, node, childName, attributeName):
        try:
            return node.getElementsByTagName(childName)[0].attributes[attributeName].value
        except (KeyError, IndexError):
            return None

    def loadElement(self, element):
        try:
            loader = getattr(self, 'load' + element.localName)
        except AttributeError:
            return None

        return loader(element)

    def getIdentifier(self, element):
        return self.getFirstChildNodeText(element, 'identifier')
    
    def loadDictionaryEntry(self, element, class_=schema.DictionaryEntry):
        identifier = self.getIdentifier(element)
        name = self.getFirstChildNodeText(element, 'name')

        instance = class_(identifier, name)
        instance.remarks = self.getFirstChildNodeText(element, 'remarks')
        instance.anchorDefinition = self.getFirstChildNodeText(element, 'anchorDefinition')
        instance.informationSource = self.getFirstChildNodeText(element, 'epsg:informationSource')

        return instance

    @addType
    @addScope
    @addDomainOfValidity
    def loadDatum(self, element, class_):
        instance = self.loadDictionaryEntry(element, class_)
        instance.realizationEpoch = self.getFirstChildNodeText(element, 'realizationEpoch')
        return instance
        
    def loadGeodeticDatum(self, element):
        instance = self.loadDatum(element, schema.GeodeticDatum)
        instance.primeMeridian = self[self.getFirstChildAttributeValue(element, 'primeMeridian', 'xlink:href')]
        instance.ellipsoid = self[self.getFirstChildAttributeValue(element, 'ellipsoid', 'xlink:href')]
        return instance

    def loadVerticalDatum(self, element):
        return self.loadDatum(element, schema.VerticalDatum)

    def loadEngineeringDatum(self, element):
        return self.loadDatum(element, schema.EngineeringDatum)

    def loadEllipsoid(self, element):
        instance = self.loadDictionaryEntry(element, schema.Ellipsoid)
        instance.semiMajorAxis = self.getFirstChildNodeText(element, 'semiMajorAxis')
        instance.semiMinorAxis = self.getFirstChildNodeText(element, 'semiMinorAxis')
        instance.inverseFlattening = self.getFirstChildNodeText(element, 'inverseFlattening')
        instance.isSphere = self.getFirstChildNodeText(element, 'isSphere')

        return instance

    def loadPrimeMeridian(self, element):
        instance = self.loadDictionaryEntry(element, schema.PrimeMeridian)
        instance.greenwichLongitude = self.getFirstChildNodeText(element, 'greenwichLongitude')

        return instance

    def loadAreaOfUse(self, element):
        instance = self.loadDictionaryEntry(element, schema.AreaOfUse)
        instance.description = self.getFirstChildNodeText(element, 'gmd:description')
        instance.westBoundLongitude = self.getFirstChildNodeText(element, 'gmd:westBoundLongitude')
        instance.eastBoundLongitude = self.getFirstChildNodeText(element, 'gmd:eastBoundLongitude')
        instance.southBoundLatitude = self.getFirstChildNodeText(element, 'gmd:southBoundLatitude')
        instance.northBoundLatitude = self.getFirstChildNodeText(element, 'gmd:northBoundLatitude')

        return instance

    @addType
    @addScope
    @addDomainOfValidity
    def loadCoordinateReferenceSystem(self, element, class_):
        instance = self.loadDictionaryEntry(element, class_)
        return instance

    def loadCoordinateSystemAxis(self, element):
        identifier = self.getIdentifier(element)
        instance = schema.CoordinateSystemAxis(identifier)
        instance.axisAbbrev = self.getFirstChildNodeText(element, 'axisAbbrev')
        instance.axisDirection = self.getFirstChildNodeText(element, 'axisDirection')
        instance.descriptionReference = self[self.getFirstChildAttributeValue(element, 'descriptionReference', 'xlink:href')]

        return instance

    def loadAxisName(self, element):
        instance = self.loadDictionaryEntry(element, schema.AxisName)
        instance.description = self.getFirstChildNodeText(element, 'description')
        return instance

    @addType
    def loadCoordinateSystem(self, element, class_):
        instance = self.loadDictionaryEntry(element, class_)
        axes = []
        for axisNode in element.getElementsByTagName('axis'):
            node = axisNode.getElementsByTagName('identifier')[0]
            urn = getText(node)
            axis = self[urn]
            axes.append(axis)
        instance.axes = axes
        return instance

    def loadEllipsoidalCS(self, element):
        return self.loadCoordinateSystem(element, schema.EllipsoidalCS)

    def loadCartesianCS(self, element):
        return self.loadCoordinateSystem(element, schema.CartesianCS)

    def loadVerticalCS(self, element):
        return self.loadCoordinateSystem(element, schema.VerticalCS)

    def loadSphericalCS(self, element):
        return self.loadCoordinateSystem(element, schema.SphericalCS)

    def loadGeodeticCRS(self, element):
        instance = self.loadCoordinateReferenceSystem(element, schema.GeodeticCRS)
        instance.geodeticDatum = self[self.getFirstChildAttributeValue(element, 'geodeticDatum', 'xlink:href')]
        instance.ellipsoidalCS = self[self.getFirstChildAttributeValue(element, 'ellipsoidalCS', 'xlink:href')]

        return instance

    def loadProjectedCRS(self, element):
        instance = self.loadCoordinateReferenceSystem(element, schema.ProjectedCRS)
        instance.baseGeodeticCRS = self[self.getFirstChildAttributeValue(element, 'baseGeodeticCRS', 'xlink:href')]
        instance.cartesianCS = self[self.getFirstChildAttributeValue(element, 'cartesianCS', 'xlink:href')]
        return instance

    def loadVerticalCRS(self, element):
        instance = self.loadCoordinateReferenceSystem(element, schema.VerticalCRS)
        instance.verticalDatum = self[self.getFirstChildAttributeValue(element, 'verticalDatum', 'xlink:href')]
        instance.verticalCS = self[self.getFirstChildAttributeValue(element, 'verticalCS', 'xlink:href')]
        return instance

    def loadEngineeringCRS(self, element):
        instance = self.loadCoordinateReferenceSystem(element, schema.EngineeringCRS)
        instance.coordinateSystem = self[self.getFirstChildAttributeValue(element, 'coordinateSystem', 'xlink:href')]
        instance.engineeringDatum = self[self.getFirstChildAttributeValue(element, 'engineeringDatum', 'xlink:href')]
        return instance
    
    def loadCompoundCRS(self, element):
        instance = self.loadCoordinateReferenceSystem(element, schema.CompoundCRS)
        components = []
        for componentNode in element.getElementsByTagName('componentReferenceSystem'):
            urn = componentNode.attributes['xlink:href'].value
            crs = self[urn]
            components.append(crs)
        instance.componentReferenceSystems = components
        return instance

    def load(self):
        # iterate through all available keys
        for key in self.xml.keys():
            try:
                # try and retrieve a related object for the key
                self[key]
            except KeyError:
                pass
