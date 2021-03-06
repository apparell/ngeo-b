#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Marko Locher <marko.locher@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2012 European Space Agency
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

import logging
from itertools import izip, tee

from eoxserver.core.util.timetools import getDateTime

from ngeo_browse_server.namespace import ns_rep, ns_rep_old, ns_bsi
from ngeo_browse_server.decoding import XMLDecoder
from ngeo_browse_server.config.browsereport import data
from ngeo_browse_server.config.browsereport.exceptions import DecodingException


logger = logging.getLogger(__name__)


def pairwise(iterable):
    "s -> (s0,s1), (s2,s3), (s4, s5), ..."
    a = iter(iterable)
    return izip(a, a)


def pairwise_iterative(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)


def decode_coord_list(coord_list, swap_axes=False):
    coords = list(pairwise(map(lambda x: x if x in ["ncol", "nrow"]
                               else float(x), coord_list.split())))
    if not swap_axes:
        return coords
    else:
        return [(x, y) for (y, x) in coords]


def decode_browse(browse_elem, ns):
    """ Parsing function to return a Browse object from an ElementTree.Element
        node.
    """

    browse_decoder = XMLDecoder({
        "browse_identifier": ("rep:browseIdentifier/text()", str, "?"),
        "file_name": "rep:fileName/text()",
        "image_type": "rep:imageType/text()",
        "reference_system_identifier": "rep:referenceSystemIdentifier/text()",
        "start_time": ("rep:startTime/text()", getDateTime),
        "end_time": ("rep:endTime/text()", getDateTime),
    }, {"rep": ns.uri})

    # general args
    kwargs = browse_decoder.decode(browse_elem)

    browse_identifier = browse_elem.find(ns("browseIdentifier"))
    if browse_identifier is not None:
        kwargs["browse_identifier"] = browse_identifier.text

    # allow spaces in reference_system_identifier e.g. "EPSG: 4326"
    # work-around for ESA's Landsat data
    kwargs['reference_system_identifier'] = kwargs['reference_system_identifier'].replace(" ", "")

    # check type of geo reference
    rectified_browse = browse_elem.find(ns("rectifiedBrowse"))
    footprint = browse_elem.find(ns("footprint"))
    regular_grid = browse_elem.find(ns("regularGrid"))
    model_in_geotiff = browse_elem.find(ns("modelInGeotiff"))
    vertical_curtain_footprint = browse_elem.find(ns("verticalCurtainFootprint"))

    rectified_decoder = XMLDecoder({
        "coord_list": "rep:coordList/text()",
    }, {"rep": ns.uri})

    footprint_decoder = XMLDecoder({
        "node_number": ("@nodeNumber", int),
        "col_row_list": "rep:colRowList/text()",
        "coord_list": "rep:coordList/text()"
    }, {"rep": ns.uri})

    regular_grid_decoder = XMLDecoder({
        "col_node_number": ("rep:colNodeNumber/text()", int),
        "row_node_number": ("rep:rowNodeNumber/text()", int),
        "col_step": ("rep:colStep/text()", float),
        "row_step": ("rep:rowStep/text()", float),
        "coord_lists": ("rep:coordList/text()", str, "+")
    }, {"rep": ns.uri})

    if rectified_browse is not None:
        logger.info("Parsing Rectified Browse.")
        kwargs.update(rectified_decoder.decode(rectified_browse))
        return data.RectifiedBrowse(**kwargs)

    elif footprint is not None:
        logger.info("Parsing Footprint Browse.")
        kwargs.update(footprint_decoder.decode(footprint))
        return data.FootprintBrowse(**kwargs)

    elif regular_grid is not None:
        logger.info("Parsing Regular Grid Browse.")
        kwargs.update(regular_grid_decoder.decode(regular_grid))
        return data.RegularGridBrowse(**kwargs)

    elif model_in_geotiff is not None:
        logger.info("Parsing GeoTIFF Browse.")
        return data.ModelInGeotiffBrowse(**kwargs)

    elif vertical_curtain_footprint is not None:
        logger.info("Parsing Vertical Curtain Browse.")
        return data.VerticalCurtainBrowse(**kwargs)

    else:
        raise DecodingException("Missing geo-spatial reference type.")


def decode_browse_report(browse_report_elem):
    """ Parsing function to return a BrowseReport object from an
        ElementTree.Element node.
    """

    logger.info("Start parsing browse report.")

    try:
        browse_report_elem = browse_report_elem.getroot()
    except AttributeError:
        pass

    expected_tags = ns_bsi("ingestBrowse"), ns_rep("browseReport"), ns_rep_old("browseReport")
    if browse_report_elem.tag not in expected_tags:
        raise DecodingException("Invalid root tag '%s'. Expected one of '%s'."
                               % (browse_report_elem.tag, expected_tags))

    if browse_report_elem.find(ns_rep_old("browseType")) is not None:
        ns = ns_rep_old
    else:
        ns = ns_rep

    browse_report_decoder = XMLDecoder({
        "date_time": ("rep:dateTime/text()", getDateTime),
        "browse_type": "rep:browseType/text()",
        "responsible_org_name": "rep:responsibleOrgName/text()",
        "browses": ("rep:browse", lambda browse: decode_browse(browse, ns), "*")
    }, {"rep": ns.uri})

    browse_report = data.BrowseReport(
        **browse_report_decoder.decode(browse_report_elem)
    )

    logger.info("Finished decoding browse report.")

    return browse_report
