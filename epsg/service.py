"""
Retrieve data from from the remote EPSG web service
"""

from urlparse import urlparse
import httplib
from xml.dom.minidom import parseString

# The XML used for requesting the latest version from the EPSG repository
version_xml = """<?xml version="1.0" encoding="UTF-8"?>
<GetRecords
    xmlns="http://www.opengis.net/cat/csw/2.0.2"
    xmlns:ogc="http://www.opengis.net/ogc"
    xmlns:rim="urn:oasis:names:tc:ebxml-regrep:xsd:rim:3.0"
    xmlns:wrs="http://www.opengis.net/cat/wrs/1.0"
    startPosition="1"
    maxRecords="1"
    outputFormat="application/xml; charset=UTF-8"
    resultType="results"
    service="CSW-ebRIM"
    version="2.0.2">
  <!--
      Retrieve valid Version History records.
      Sort by the Version History Slot named 'VersionDate'; use Ascending order
      so that the last Version History record in the result list will represent
      the current version of the dataset.
  -->
  <Query typeNames="wrs:ExtrinsicObject_eo rim:Slot_versionDate">
    <ElementSetName typeNames="eo">full</ElementSetName>
    <Constraint version="1.1.0">
      <ogc:Filter>
        <ogc:And>
          <ogc:PropertyIsLike wildCard="*" escapeChar="/" singleChar="?">
            <ogc:PropertyName>$eo/@id</ogc:PropertyName>
            <ogc:Literal>*:EPSG::*</ogc:Literal>
          </ogc:PropertyIsLike>
          <ogc:PropertyIsEqualTo>
            <ogc:PropertyName>$eo/@objectType</ogc:PropertyName>
            <ogc:Literal>urn:x-ogp:def:ObjectType:EPSG:version-history</ogc:Literal>
          </ogc:PropertyIsEqualTo>
          <ogc:PropertyIsEqualTo>
            <ogc:PropertyName>$eo/@status</ogc:PropertyName>
            <ogc:Literal>urn:oasis:names:tc:ebxml-regrep:StatusType:Approved</ogc:Literal>
          </ogc:PropertyIsEqualTo>
          <ogc:PropertyIsEqualTo>
            <ogc:PropertyName>$eo/$versionDate/@name</ogc:PropertyName>
            <ogc:Literal>VersionDate</ogc:Literal>
          </ogc:PropertyIsEqualTo>
        </ogc:And>
      </ogc:Filter>
    </Constraint>
    <ogc:SortBy>
      <ogc:SortProperty>
        <ogc:PropertyName>$eo/$versionDate/ValueList/Value</ogc:PropertyName>
        <ogc:SortOrder>DESC</ogc:SortOrder>
      </ogc:SortProperty>
    </ogc:SortBy>
  </Query>
</GetRecords>
"""

