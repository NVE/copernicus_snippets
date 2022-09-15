#!/usr/bin/env python

# Requires GDAL Python bindings:
# !conda install gdal

# Imports from builtin libs
# import atexit
import os
from datetime import datetime, timedelta
import json
import logging
from math import ceil, floor
from pathlib import Path
from urllib import request, parse
import sys
import tempfile
from warnings import warn

# Imports from non-standards Python libraries
# gdal må være tilgjengelig for Python interpreteren
# nedenfor defineres omgivelsesvariablene for CONDA

if "GDAL_DATA" not in os.environ or "PROJ_LIB" not in os.environ:
    if "CONDA_PREFIX" in os.environ:
        if not Path(os.environ["CONDA_PREFIX"] + r"\Library\share\gdal").exists():
            raise Exception(f"Mappe med GDAL: {os.environ['CONDA_PREFIX']}/Library/share/gdal finnes ikke.")
        os.environ["GDAL_DATA"] = os.environ["CONDA_PREFIX"] + r"\Library\share\gdal"
        if not Path(os.environ["CONDA_PREFIX"] + r"\Library\share\proj").exists():
            raise Exception(f"Mappe med PROJ: {os.environ['CONDA_PREFIX']}/Library/share/proj finnes ikke.")
        os.environ["PROJ_LIB"] = os.environ["CONDA_PREFIX"] + r"\Library\share\proj"


from osgeo import ogr, osr, gdal
import numpy as np


def setup_logging():
    # console = logging.StreamHandler()
    # logging.basicConfig(
    #     level=logging.DEBUG,
    #     format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
    #     datefmt="%m-%d %H:%M%S",
    #     filename="mylogfile.log",
    #     filemode="w",
    # )
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
    console.setFormatter(formatter)
    logging.getLogger(__name__).addHandler(console)
    basic_logger = logging.getLogger("")
    return basic_logger


def align_windows(window, ref):
    """Align two regions
    Python version of:
    https://github.com/OSGeo/grass/blob/main/lib/raster/align_window.c
    Modifies the input ``window`` to align to ``ref`` region. The
    resolutions in ``window`` are set to match those in ``ref``
    and the ``window`` edges (ymax, ymin, xmax, xmin) are modified
    to align with the grid of the ``ref`` region.
    The ``window`` may be enlarged if necessary to achieve the
    alignment. The ymax is rounded ymaxward, the ymin yminward,
    the xmax xmaxward and the xmin xminward. Lon-lon constraints are
    taken into consideration to make sure that the ymax doesn't go
    above 90 degrees (for lat/lon) or that the xmax does "wrap" past
    the xmin, etc.
    :param window: dict of window to align, with keys ymax, ymin, xmax,
                   xmin, pixelSizeY, pixelSizeX, is_latlong
    :type window: dict
    :param ref: dict of window to align to, with keys ymax, ymin, xmax,
                xmin, pixelSizeY, pixelSizeX, is_latlong
    :type ref: dict
    :return: a modified version of ``window`` that is aligend to ``ref``
    :rtype: dict
    """

    window["pixelSizeY"] = ref["pixelSizeY"]
    window["pixelSizeX"] = ref["pixelSizeX"]
    window["is_latlong"] = ref["is_latlong"]

    logger.debug("before alignment:")
    logger.debug(f'ymax: {window["ymax"]:.15g}')
    logger.debug(f'ymin: {window["ymin"]:.15g}')
    logger.debug(f'xmin: {window["xmin"]:.15g}')
    logger.debug(f'xmax: {window["xmax"]:.15g}')

    window["ymax"] = (
        ref["ymax"]
        - floor((ref["ymax"] - window["ymax"]) / ref["pixelSizeY"]) * ref["pixelSizeY"]
    )
    window["ymin"] = (
        ref["ymin"]
        - ceil((ref["ymin"] - window["ymin"]) / ref["pixelSizeY"]) * ref["pixelSizeY"]
    )
    # Rast_easting_to_col() wraps easting:
    # xmax can become < xmin, or both xmin and xmax are shifted */
    window["xmin"] = (
        ref["xmin"]
        + floor((window["xmin"] - ref["xmin"]) / ref["pixelSizeX"]) * ref["pixelSizeX"]
    )
    window["xmax"] = (
        ref["xmax"]
        + ceil((window["xmax"] - ref["xmax"]) / ref["pixelSizeX"]) * ref["pixelSizeX"]
    )

    if window["is_latlong"]:
        while window["ymax"] > 90.0 + window["pixelSizeY"] / 2.0:
            window["ymax"] -= window["pixelSizeY"]
        while window["ymin"] < -90.0 - window["pixelSizeY"] / 2.0:
            window["ymin"] += window["pixelSizeY"]

    window["width"] = int((window["xmax"] - window["xmin"]) / window["pixelSizeX"])
    window["height"] = int((window["ymax"] - window["ymin"]) / window["pixelSizeY"])
    window[
        "bbox"
    ] = f"{window['xmin']}, {window['ymin']}, {window['xmax']}, {window['ymax']}"

    logger.debug("after alignment:")
    logger.debug(f'ymax: {window["ymax"]:.15g}')
    logger.debug(f'ymin: {window["ymin"]:.15g}')
    logger.debug(f'xmin: {window["xmin"]:.15g}')
    logger.debug(f'xmax: {window["xmax"]:.15g}')

    return window


