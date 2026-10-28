#!/usr/bin/env python3

# Run from e.g. grass /actinia_core/grassdb/ETRS_33N/vs_test
# Create mapset if needed (-c)

# ToDo:
# - 
# - Parallelize across tracks?



import os

from functools import partial
from gettext import gettext as _
from math import ceil
from pathlib import Path

import grass.script as gs
from grass.tools import Tools


# Define input variables for script run
mask_mapset: str = "Sentinel_1_track_masks"
output_dir = Path(
    "/hdata/fjernanalyse3/Sentinel1/NORCE_masks_wetsnow/"
)
dtm = "DTM_20m_Norge_Sverige@DTM"

# Create output directory if needed
output_dir.mkdir(parents=True, exist_ok=True)


TEMP_NAME = gs.tempname(12)

basename: str = "Sentinel_1"
invalid_lc_codes: tuple[int] = (40, 90, 100)  # Cropland, built-up, water
requested_track: int | None = None
landcover_map: str = "LCFM_LCM_10_V1@LandCover"
nodata_threshold: float = -30.0
k: float = 0.5
filter_size: int = 5
method: str = "median"
VV: str = "VV"
VH: str = "VH"
linc: str = "Linc"
mask: str = "Mask"
nprocs: int = 1
memory: int = 4096
overwrite: bool = True

COG_CREATEOPTS = (
    "BIGTIFF=YES,"
    "PREDICTOR=2,"
    "COMPRESS=ZSTD,"
    "LEVEL=3,"
    "OVERVIEW_COUNT=8,"
    "OVERVIEW_RESAMPLING=NEAREST,"
    "STATISTICS=YES"
)


# Initialize tools object
tools = Tools()

# Set and store region for data preparation
current_region = tools.g_region(
    flags="ap",
    raster=dtm,
    res=100,
    format="json",
).json


# Add input mapsets to the search path
tools.g_mapsets(
    operation="add",
    mapset=[mask_mapset, "DTM",],
)

def extend_region_to_resolution(region: dict, resolution: int, *, env: dict | None = None) -> dict:
    """Extend a GRASS region to a coarser resolution.
    The south and west boundaries remain unchanged.
    North and east are extended so that the resulting number
    of rows and columns is divisible by the aggregation factor
    relative to the original resolution.
    region : dict
        Region dictionary returned by g.region format=json.
    resolution : int | float
        Desired target resolution.
    env : dict | None, optional
        Environment to use. Defaults to None.
    """
    env = env or os.environ.copy()
    tools = Tools(env=env)
    if resolution % region["nsres"] != 0 or resolution % region["ewres"] != 0:
        gs.fatal(_(
            "Target resolution %i must be a multiple "
            "of source resolution (%i, %i)"
        ) % (resolution, int(region["nsres"]), int(region["ewres"]))
        )
    row_factor = int(round(resolution / region["nsres"]))
    col_factor = int(round(resolution / region["ewres"]))
    new_rows = ceil(region["rows"] / row_factor) * row_factor
    new_cols = ceil(region["cols"] / col_factor) * col_factor
    return tools.g_region(
        res = resolution,
        # keep south/west fixed
        s=region["south"],
        w=region["west"],
        # extend north/east
        n=float(region["south"]) + new_rows * region["nsres"],
        e=float(region["west"]) + new_cols * region["ewres"],
        flags="p",
        format="json",
    ).json



def parse_mapname(map_name: str, basename: str, measure_mapping: dict, *, separator: str = "_") -> tuple[str, int] | None:
    """Extract track and measure from map name."""
    map_name = map_name.replace(basename, "")
    parts = map_name.split(separator)
    measure = next((measure_mapping[p] for p in parts if p in measure_mapping), None)
    track = next((p for p in parts if p.isdigit() and len(p) <= 3), None)
    if measure and track:
        return measure, int(track)
    return None


