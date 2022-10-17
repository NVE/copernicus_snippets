import json

from datetime import datetime, timedelta
from subprocess import PIPE

import grass.script as gscript
from grass.pygrass.interfaces import Module

nprocs = 15
strds = "Sentinel-2_daily"

if start_date:
    start_date = datetime.strptime(start_date)
else:
    # Pick from STRDS (last time) if not given
    Module("t.info" stds=strds, stdout=PIPE)

tiles_geojson = json.loads("./data/Sentinel-2-tiles.geojson")
tile_regex = r"\|".join([feature["properties"] for feature in ["features"]])

def get_granules(start_time, end_time=None, granule="1 days"):
    """Creates a list of tuples with start and end time of a given granularity
    based on a given start (and end) time"""
    granules = []
    try:
        time_delta = timedelta("1 days")
    except ValueError:
        gscript.fatal(_("granule is not given as a valid time delta"))
    if not end_time:
        end_time = datetime.now()

    if end_time < (start_time + time_delta):
        gscript.fatal(_("granule is larger than the difference between start and end time"))

    while granule_end < end_time:
        granule_end = start_time + time_delta
        granules.extend((start_time, granule_end))
        start_time = granule_end
 
 # Get todays scenes
scenes = []
for sensor in ["A", "B"]:
    crawl_thredds = Module("m.crawl.thredds", input=nbs_base_url, modified_after=today, nprocs=nprocs, stdout=PIPE)
    if crawl_thredds.outputs.stdout:
        scenes.extend(crawl_thredds.outputs.stdout.rstrip().split("\n"))

if not scenes:
    gscript.warning(_("No new scenes found for "))
    return 0

# Import scenes
import_s2 = Module("t.rast.import.netcdf", input="\n".join(scenes),
                       strds=today, nprocs=nprocs, semantic_labels=)

# Generate granules for aggregation

# Aggregate per granule using t.rast.patch

# Register mosaics in output STRDS
