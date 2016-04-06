#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2013 European Space Agency
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

import re
from os.path import join
import logging
import urllib2
import time
from datetime import datetime
import urlparse

from collections import namedtuple
from lxml import etree
from lxml.builder import E
from django.conf import settings
from django.utils.timezone import utc
from eoxserver.core.util.timetools import isotime, getDateTime

from ngeo_browse_server.config import models
from ngeo_browse_server.config import get_ngeo_config, safe_get
from ngeo_browse_server.control.control.config import (
    get_controller_config, get_controller_config_path, get_instance_id,
    CONTROLLER_SERVER_SECTION
)


logger = logging.getLogger(__name__)

class Report(object):
    operation = None
    def __init__(self, begin, end, filename):
        self.begin = begin
        self.end = end
        self.filename = filename


#10.0.2.2 - - [28/Apr/2014:13:00:08 +0000] "GET /c/wmts/?SERVICE=WMTS&REQUEST=GetCapabilities&VERSION=1.0.0 HTTP/1.1" 200 1576 "-" "Mo..." 1927 "-"

class BrowseAccessReport(Report):
    operation = "BROWSE_ACCESS"

    def get_records(self):
        regex = re.compile('[(\d\.)]+ - - \[(.*?)\] "GET (.*?) HTTP/1\.." (\d+) (\d+|-) ".*?" ".*?" (\d+) "(.*?)"')

        with open(self.filename) as f:

            bins = {}

            for line in f:
                match = regex.match(line)
                if not match:
                    continue

                raw_dt, request, raw_status, raw_size, raw_pt, user = match.groups()

                dt = datetime(
                    *time.strptime(raw_dt, "%d/%b/%Y:%H:%M:%S +0000")[0:6],
                    tzinfo=utc
                )

                if self.begin and dt < self.begin:
                    continue
                elif self.end and dt > self.end:
                    continue

                if int(raw_status) not in (200, 304):
                    continue

                try: 
                    size = int(raw_size)
                except ValueError:
                    size = 0

                size = max(size, 0)

                try:
                    processing_time = int(raw_pt)
                except ValueError:
                    processing_time = 0

                processing_time = max(processing_time, 0)

                layers = self.get_layers(request)
                if not layers:
                    continue

                bins.setdefault((user, layers), []).append(
                    (size, processing_time, dt)
                )


            for (user, layers), items in bins.items():
                count = str(len(items))
                sizes, processing_times, dts = zip(*items)
                agg_size = str(sum(sizes))
                agg_processing_time = str(sum(processing_times))
                max_dt = max(dts)

                yield BrowseAccessRecord(
                    max_dt, layers, user, count, agg_size, agg_processing_time
                )

    def get_additional_keys(self, record):
        return ()

    def get_data(self, record):
        for key, value in zip(record._fields[1:], record[1:]):
            yield key, value

    def get_layers(self, request):
        kvps = dict(
            (key.lower(), value)
            for key, value in urlparse.parse_qsl(request)
        )

        if request.startswith("/c/wmts"):
            if kvps:
                return kvps.get("layer")
            try:
                layer = request.split("/")[3]
                if layer == "WMTSCapabilities.xml":
                    return None
                return layer
            except IndexError:
                return None
        elif request.startswith("/c/wms"):
            return kvps.get("layers")



class BrowseReportReport(Report):
    operation = "BROWSE_REPORT"
    def get_records(self):
        with open(self.filename) as f:
            for line in f:
                items = line[:-1].split("/\\/\\")
                date = getDateTime(items[0])
                if self.end and self.end < date:
                    continue
                elif self.begin and self.begin > date:
                    continue
                yield BrowseReportRecord(date, *items[1:])

    def get_additional_keys(self, record):
        return ()

    def get_data(self, record):
        return [(key, value) for key, value in record._asdict().items() if key != "date"]


BrowseAccessRecord = namedtuple("BrowseAccessRecord", ("date", "browselayers", "userid", "numRequests", "aggregatedSize", "aggregatedProcessingTime"))
BrowseReportRecord = namedtuple("BrowseReportRecord", ("date", "responsibleOrgName", "dateTime", "browseType", "numberOfContainedBrowses", "numberOfSuccessfulBrowses", "numberOfFailedBrowses"))

def get_report_xml(begin, end, access_logfile=None, report_logfile=None, config=None):
    
    config = config or get_ngeo_config()
    component_name = config.get("control", "instance_id")

    reports = []
    if access_logfile:
        reports.append(BrowseAccessReport(begin, end, access_logfile))
    if report_logfile:
        reports.append(BrowseReportReport(begin, end, report_logfile))

    root = E("fetchReportDataResponse")
    for report in reports:
        for record in report.get_records():
            root.append(
                E("report",
                    E("header",
                        E("operation", report.operation),
                        E("component", component_name),
                        E("date", isotime(record.date)), *[
                            E("additionalKey", value, key=key)
                            for key, value in report.get_additional_keys(record)
                        ]
                    ),
                    E("data", *[
                        E("value", value, key=key)
                        for key, value in report.get_data(record)
                    ])
                )
            )
    return root


def send_report(ip_address=None, begin=None, end=None, access_logfile=None, report_logfile=None, config=None):
    config = config or get_ngeo_config()

    try:
        if not ip_address:
            ctrl_config = get_controller_config(get_controller_config_path(config))
            ip_address = safe_get(ctrl_config, CONTROLLER_SERVER_SECTION, "address")
    except IOError:
        # probably no config file present, so IP cannot be determined.
        pass

    if not ip_address:
        raise Exception("IP address could not be determined")

    tree = get_report_xml(begin, end, types, access_logfile, report_logfile)
    req = urllib2.Request(
        url="http://%s/notify" % ip_address,
        data=etree.tostring(tree, pretty_print=True),
        headers={'Content-Type': 'text/xml'}
    )
    print req.data
    try:
        urllib2.urlopen(req, timeout=10)
    except (urllib2.HTTPError, urllib2.URLError), e:
        logger.error(
            "Could not send report (%s): '%s'" % (type(e).__name__, str(e))
        )
        raise


def save_report(filename, begin=None, end=None, access_logfile=None, report_logfile=None, config=None):
    config = config or get_ngeo_config()
    tree = get_report_xml(begin, end, access_logfile, report_logfile, config)
    
    with open(filename, "w+") as f:
        f.write(etree.tostring(tree, pretty_print=True))