def _reduce_noise(
    raster_map: str,
    output_map: str,
    filter_size: int = 5,
    resolution: int = 100,
    *,
    nodata_threshold: float | None = None,
    method: str = "median",
    nprocs: int = 1,
    memory: int = 2048,
    temp_name: str = TEMP_NAME,
    env: dict | None = None,
) -> None:
    """Reduce noise in a raster map by reclassifying, resampling and filtering.

    Optionally masks out values below a nodata threshold, resamples to a
    coarser resolution using ``method`` if the map is finer than
    ``resolution``, and applies a neighborhood filter of ``filter_size``.

    :param str raster_map: Name of the input raster map
    :param int filter_size: Neighborhood size for noise filtering (must be
        odd), filtering is skipped if 0
    :param int resolution: Target resolution in map units
    :param float nodata_threshold: Lowest value considered valid; lower
        values are set to null, no reclassification if None
    :param str method: Aggregation/filtering method (e.g. median, average)
    :param int nprocs: Number of parallel processes to use for tool calls
    :param int memory: Memory in MB to use for tool calls
    :param str temp_name: Prefix used to name temporary raster maps
    :param dict env: Environment to run tools in, shared with any active
        mask/region managers; ``os.environ`` is used if None
    :return: None
    """
    env = env.copy() if env else os.environ.copy()
    tools = Tools(env=env)
    raster_map_basename = next(iter(raster_map.split("@")))
    rmap_info = tools.r_info(map=raster_map, format="json", env=env).json
    aggregate_resolution = (
        rmap_info["ewres"] < resolution or rmap_info["nsres"] < resolution
    )
    input_map = raster_map
    if nodata_threshold is not None and nodata_threshold > rmap_info["min"]:
        gs.verbose(_("Applying nodata threshold to raster map {raster_map}").format(raster_map=raster_map))
        reclassed_map = f"{temp_name}_{raster_map_basename}_rc" if aggregate_resolution or filter_size > 0 else output_map
        with gs.RegionManager(align=raster_map, env=env):
            tools.r_mapcalc(
                expression=f"{reclassed_map}=if({input_map} >= {nodata_threshold}, {input_map}, null())",
                nprocs=nprocs,
                overwrite=True,
                env=env,
            )
        input_map = reclassed_map
    if aggregate_resolution:
        gs.verbose(_("Resampling raster map {raster_map} to {resolution}m resolution").format(raster_map=input_map, resolution=resolution))
        resampled_map = f"{temp_name}_{raster_map_basename}_{resolution}m" if filter_size > 0 else output_map
        tools.r_resamp_stats(
            flags="w",
            input=input_map,
            output=resampled_map,
            method=method,
            nprocs=nprocs,
            memory=memory,
            overwrite=True,
            env=env,
        )
        input_map = resampled_map
    if filter_size > 0:
        gs.verbose(_("Applying {method} neighborhood filter to raster map {raster_map} with filter size {filter_size}").format(method=method, raster_map=input_map, filter_size=filter_size))
        filtered_map = f"{temp_name}_{raster_map_basename}_{resolution}m"
        tools.r_neighbors(
            input=input_map,
            selection=input_map,
            output=filtered_map,
            method=method,
            size=filter_size,
            nprocs=nprocs,
            memory=memory,
            overwrite=True,
            env=env,
        )
        tools.r_mapcalc(
            expression=f"{output_map}=if({input_map}, {filtered_map}, null())",
            nprocs=nprocs,
            overwrite=True,
            env=env,
        )


def collect_reference_data(
    mapset: str,
    basename: str,
    *,
    VV: str = "VV",
    VH: str = "VH",
    linc: str = "Linc",
    mask: str = "Mask",
    requested_track: int | None = None,
) -> dict:
    """Collect input for reference data preparation.
    Run e.g. as: reference_maps_dict = collect_reference_data("Sentinel_1_track_masks", "Sentinel_1")
    """
    map_list = tools.g_list(
        type="raster",
        pattern=f"{basename}*",
        mapset=mapset,
        format="json",
    ).json
    # Identify relevant maps
    reference_maps = {}
    measure_mapping = {VV: "VV", VH: "VH", linc: "linc", mask: "mask"}
    for m in map_list:
        if requested_track and not (f"_{requested_track}_" in m["name"] or m["name"].endswith(f"_{requested_track}")):
            continue
        components  = parse_mapname(m["name"], basename, measure_mapping)
        if not components:
            continue
        if components[1] in reference_maps:
            reference_maps[components[1]][components[0]] = m["fullname"]
        else:
            reference_maps[components[1]] = {components[0]: m["fullname"]}
    for track, raster_maps in reference_maps.items():
        if not all(measure in raster_maps for measure in measure_mapping.values()):
            gs.warning("Incomplete reference maps for track %i. Skipping..." % track)
            del reference_maps[track]
            continue
    return reference_maps


