from datetime import datetime
from io import StringIO
from pathlib import Path

import numpy as np

import grass.script as gs

from grass.tools import Tools

basedir = Path("/hdata/fjernanalyse3/CopernicusUtviklingOgTest")


tools = Tools()
tools.v_in_ogr(
    input=basedir / "Hydrologi_TotalNedborfeltMalestasjon.geojson",
    output="TotalNedborfeltMalestasjon",
    snap=-1,
    min_area=0.0001,
    where='objektType = \'NedbørfeltMålestasjon\' AND ("feltNr" < 4000 OR  "feltNr"  >= 5000)',
    overwrite=True,
    verbose=True,
)
dj = tools.v_category(
    input="TotalNedborfeltMalestasjon", op="print", layer=[1, 2], format="json"
).json
arr = np.array([(j["id"], j["layer"], j["category"]) for j in dj])
ids_with_layer2 = np.unique(arr[arr[:, 1] == 2, 0])
mask = ~np.isin(arr[:, 0], ids_with_layer2)
arr_no_layer2 = arr[mask]
arr_with_layer2 = arr[~mask]
layer_n = int(np.max(np.unique_counts(arr_with_layer2[:, 0]).counts))
# Create empty mapping
map_dict = {
    i: {"ids": set(), "cats": set()}
    for i in range(layer_n)
}
# Fill first entry in mapping with areas without overlap
map_dict[0] = {
    "ids": set(arr_no_layer2[:, 0]),
    "cats": set(arr_no_layer2[:, 2]),
}
# Distribute categories with overlap to separate layers
cats, cat_inverse = np.unique(arr_with_layer2[:, 2], return_inverse=True)
cats = cats
order = np.argsort(cat_inverse)
cat_inverse = cat_inverse[order]
ids_sorted = arr_with_layer2[:, 0][order]
starts = np.r_[0, np.flatnonzero(np.diff(cat_inverse)) + 1]
ends = np.r_[starts[1:], len(cat_inverse)]
cat_id_sets = {
    cats[i]: set(ids_sorted[s:e]) for i, (s, e) in enumerate(zip(starts, ends))
}


id_layers = {}
import itertools
from collections import defaultdict
conflicts = defaultdict(set)
for _, group in itertools.groupby(
    arr_with_layer2[np.argsort(arr_with_layer2[:,0])],
    key=lambda x: x[0]
    ):
    cats = [r[2] for r in group]
    for c1 in cats:
        conflicts[c1].update(cats)
for c in conflicts:
    conflicts[c].discard(c)
# highest degree first usually gives a better coloring
nodes = sorted(
    conflicts,
    key=lambda c: len(conflicts[c]),
    reverse=True,
)
color_of = {}
for node in nodes:
    used_colors = {
        color_of[n]
        for n in conflicts[node]
        if n in color_of
    }
    color = 0
    while color in used_colors:
        color += 1
    color_of[node] = color
n_colors = max(color_of.values()) + 1
map_dict = {
    i: {"ids": set(), "cats": set()}
    for i in range(n_colors)
}
for cat, color in color_of.items():
    map_dict[color]["cats"].add(cat)





for cat, cat_ids in cat_id_sets.items():
    for m in map_dict.values():
        if m["ids"].isdisjoint(cat_ids):
            m["ids"].update(cat_ids)
            m["cats"].add(cat)
            break

# Create zones raster for each layer
for i in range(layer_n):
    gs.message(f"Processing layer {i} with {len(map_dict[i]['cats'])} categories.")
    tools.v_extract(
        flags="d",
        input="TotalNedborfeltMalestasjon",
        output=f"TotalNedborfeltMalestasjon_split_{i}",
        file=StringIO("\n".join(map(str, map_dict[i]["cats"]))),
        overwrite=True,
        verbose=True,
        dissolve_column="cat",
    )
    field_nrs_v = {i["feltNr"] for i in tools.v_db_select(map=f"TotalNedborfeltMalestasjon_split_{i}", columns="feltNr", format="json").json["records"]}
    gs.message(f"Extracted {len(field_nrs_v)} feltNr.")
    gs.message(tools.g_region(
        flags="p",
        vector=f"TotalNedborfeltMalestasjon_split_{i}",
        align="DTM_250m@DTM",
        format="json",
    ).text)
    tools.v_to_rast(
        #flags="d",
        input=f"TotalNedborfeltMalestasjon_split_{i}",
        output=f"TotalNedborfeltMalestasjon_split_{i}",
        overwrite=True,
        type="area",
        use="attr",
        attribute_column="feltNr",
    )
    field_nrs_r = {i['category'] for i in tools.r_category(map=f"TotalNedborfeltMalestasjon_split_{i}", format="json").json}
    missing_field_nrs = field_nrs_v - field_nrs_r
    if missing_field_nrs:
        gs.warning(f"Missing field numbers in raster map {i}: {missing_field_nrs}")

# Calculate zonal statistics over time series for each layer
processing_time = datetime.now().strftime("%Y%m%d%H%M%S")
for i in range(layer_n):
    gs.message(f"Calculating zonal statistics for layer {i}.")
    tools.g_region(
        flags="p",
        vector=f"TotalNedborfeltMalestasjon_split_{i}",
        align="DTM_250m@DTM",
        format="json",
    ).text
    tools.t_rast_univar(
        input="Sentinel_3_SLSTR_RBT_L3_1day@Sentinel_3_SLSTR_RBT_L3_1day",
        zones=f"TotalNedborfeltMalestasjon_split_{i}",
        where="semantic_label IN ('S3_SLSTR_cloud_mask', 'S3_SLSTR_fractional_snow_cover', 'S3_solar_zenith_nmin')",
        region_relation="overlaps",
        output=basedir / f"TotalNedborfeltMalestasjon_split_snow_stats_l3_{processing_time}_layer_{i}.csv",
        nprocs=1,
        separator=",",
        percentile=[10, 90],
        flags="eu" if i > 0 else "e",
    )

with (basedir / f"TotalNedborfeltMalestasjon_split_snow_stats_l3_{processing_time}_merged.csv").open("w", encoding="utf-8") as fout:
    for i in range(layer_n):
        fout.write((basedir / f"TotalNedborfeltMalestasjon_split_snow_stats_l3_{processing_time}_layer_{i}.csv").read_text(encoding="utf-8"))