def create_gdal_raster(
    reference_grid, srs, data_type, ds_name="dtm_raster", driver_name="MEM"
):
    driver = gdal.GetDriverByName(driver_name)
    target_ds = driver.Create(
        ds_name,
        int(
            (reference_grid["xmax"] - reference_grid["xmin"])
            / reference_grid["pixelSizeX"]
        ),
        int(
            (reference_grid["ymax"] - reference_grid["ymin"])
            / reference_grid["pixelSizeY"]
        ),
        1,
        data_type,
    )
    target_ds.GetRasterBand(1).Fill(0)
    target_ds.SetGeoTransform(
        (
            (reference_grid["xmin"]),
            reference_grid["pixelSizeX"],
            0,
            reference_grid["ymax"],
            0,
            -reference_grid["pixelSizeY"],
        )
    )
    target_ds.SetProjection(srs.ExportToWkt())
    return target_ds


def aggregate_raster(
    in_ds,
    reference_grid,
    spatial_ref,
    data_type=gdal.GDT_Float32,
    agg_alg=gdal.GRA_Average,
):
    """Aggregate Raster to coarser resolution"""
    target_ds = create_gdal_raster(reference_grid, spatial_ref, data_type)
    gdal.Warp(
        target_ds,
        in_ds,
        #format=gdal_format,
        # width=ref_grid['width'],
        # height=ref_grid['height'],
        resampleAlg=agg_alg,
        # dstSRS=spatial_ref,
        multithread=True,
    )

    out_array = np.array(target_ds.ReadAsArray())
    target_ds = None
    return out_array


def reproject_geojson(geo_json, spatial_ref):
    """Reproject GeoJSON to CRS of Image server"""
    # Set GeoJSON spatial reference
    s_srs = osr.SpatialReference()
    s_srs.ImportFromEPSG(4326)

    # Create temporary (shape) file
    tmp_shp = tempfile.NamedTemporaryFile().name + ".shp"

    # Reproject AOI layer
    gdal.VectorTranslate(
        tmp_shp, geo_json, dstSRS=spatial_ref, srcSRS=s_srs, reproject=True
    )

    return gdal.OpenEx(tmp_shp)