# The python template string for generating XML that retrieves the
# download url from the EPSG repository
download_xml = """<?xml version="1.0" encoding="UTF-8"?>
<GetRecords
    xmlns="http://www.opengis.net/cat/csw/2.0.2"
    xmlns:ogc="http://www.opengis.net/ogc"
    xmlns:rim="urn:oasis:names:tc:ebxml-regrep:xsd:rim:3.0"
    xmlns:wrs="http://www.opengis.net/cat/wrs/1.0"
    startPosition="1"
    maxRecords="100"
    outputFormat="application/xml; charset=UTF-8"
    resultType="results"
    service="CSW-ebRIM"
    version="2.0.2">
  <!--
      Retrieve the ReleaseObject releated to the current Version History record.
      Then use the ReleaseObject identifier to obtain the actual compressed
      GML Dictionary file containing the EPSG Dataset via a getRepositoryItem
      request.
  -->
  <Query typeNames="rim:Association_a rim:RegistryObject_release rim:Slot_format">
    <ElementSetName typeNames="release">full</ElementSetName>
    <Constraint version="1.1.0">
      <ogc:Filter>
        <ogc:And>
          <!-- find the correct association -->
          <ogc:PropertyIsEqualTo>
            <ogc:PropertyName>$a/targetObject</ogc:PropertyName>
            <ogc:Literal>%s</ogc:Literal>
          </ogc:PropertyIsEqualTo>
          <ogc:PropertyIsEqualTo>
            <ogc:PropertyName>$a/associationType</ogc:PropertyName>
            <ogc:Literal>urn:x-ogp:def:AssociationType:EPSG:ReleaseFor</ogc:Literal>
          </ogc:PropertyIsEqualTo>
          <!-- limit the formats to GML -->
          <ogc:PropertyIsEqualTo>
            <ogc:PropertyName>$release/$format/@name</ogc:PropertyName>
            <ogc:Literal>Format</ogc:Literal>
          </ogc:PropertyIsEqualTo>
          <ogc:PropertyIsEqualTo>
            <ogc:PropertyName>$release/$format/ValueList/Value</ogc:PropertyName>
            <ogc:Literal>GML</ogc:Literal>
          </ogc:PropertyIsEqualTo>
          <!-- now relate it to the ReleaseObject -->
          <ogc:PropertyIsEqualTo>
            <ogc:PropertyName>$a/sourceObject</ogc:PropertyName>
            <ogc:PropertyName>$release/id</ogc:PropertyName>
          </ogc:PropertyIsEqualTo>
        </ogc:And>
      </ogc:Filter>
    </Constraint>
  </Query>
</GetRecords>
"""

class Service(object):
    """
    Represents the EPSG web service

    This class provides the facility to connect to the EPSG web
    service and export the EPSG registry data in GML format. e.g.

    >>> from epsg.service Service
    >>> service = Service()
    >>> service.connect()
    >>> gml = service.export() # GML string
    >>> service.close()
    """

    # the name of the GML file in the EPSG zip export
    gmlExportName = 'GmlDictionary.xml'

    def __init__(self, url='http://www.epsg-registry.org/indicio/query'):
        self.url = url

    def connect(self):
        """
        Initiate an HTTP connection with the online registry
        """
        self._parsedUrl = urlparse(self.url)
        self._conn = httplib.HTTPConnection(self._parsedUrl.netloc)

    def close(self):
        """
        Close the HTTP connection to the online registry
        """
        self._conn.close()

    def getLatestVersion(self):
        """
        Return the ID of the latest repository version for downloading
        """
        self._conn.request('POST', self._parsedUrl.path, version_xml, {'Content-Type': 'appliation/xml'})
        response = self._conn.getresponse()
        xmlResponse = response.read()
        dom = parseString(xmlResponse)

        element = dom.getElementsByTagName('wrs:ExtrinsicObject')[0]
        version = element.attributes['id'].value

        return version

    def getExportURL(self):
        """
        Return the URL for exporting the latest repository export
        """

        version = self.getLatestVersion()
        xmlBody = download_xml % version
        self._conn.request('POST', self._parsedUrl.path, xmlBody, {'Content-Type': 'appliation/xml'})
        response = self._conn.getresponse()
        xmlResponse = response.read()
        dom = parseString(xmlResponse)

        element = dom.getElementsByTagName('wrs:repositoryItemRef')[0]
        url = element.attributes['xlink:href'].value

        return url

    def export(self):
        """
        Export the EPSG repository data as GML
        """
        import zipfile, tempfile

        # get the url to query
        url = self.getExportURL()
        parsedUrl = urlparse(url)
        path = parsedUrl.path
        if parsedUrl.query:
            path += '?' + parsedUrl.query

        # retrieve the url resource
        self._conn.request('GET', path)
        response = self._conn.getresponse()

        # write the response to a temporary file
        with tempfile.TemporaryFile() as tmp_fh:
            tmp_fh.write(response.read())
            tmp_fh.seek(0)

            # open the temporary file as a zipfile
            with zipfile.ZipFile(tmp_fh, 'r') as zh:
                if self.gmlExportName not in zh.namelist():
                    raise ValueError('The required GML file is not present in the zip export: %s' % self.gmlExportName)

                fh = zh.open(self.gmlExportName, 'r')
                gml = fh.read()
                return gml

    def __repr__(self):
        return '<Service(%s)>' % repr(self.url)
