import json

from datetime import datetime, timedelta
from subprocess import PIPE

import grass.script as gscript
from grass.pygrass.interfaces import Module

nprocs = 15
strds = "Sentinel_2_daily"
strds_mosaic = "Sentinel_2_daily_mosaic"

start_date = None
semantic_labels = "./data/semantic_labels.txt"

if start_date:
    start_date = datetime.strptime(start_date)
else:
    # Pick from STRDS (last time) if not given
    strds_list = Module("t.list", stdout=subprocess.PIPE).outputs.stdout.rstrip().split("\n")
    if strds in strds_list:
        Module("t.info" stds=strds, stdout=PIPE)
    else:
        start_date = datetime.now() - timedelta(days=5)

with open("./data/Sentinel-2-tiles.geojson") as gjson:
    tiles_geojson = json.load(gjson)

tile_regex = "|".join({feature["properties"]["Name"] for feature in tiles_geojson["features"]})

def get_granules(start_time=datetime.now() - timedelta(days=5), end_time=None, granule=timedelta(days=1)):
    """Creates a list of tuples with start and end time of a given granularity
    based on a given start (and end) time"""
    granules = []
    # try:
    #     time_delta = timedelta(days=1)
    # except ValueError:
    #     gscript.fatal(_("granule is not given as a valid time delta"))
    if not end_time:
        end_time = datetime.now()

    if end_time < (start_time + time_delta):
        gscript.fatal(_("granule is larger than the difference between start and end time"))

    granule_end = start_time
    while granule_end < end_time:
        granule_end = start_time + time_delta
        granules.append(tuple((start_time, granule_end)))
        start_time = granule_end
    return granules
 
# Get todays scenes
scenes = []
for sensor in ["A", "B"]:
    crawl_thredds = Module("m.crawl.thredds", input=f"https://nbstds.met.no/thredds/catalog/NBS/S2{sensor}/2022/10/catalog.xml",
                           filter=f".*({tile_regex}).*",
                           modified_after=start_date.isoformat(),
                           nprocs=nprocs,
                           stdout_=subprocess.PIPE)
    if crawl_thredds.outputs.stdout:
        scenes.extend(crawl_thredds.outputs.stdout.rstrip().split("\n"))

if not scenes or scenes == ['']:
    gscript.warning(_("No new scenes found for "))
    return 0

# Import scenes
import_s2 = Module("t.rast.import.netcdf",
                   input="\n".join(scenes),
                   output=strds,
                   memory=2048,
                   nprocs=nprocs,
                   semantic_labels=semantic_labels,
                   verbose=True)

# Generate granules for aggregation
granules = get_granules(start_time=datetime.now() - timedelta(days=5),
                        end_time=None,
                        granule=timedelta(days=1))

for granule in granules:
    # Aggregate per granule using t.rast.patch
    Module("t.rast.patch",
       input=strds,
       output=f"Sentinel_2_mosaik_{granule[0].strftime('%Y_%m_%d')}",
       where=f"start_time >= '{granule[0].isoformat()}' and start_time <= '{granule[1].isoformat()}'",
       flags="sv",
           )

    # Register mosaics in output STRDS
    Module("t.register", input=strds_mosaic,
           maps=f"Sentinel_2_mosaik_{granule[0].strftime('%Y_%m_%d')}"