def rasterize_aoi(reference_grid, aoi, spatial_ref):
    """Rasterize AOI on reference grid"""

    # Create target raster map from reference grid
    target_ds = create_gdal_raster(
        reference_grid, spatial_ref, gdal.GDT_Byte, ds_name="mask_raster", driver_name="MEM"
    )

    # Rasterize AOI on target raster map
    gdal.Rasterize(
        target_ds, aoi, allTouched=True, layers=[aoi.GetLayerByIndex(0).GetName()]
    )
    return np.array(target_ds.ReadAsArray(), dtype=np.bool_)


def query_image_server(
    image_service="http://gis3.nve.no/image/rest/services/ImageService/S3_SLSTR_fsc_sa/ImageServer/",
    query_params=None,
    print_metadata=None,
    aoi=None,
):
    """Queries an ImageServer instance for data in space and time"""
    # ToDo: Probably more elegantly implemented as a class
    # (checking server, listing services, ...)
    # Get Service metadata
    url = image_service + "?f=pjson"
    with request.urlopen(url) as response:
        if not response.getcode() != "200":
            logger.error(response.read())
            sys.exit("Kan ikke lese fra ImageServeren.")
        response_text = response.read()
    service_description = json.loads(response_text.decode("utf-8"))
    if print_metadata and print_metadata == "service_description":
        return service_description

    # Get IDs of image(s) for selected day(s)
    params = {
        "returnGeometry": "false",
        "returnIdsOnly": "true",
        "f": "json",
    }
    if query_params:
        params.update(query_params)

    query_string = parse.urlencode(params)

    url = image_service + "query?" + query_string

    with request.urlopen(url) as response:
        response_text = response.read()
    j = json.loads(response_text.decode("utf-8"))
    if "objectIds" not in j:
        logging.error("Feil med spørring til ImageServeren.")
    images = j["objectIds"]
    if not images:
        logger.warning(
            f"Ingen bilder på ImageServeren for {selected_day.strftime('%Y-%m-%d')}."
        )

    # Get url of image(s) for selected day
    if not aoi:
        aoi = service_description["fullExtent"]
        aoi["pixelSizeX"] = service_description["pixelSizeX"]
        aoi["pixelSizeY"] = service_description["pixelSizeY"]

    width, height = (
        int((aoi["xmax"] - aoi["xmin"]) / aoi["pixelSizeX"]),
        int((aoi["ymax"] - aoi["ymin"]) / aoi["pixelSizeY"]),
    )
    bbox = ",".join(map(str, [aoi["xmin"], aoi["ymin"], aoi["xmax"], aoi["ymax"]]))
    image_params = {
        "bbox": bbox,
        "format": "tiff",
        "pixelType": service_description["pixelType"],
        "noData": "",
        "size": f"{width},{height}",
        "interpolation": "RSP_NearestNeighbor",
        "f": "json",
    }
    query_string = parse.urlencode(image_params)

    image_links = {}
    for i in images:
        url = image_service + str(i) + "/image?" + query_string
        with request.urlopen(url) as response:
            response_text = response.read()
        j = json.loads(response_text.decode("utf-8"))
        image_links[i] = j["href"]

    return image_links


def get_snow_statistics_for_height_interval(
    snow_min_elevation, snow_max_elevation, np_dtm, np_snow_ma, class_nr
):
    logger.info("Beregner verdier for klasse {}".format(class_nr))
    logger.info("Klassens minimumshøyde er {}m".format(snow_min_elevation))
    logger.info("Klassens maximumshøyde er {}m".format(snow_max_elevation))

    np_dtm_class_ma = np.ma.masked_where(
        (np_dtm < snow_min_elevation) | (np_dtm > snow_max_elevation), np_dtm, copy=True
    )

    mask = np.ma.getmask(np_dtm_class_ma)
    np_snow_ma_ma = np.ma.MaskedArray(np_snow_ma, mask)

    snow_class_mean_percentage = round(np_snow_ma_ma.mean(), 2)
    snow_class_min_percentage = np_snow_ma_ma.min()
    snow_class_max_percentage = np_snow_ma_ma.max()

    logger.info(
        "Klassens gjennomsnittlig snøprosent er {}%".format(snow_class_mean_percentage)
    )
    logger.info("Klassens minimum snøprosent er {}%".format(snow_class_min_percentage))
    logger.info("Klassens maximum snøprosent er {}%".format(snow_class_max_percentage))

    return (
        snow_class_mean_percentage,
        snow_class_min_percentage,
        snow_class_max_percentage,
    )


