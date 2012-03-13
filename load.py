"""
Functionality for reading and manipulating EPSG XML data
"""

from datetime import datetime
import schema

def getText(node):
    """
    Retrieve the text content of an XML node list
    """
    txt = []
    for child in node.childNodes:
        if child.nodeType == child.TEXT_NODE:
            txt.append(child.data)
    return ''.join(txt)

class XML(object):
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

class Loader(object):
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

    def getFirstChildNodeDate(self, node, childName):
        try:
            date = getText(node.getElementsByTagName(childName)[0])
        except IndexError:
            return None

        return datetime.strptime(date, '%Y-%m-%d').date()

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
            
    def loadGeodeticDatum(self, element):
        identifier = self.getFirstChildNodeText(element, 'identifier')
        name = self.getFirstChildNodeText(element, 'name')

        instance = schema.GeodeticDatum(identifier, name)

        instance.type = self.getFirstChildNodeText(element, 'epsg:type')
        instance.scope = self.getFirstChildNodeText(element, 'scope')
        instance.realizationEpoch = self.getFirstChildNodeDate(element, 'realizationEpoch')
        instance.remarks = self.getFirstChildNodeText(element, 'remarks')
        instance.anchorDefinition = self.getFirstChildNodeText(element, 'anchorDefinition')
        instance.informationSource = self.getFirstChildNodeText(element, 'epsg:informationSource')
        instance.primeMeridian = self[self.getFirstChildAttributeValue(element, 'primeMeridian', 'xlink:href')]
        return instance

    def loadPrimeMeridian(self, element):
        identifier = self.getFirstChildNodeText(element, 'identifier')
        name = self.getFirstChildNodeText(element, 'name')

        instance = schema.PrimeMeridian(identifier, name)
        instance.remarks = self.getFirstChildNodeText(element, 'remarks')
        instance.informationSource = self.getFirstChildNodeText(element, 'epsg:informationSource')
        instance.greenwichLongitude = self.getFirstChildNodeText(element, 'greenwichLongitude')
        
        return instance

    def load(self):
        # iterate through all available keys
        for key in self.xml.keys():
            try:
                # try and retrieve a related object for the key
                self[key]
            except KeyError:
                pass