def mask_landcover(
    landcover_map: str = "LCFM_LCM_10_V1@LandCover",
    invalid_lc_codes: tuple[int] = (40, 90, 100),  # Cropland, built-up, water
    *,
    overwrite: bool = True,
    nprocs: int = 1,
    env: dict | None = None,
) -> None:
    env = env or os.environ.copy()
    tools = Tools(env=env)
    tools.g_region(raster=landcover_map, align=landcover_map)
    mask_expression = f"landcover_mask=if(("
    mask_expression += " || ".join(f"{landcover_map} == {v}" for v in invalid_lc_codes)
    mask_expression += "), null(), 1)"
    tools.r_mapcalc(
        expression=mask_expression,
        overwrite=overwrite,
        nprocs=nprocs,
    )

# -----------------------------------------------------------------
# Preparing reference data (only once)
# -----------------------------------------------------------------
def prepare_reference_data_track(
    track: dict,
    raster_maps: dict,
    *,
    basename: str | None = None,
    output_dir: Path = Path("."),
    current_region: dict | None = None,
    temp_name: str | None = None,
    memory: int = 4096,
    nprocs: int = 1,
    overwrite: bool = True,
    env: dict | None = None,
    ) -> dict:
    """Prepare reference data for a single track.

    Args:
        track (dict): Track information.
        raster_maps (dict): Dictionary of raster maps.
        basename (str | None, optional): Base name for output maps. Defaults to None.
        output_dir (Path, optional): Output directory. Defaults to Path(".").
        current_region (dict | None, optional): Current region information. Defaults to None.
        temp_name (str | None, optional): Temporary name for intermediate maps. Defaults to None.
        memory (int, optional): Memory to use for processing. Defaults to 4096.
        nprocs (int, optional): Number of processes to use. Defaults to 1.
        overwrite (bool, optional): Whether to overwrite existing maps. Defaults to True.
        env (dict | None, optional): Environment variables. Defaults to None.

    Returns:
        dict: Dictionary containing processed reference data for the track.

    The region and active raster mask are selected through this call's copied
    GRASS environment, so different workers can use separate regions and masks
    in the same mapset. Zero and NULL cells in the selected mask are excluded.
    """
    env = env.copy() if env else os.environ.copy()
    tools = Tools(env=env)
    result_dict = {}
    temp_name = f"{temp_name}_{track}"
    gs.verbose(_("Processing track {track}").format(track=track), env=env)
    resolution = int(current_region["nsres"])
    with gs.RegionManager(
        raster=raster_maps["VV"],
        #zoom=raster_maps["VV"],
        align=raster_maps["mask"],
        env=env,
        ):
        # Region should be zoomed to track extent and aligned with resolution.
        high_res_reg = tools.g_region(
            flags="up",
            format="json",
            env=env,
        ).json
        mask_highres = f"{basename}_{track}_mask_{int(high_res_reg['nsres'])}m"
        with gs.MaskManager(mask_name="landcover_mask", env=env):
            tools.r_mapcalc(
                expression=f"{mask_highres}=if(({raster_maps['mask']} <= 100 && {raster_maps['mask']} != 32), 1, null())",
                nprocs=nprocs,
                overwrite=overwrite,
                env=env,
            )
            tools.r_semantic_label(
                map=mask_highres,
                semantic_label="mask_high_resolution",
                env=env,
            )
            result_dict[track] = {"mask_high_resolution": mask_highres}
            extend_region_to_resolution(high_res_reg, resolution, env=env)
            mask_reclass_resampled = f"{basename}_{track}_mask_{resolution}m"
            tools.r_resamp_stats(
                flags="w",
                input=mask_highres,
                output=mask_reclass_resampled,
                method="mode",
                nprocs=nprocs,
                memory=1024,
                overwrite=overwrite,
                env=env,
            )
        tools.r_semantic_label(
            map=mask_reclass_resampled,
            semantic_label="mask",
            env=env,
        )
        result_dict[track]["mask"] = mask_reclass_resampled
        with gs.MaskManager(mask_name=mask_reclass_resampled, env=env):
            for measure in {"VV", "VH", "linc"}:
                input_map = raster_maps[measure]
                output_map = f"{basename}_{track}_{measure}_{resolution}m_{method}{filter_size:02}"
                _reduce_noise(
                    input_map,
                    output_map=output_map,
                    filter_size=filter_size,
                    resolution=resolution,
                    nodata_threshold=None if measure == "linc" else nodata_threshold,
                    method=method,
                    nprocs=nprocs,
                    memory=memory,
                    temp_name=temp_name,
                    env=env,
                )
                tools.r_semantic_label(map=output_map, semantic_label=measure, env=env)
                result_dict[track][measure] = output_map
            if k:
                gs.verbose(
                    _("Creating local incidence angle weight for raster map {linc_map} with factor k={k}").format(
                        linc_map=result_dict[track]["linc"], k=k
                    ),
                    env=env,
                )
                linc_map = result_dict[track]["linc"]
                linc_weight = (
                    f"{basename}_{track}_linc_{resolution}m_{method}{filter_size:02}"
                    f"_weighted_{str(k).replace('.', '_')}"
                )
                tools.r_mapcalc(
                    expression=f"{linc_weight}=if({linc_map} >= 45.0, {k}, if({linc_map} <= 20.0, 1.0, float(1 + (45.0 - {linc_map}) / float(45.0 - 20.0))*{k}))",
                    nprocs=nprocs,
                    overwrite=overwrite,
                    env=env,
                )
                tools.r_semantic_label(
                    map=linc_weight,
                    semantic_label="linc_weight",
                    env=env,
                )
                result_dict[track]["linc_weight"] = linc_weight
        if not result_dict[track]:
            return result_dict
        group_name = f"{basename}_{track}"
        if tools.g_findfile(
            file=group_name,
            element="group",
            format="json",
            env=env,
        ).json.get("fullname"):
            if not overwrite:
                gs.warning(_("Group %s exists but overwriting is not allowed. Skipping...") % group_name)
                return result_dict
            tools.g_remove(name=group_name, type="group", flags="f", quiet=True, env=env)
        tools.i_group(
            group=group_name,
            input=[result_dict[track][m] for m in sorted(result_dict[track])],
            env=env,
        )
        tools.g_remove(type="raster", pattern=f"{temp_name}*", env=env)
        for p in output_dir.glob(f"{temp_name}*"):
            p.unlink()
    return result_dict



