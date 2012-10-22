#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Marko Locher <marko.locher@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2012 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------

from django.test import TestCase
from django.test.client import Client
from eoxserver.core.system import System

from ngeo_browse_server.config.models import Browse


class ngEOTestCaseMixIn(object):
    """ Base Mixin for ngEO test cases using the http interface. Compares the 
    expected response/status code with the actual results.
    """
    
    request = None
    url = None
    
    expected_status = 200
    expected_response = ""
    
    
    def setUp(self):
        super(ngEOTestCaseMixIn, self).setUp()
        
        client = Client()        
        self.response = client.post(self.url, self.request, "text/xml")

    
    def test_expected_status(self):
        self.assertEqual(self.expected_status, self.response.status_code)
    
    
    def test_expected_response(self):
        self.assertEqual(self.expected_response, self.response.content)


class ngEOIngestTestCaseMixIn(ngEOTestCaseMixIn):
    """ Mixin for ngEO ingest test cases. Checks whether or not the browses with
    the specified IDs have been correctly registered.  
    """
    
    fixtures = ["initial_rangetypes.json"]
    expected_ingested_browse_ids = ()
    
    
    def test_expected_ingested_browses(self):
        System.init()
        for browse_id in self.expected_ingested_browse_ids:
            self.assertTrue(Browse.objects.exists(id=browse_id))
            coverage_wrapper = System.getRegistry().getFromFactory(
                "resources.coverages.wrappers.EOCoverageFactory",
                {"obj_id": browse_id}
            )
            self.assertTrue(coverage_wrapper is not None)
     

#===============================================================================
# actual test cases
#===============================================================================

class IngestRegularGrid(ngEOIngestTestCaseMixIn, TestCase):
    url = "/ingest/"
    request = """\
<?xml version="1.0" encoding="UTF-8"?>
<rep:browseReport xmlns:rep="http://ngeo.eo.esa.int/schema/browseReport" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browseReport http://ngeo.eo.esa.int/schema/browseReport/browseReport.xsd" version="1.1">
    <rep:responsibleOrgName>EOX</rep:responsibleOrgName>
    <rep:dateTime>2012-10-02T09:30:00Z</rep:dateTime>
    <rep:browseType>BRWTYPE</rep:browseType>
    <rep:browse>
        <rep:browseIdentifier>ASAR</rep:browseIdentifier>
        <rep:fileName>ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775.tiff</rep:fileName>
        <rep:imageType>TIFF</rep:imageType>
        <rep:referenceSystemIdentifier>EPSG:4326</rep:referenceSystemIdentifier> 
        <rep:regularGrid>
            <rep:colNodeNumber>11</rep:colNodeNumber>
            <rep:rowNodeNumber>10</rep:rowNodeNumber>
            <rep:colStep>56.7</rep:colStep>
            <rep:rowStep>54</rep:rowStep>
            <rep:coordList>-33.039026 22.301754 -32.940249 21.858518 -32.839872 21.416104 -32.737996 20.974925 -32.634647 20.535039 -32.530560 20.099457 -32.423501 19.658868 -32.315686 19.222430 -32.206376 18.787042 -32.095583 18.352726</rep:coordList>
            <rep:coordList>-31.984922 17.925622 -33.397168 22.188887 -33.298089 21.743944 -33.197388 21.299842 -33.095169 20.856998 -32.991456 20.415469 -32.886988 19.978276 -32.779523 19.536078 -32.671284 19.098063 -32.561531 18.661121</rep:coordList>
            <rep:coordList>-32.450277 18.225272 -32.339140 17.796681 -33.755205 22.075213 -33.655818 21.628534 -33.554789 21.182717 -33.452221 20.738179 -33.348139 20.294979 -33.243284 19.856150 -33.135407 19.412314 -33.026740 18.972696</rep:coordList>
            <rep:coordList>-32.916538 18.534174 -32.804815 18.096769 -32.693198 17.666665 -34.113133 21.960709 -34.013433 21.512264 -33.912071 21.064702 -33.809149 20.618442 -33.704692 20.173543 -33.599445 19.733050 -33.491150 19.287550</rep:coordList>
            <rep:coordList>-33.382048 18.846303 -33.271391 18.406174 -33.159194 17.967187 -33.047090 17.535547 -34.470954 21.845378 -34.370937 21.395137 -34.269236 20.945801 -34.165954 20.497790 -34.061117 20.051163 -33.955472 19.608978</rep:coordList>
            <rep:coordList>-33.846754 19.161786 -33.737211 18.718883 -33.626093 18.277122 -33.513416 17.836527 -33.400819 17.403326 -34.828661 21.729172 -34.728321 21.277104 -34.626275 20.825964 -34.522628 20.376173 -34.417405 19.927790</rep:coordList>
            <rep:coordList>-34.311357 19.483886 -34.202209 19.034974 -34.092219 18.590387 -33.980634 18.146967 -33.867470 17.704737 -33.754375 17.269949 -35.186259 21.612104 -35.085590 21.158180 -34.983195 20.705206 -34.879177 20.253605</rep:coordList>
            <rep:coordList>-34.773562 19.803437 -34.667105 19.357784 -34.557521 18.907124 -34.447078 18.460826 -34.335020 18.015720 -34.221363 17.571829 -34.107762 17.135429 -35.543742 21.494141 -35.442739 21.038329 -35.339988 20.583490</rep:coordList>
            <rep:coordList>-35.235594 20.130049 -35.129581 19.678066 -35.022709 19.230636 -34.912683 18.778199 -34.801780 18.330163 -34.689243 17.883343 -34.575086 17.437765 -34.460973 16.999727 -35.901108 21.375264 -35.799766 20.917532</rep:coordList>
            <rep:coordList>-35.696654 20.460797 -35.591877 20.005485 -35.485461 19.551657 -35.378166 19.102421 -35.267692 18.648179 -35.156323 18.198375 -35.043300 17.749814 -34.928636 17.302521 -34.814005 16.862819 -36.259107 21.262123</rep:coordList>
            <rep:coordList>-36.157233 20.801477 -36.053622 20.342135 -35.948361 19.884418 -35.841461 19.428326 -35.733683 18.976948 -35.622707 18.520618 -35.510829 18.068811 -35.397282 17.618307 -35.282080 17.169124 -35.166903 16.727605</rep:coordList>
        </rep:regularGrid>
        <rep:startTime>2012-10-02T09:20:00Z</rep:startTime>
        <rep:endTime>2012-10-02T09:20:00Z</rep:endTime>
    </rep:browse>
</rep:browseReport>"""

    expected_response = """\
<?xml version="1.0" encoding="UTF-8"?>
<bsi:ingestBrowseResponse xsi:schemaLocation="http://ngeo.eo.esa.int/schema/browse/ingestion ../ngEOBrowseIngestionService.xsd"
xmlns:bsi="http://ngeo.eo.esa.int/schema/browse/ingestion" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <bsi:status>success</bsi:status>
    <bsi:ingestionSummary>
        <bsi:toBeReplaced>1</bsi:toBeReplaced>
        <bsi:actuallyInserted>1</bsi:actuallyInserted>
        <bsi:actuallyReplaced>0</bsi:actuallyReplaced>
    </bsi:ingestionSummary>
    <bsi:ingestionResult>
        <bsi:briefRecord>
            <bsi:identifier>ASAR</bsi:identifier>
            <bsi:status>success</bsi:status>
        </bsi:briefRecord>
    </bsi:ingestionResult>
</bsi:ingestBrowseResponse>
"""
    
    
    
