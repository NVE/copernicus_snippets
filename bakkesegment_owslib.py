#!/usr/bin/env python3

# Install owslib if necessary
# !python3 -m pip install owslib

from datetime import datetime

# Import OWSlib
from owslib.fes import (
    PropertyIsEqualTo,
    PropertyIsLike,
    PropertyIsBetween,
    PropertyIsGreaterThanOrEqualTo,
    BBox,
)
from owslib.csw import CatalogueServiceWeb

csw = CatalogueServiceWeb("https://nbs.csw.met.no/csw")

# Set parameters for temporal query
start_date = datetime(year=2022, month=9, day=29)
end_date = datetime(year=2022, month=10, day=7)

# Set parameters for dataset query
format_query = PropertyIsEqualTo("dc:format", "NetCDF-CF")
date_query = PropertyIsBetween("dc:date", start_date, end_date)
date_greater_query = PropertyIsGreaterThanOrEqualTo("dc:date", start_date)
title_query = PropertyIsLike("dc:title", "S1%IW_GRD%")

# Get records from CSW
offset = 0
nextrecords = 1
results = {}
while nextrecords > 0:
    csw.getrecords2(
        constraints=[[format_query, date_query, title_query]],
        startposition=offset,
        sortby="dc:title",
    )
    offset = csw.results["nextrecord"]
    nextrecords = csw.results["nextrecord"]
    results.update(csw.records)

# Print results
print("\n".join([f"{rec.date},{rec.format},{rec.title}" for rec in results.values()]))

# Get download URL from references
print([rec.references for idx, rec in enumerate(results.values()) if idx == 0])