def prepare_reference_data(mapset: str, basename: str, output_dir: Path, TEMP_NAME: str, *, requested_track: int | None = None, VV: str = "VV", VH: str = "VH", linc: str = "linc", mask: str = "mask", memory: int = 4096, nprocs:int = 1, overwrite: bool=True, env: dict | None = None):
    """
    Prepare reference data for a given mapset and basename.

    Parameters
    ----------
    mapset : str
        The name of the mapset containing the reference data.
    basename : str
        The base name of the reference data.
    output_dir : str or Path
        The directory where the output data will be stored.
    TEMP_NAME : str
        Temporary name prefix for intermediate files.
    requested_track : int or None, optional
        The specific track to prepare (default is None, meaning all tracks).
    VV : str, optional
        Name of the VV polarization map (default is "VV").
    VH : str, optional
        Name of the VH polarization map (default is "VH").
    linc : str, optional
        Name of the local incidence angle map (default is "linc").
    mask : str, optional
        Name of the mask map (default is "mask").
    memory : int, optional
        Amount of memory to use (default is 4096).
    nprocs : int, optional
        Number of processors to use (default is 1).
    overwrite : bool, optional
        Whether to overwrite existing files (default is True).
    env : dict, optional
        Environment variables for the tools (default is None).

    Returns
    -------
    dict
        A dictionary containing the prepared reference data.
    """
    env = env.copy() if env else os.environ.copy()
    tools = Tools(env=env)
    current_region = tools.g_region(
        flags="up",
        format="json",
    ).json
    tools.r_external_out(
        directory=output_dir,
        format="COG",
        extension="tif",
        options=COG_CREATEOPTS,
        )
    # Identify relevant maps (variable naming (e.g. Linc)
    # is specific to NORCE and handled in the helper function)
    reference_maps = collect_reference_data(
        mapset,
        basename,
        # VV=VV,
        # VH=VH,
        # linc=linc,
        # mask=mask,
        requested_track=requested_track,
    )
    mask_landcover(
        landcover_map="LCFM_LCM_10_V1@LandCover",
        invalid_lc_codes=(40, 90, 100),
        overwrite=True,
        nprocs=nprocs,
    )
    partial_prepare_reference_data_track = partial(
        prepare_reference_data_track,
        basename=basename,
        output_dir=output_dir,
        current_region=current_region,
        temp_name=TEMP_NAME,
        memory=memory,
        nprocs=nprocs,
        overwrite=overwrite,
        env=env,
        )
    result_dict = {}
    for track, raster_maps in reference_maps.items():
        result_dict.update({track: partial_prepare_reference_data_track(track=track, raster_maps=raster_maps)})
    return result_dict

#rd = prepare_reference_data("Sentinel_1_track_masks", "Sentinel_1", output_dir, TEMP_NAME, nprocs=1, env=os.environ.copy())