logger = setup_logging()

DATA_TYPES = {
    "U1": gdal.GDT_Byte,
    "U2": gdal.GDT_Byte,
    "U4": gdal.GDT_Byte,
    "U8": gdal.GDT_Byte,
    "U16": gdal.GDT_UInt16,
    "U32": gdal.GDT_UInt32,
    "S8": gdal.GDT_Byte,
    "S16": gdal.GDT_Int16,
    "S32": gdal.GDT_Int32,
    "F32": gdal.GDT_Float32,
    "F64": gdal.GDT_Float64,
    "C64": gdal.GDT_CFloat64,
    "C128": gdal.GDT_CFloat64,
    # gdal.GDT_CFloat32
    # gdal.GDT_CFloat64
    # gdal.GDT_CInt16
    # gdal.GDT_CInt32
    "UNKNOWN": gdal.GDT_Unknown,
}


def main():
    """Do the main work"""
    # User defined variables
    aoi = "C:/data/aoi.geojson"  # Path to GeoJSON with AOI could also be a WKT Polygon or shape file....
    server = (
        "http://gis3.nve.no/image/rest/services/ImageService/"  # defaults to is3.nve.no
    )
    dtm_service = "AuxDEM250"  # url to image service with DTM
    snow_service = "S3_SLSTR_fsc_sa"
    date_start = (datetime.now() - timedelta(days=3)).strftime(
        "%Y-%m-%d"
    )  # "2022-06-27"  # date in iso-format (without time)
    date_end = (datetime.now() - timedelta(days=0)).strftime(
        "%Y-%m-%d"
    )  # "2022-06-27"  # date in iso-format (without time)
    min_snow_percent = 20.0
    # Probably more userfriendly for generate relatable height intervals dynamically and
    # let user define height intervals here
    snow_bands = 250
    # Currently not used
    # ws = "in_memory"

    if not Path(aoi).exists():
        raise Exception("Finner ikke {}. Sjekk filnavn og sti.".format(aoi))

    if not date_start:
        raise Exception("Parameter 'start dato' mangler.")
    else:
        try:
            datetime.fromisoformat(date_start)
        except Exception:
            raise Exception("Parameter 'start dato' er ikke et ISO-formatert dato (YYYY-MM-DD).")

    if not date_end:
        date_end = date_start
    else:
        try:
            datetime.fromisoformat(date_end)
        except Exception:
            raise Exception("Parameter 'end dato' er ikke et ISO-formatert dato (YYYY-MM-DD).")

    # Compile URL and query paramters for snow image server
    query = {
        "where": f"""opptakstidspunkt >= date '{date_start} 00:00:00' AND opptakstidspunkt <= date '{date_end} 23:59:59'"""
    }
    logging.debug("SQL er: {query['where']}")

    image_server = "{server}/{service}/ImageServer/"

    snow_image_service = image_server.format(server=server, service=snow_service)
    snow_service_description = query_image_server(
        image_service=snow_image_service, print_metadata="service_description"
    )

    # Get spatial reference of ImageServer
    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromEPSG(
        snow_service_description["fullExtent"]["spatialReference"]["wkid"]
    )

    # Get Area of interest
    aoi_reproj = reproject_geojson(aoi, spatial_ref)
    aoi_layer = aoi_reproj.GetLayerByIndex(0)
    aoi_dict = {}
    (
        aoi_dict["xmin"],
        aoi_dict["xmax"],
        aoi_dict["ymin"],
        aoi_dict["ymax"],
        aoi_dict["is_latlong"],
    ) = (*aoi_layer.GetExtent(), bool(spatial_ref.IsGeographic()))

    # Create a reference grid to operate on (extent, resolution, rows, cols)
    ref_grid = snow_service_description["fullExtent"]
    ref_grid["is_latlong"] = bool(spatial_ref.IsGeographic())
    ref_grid["pixelSizeX"], ref_grid["pixelSizeY"] = (
        snow_service_description["pixelSizeX"],
        snow_service_description["pixelSizeY"],
    )

    # Align Area of Interest to reference grid
    raster_aoi = align_windows(aoi_dict, ref_grid)

    # Rasterize Area of interest on reference grid to be sed as mask
    raster_mask = rasterize_aoi(raster_aoi, aoi_reproj, spatial_ref)

    # Get a list of images for the requested time period from the server
    images = query_image_server(
        image_service=snow_image_service, query_params=query, aoi=raster_aoi
    )

    # Create an empty numpy array
    np_snow = np.zeros(raster_mask.shape)

    # Read images to array and compute average value over available images
    for i in images.values():
        ds = gdal.Open(f"/vsicurl/{i}")
        ds = np.array(ds.ReadAsArray())
        np_snow += np.where((ds > 100) & (ds <= 200), ds - 100, 0)
    np_snow = np_snow / len(images)

    try:
        # Ekstra test siden extract by mask ikke feiler i Desktop
        # bare pixler fra og med brukerdefinert grenseverdi skal være med
        np_snow_ma = np.ma.masked_where(np_snow < min_snow_percent, np_snow, copy=True)
        if np_snow_ma.count() == 0:
            raise Exception(
                "Fant ingen gyldige piksler. Dette er enten fordi det ikke finnes raster for valgt dato eller at angitt polygon ikke overlapper med raster."
            )

        px_area = raster_aoi["pixelSizeX"] * raster_aoi["pixelSizeY"]

        res_dict = {"snow_area": float(np_snow_ma.count() * px_area / 1000000),
                    "snow_mean_percentage": float(round(np_snow_ma.mean(), 2)),
                    "snow_min_percentage": float(round(np_snow_ma.min(), 2)),
                    "snow_max_percentage": float(round(np_snow_ma.max(), 2))}

        logger.info(
            "Gjennomsnittlig snøprosent er {}%".format(res_dict["snow_mean_percentage"])
        )
        logger.info("Minimum snøprosent er {}%".format(res_dict["snow_min_percentage"]))
        logger.info("Maximum snøprosent er {}%".format(res_dict["snow_max_percentage"]))

        # np_snow_ma_non_zero = np.ma.masked_where(np_snow > 254, np_snow, copy=True)
        res_dict["area_complete"] = float(np_snow_ma.count() * px_area / 1000000)

        logger.info(
            "Areal for piklser med minst {min_snow}% snø er {areal}km2".format(min_snow=min_snow_percent, areal=res_dict["snow_area"])
        )
        logger.info("Analyseareal er {}km2".format(res_dict["area_complete"]))

        res_dict["area_with_snow"] = float(round(
            res_dict["snow_area"] / res_dict["area_complete"] * 100, 2)
        )

        # Find elevation for pixels with snow
        res_dict["snow_mean_elevation"] = -9999
        res_dict["snow_min_elevation"] = -9999
        res_dict["snow_max_elevation"] = -9999

        # TODO: Hva skal man sette her som grense og skal det være en grense i det hele tatt?
        try:
            if (res_dict["snow_min_percentage"]) > 0:

                dtm_image_service = image_server.format(
                    server=server, service=dtm_service
                )
                dtm_service_description = query_image_server(
                    image_service=dtm_image_service,
                    print_metadata="service_description",
                )
                dtm_ref_grid = dtm_service_description["fullExtent"]
                dtm_ref_grid["is_latlong"] = bool(spatial_ref.IsGeographic())
                dtm_ref_grid["pixelSizeX"], dtm_ref_grid["pixelSizeY"] = (
                    dtm_service_description["pixelSizeX"],
                    dtm_service_description["pixelSizeY"],
                )
                dtm_aoi = align_windows(aoi_dict.copy(), dtm_ref_grid)

                dtm = query_image_server(image_service=dtm_image_service, aoi=dtm_aoi)
                np_dtm = aggregate_raster(
                    gdal.Open(f"/vsicurl/{list(dtm.values())[0]}"),
                    raster_aoi,
                    spatial_ref,
                    agg_alg=gdal.GRA_Average,
                )

                # Create snow mask
                mask = np.ma.getmask(np_snow_ma)
                # Mask DTM
                np_dtm_ma = np.ma.MaskedArray(np_dtm, mask)

                res_dict["snow_mean_elevation"] = float(round(np_dtm_ma.mean(), 2))
                res_dict["snow_min_elevation"] = float(round(np_dtm_ma.min(), 2))
                res_dict["snow_max_elevation"] = float(round(np_dtm_ma.max(), 2))

                logger.info(
                    "Gjennomsnittlig terrenghøyde med snø er {} meter".format(
                        res_dict["snow_mean_elevation"]
                    )
                )
                logger.info(
                    "Laveste terrenghøyde med snø er {} meter".format(
                        res_dict["snow_min_elevation"]
                    )
                )
                logger.info(
                    "Høyeste terrenghøyde med snø er {} meter".format(
                        res_dict["snow_max_elevation"]
                    )
                )

                snow_classes = [snow_class for snow_class in np.unique(np.floor(np_dtm_ma / snow_bands).astype(np.int8)) if snow_class]

                snow_diff_elevation = (
                    res_dict["snow_max_elevation"] - res_dict["snow_min_elevation"]
                ) / len(snow_classes)
                logger.info(
                    "snow_diff_elevation er {} meter".format(snow_diff_elevation)
                )

                for i in snow_classes:
                    snow_class_min = i * snow_bands
                    snow_class_max = snow_class_min + snow_bands
                    (
                        snow_class_mean_percentage,
                        snow_class_min_percentage,
                        snow_class_max_percentage,
                    ) = get_snow_statistics_for_height_interval(
                        snow_class_min, snow_class_max, np_dtm, np_snow_ma, i
                    )

                    # res_dict[f"snow_{snow_class_min}m_to_{snow_class_max}m"] = snow_class_min

                    try:
                        res_dict[
                            f"snow_{snow_class_min}m_to_{snow_class_max}m_mean_percentage"
                        ] = float(snow_class_mean_percentage)
                    except Exception:
                        res_dict[f"snow_{snow_class_min}m_to_{snow_class_max}m_mean_percentage"] = -9999

                    try:
                        res_dict[
                            f"snow_{snow_class_min}m_to_{snow_class_max}m_min_percentage"
                        ] = float(snow_class_min_percentage)
                    except Exception:
                        res_dict[f"snow_{snow_class_min}m_to_{snow_class_max}m_min_percentage"] = -9999

                    try:
                        res_dict[
                            f"snow_{snow_class_min}m_to_{snow_class_max}m_max_percentage"
                        ] = float(snow_class_max_percentage)
                    except Exception:
                        res_dict[f"snow_{snow_class_min}m_to_{snow_class_max}m_max_percentage"] = -9999
            else:
                logger.warning(
                    "Minimum snøprosent er {}. Beregner derfor ikke høyde".format(
                        res_dict["snow_min_percentage"]
                    )
                )
        except Exception as err:
            logger.error("Feilet ved DTM-analyse: {}".format(err))

        print(res_dict)
        print(json.dumps(res_dict))
        return json.dumps(res_dict)

    except Exception as err:
        logger.error("Feilet: {}".format(err))


if __name__ == "__main__":
    # atexit.register(cleanup)
    sys.exit(main())
