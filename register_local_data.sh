rm -rf /localhome/actiniad/actinia/userdata/user/ETRS_33N/DTM
/localhome/actiniad/.local/bin/grass -c -e /localhome/actiniad/actinia/userdata/user/ETRS_33N/DTM

# Run import / registration of all data
/localhome/actiniad/.local/bin/grass /localhome/actiniad/actinia/userdata/user/ETRS_33N/DTM \
--exec r.in.gdal --o --v -o input=/hdata/fjernanalyse3/CopernicusUtviklingOgTest/data/Norge_DTM250_int.tif \
output=DTM_250m

# Create mapset if it does not exist
rm -rf /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_2_lake_ice_cover
/localhome/actiniad/.local/bin/grass -c -e /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_2_lake_ice_cover

# Run import / registration of all data
/localhome/actiniad/.local/bin/grass /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_2_lake_ice_cover \
--exec /hdata/fjernanalyse3/CopernicusUtviklingOgTest/t.register.local --overwrite -o \
input="/hdata/fjernanalyse2/Sentinel2/Sentinel2jobs/workdir/lake_ice_cover/" \
suffix="nc" units="%" output="Sentinel_2_lake_ice_cover" \
semantic_labels="/hdata/fjernanalyse3/CopernicusUtviklingOgTest/data_import/semantic_labels_lake_ice_cover.txt" \
long_name="binary lake ice cover from Sentinel-2" nprocs=5 nodata=255 time_format="%Y%m%d"

# Create mapset if it does not exist
rm -rf /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_2_cloud_mask
/localhome/actiniad/.local/bin/grass -c -e /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_2_cloud_mask

# Run import / registration of all data
/localhome/actiniad/.local/bin/grass /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_2_cloud_mask \
--exec /hdata/fjernanalyse3/CopernicusUtviklingOgTest/t.register.local --overwrite -o \
input="/hdata/fjernanalyse2/Sentinel2/Sentinel2jobs/workdir/mask_cloud" \
suffix="nc" units="classification" output="Sentinel_2_cloud_mask" \
semantic_labels="/hdata/fjernanalyse3/CopernicusUtviklingOgTest/data_import/semantic_labels_cloud_masks.txt" \
long_name="Sentinel-2 cloud masks for dense, cirrus and all clouds" nprocs=5 nodata=255 time_format="%Y%m%d"

# Create mapset if it does not exist
rm -rf /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_2
/localhome/actiniad/.local/bin/grass -c -e /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_2

# Run import / registration of all data
/localhome/actiniad/.local/bin/grass /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_2 \
--exec /hdata/fjernanalyse3/CopernicusUtviklingOgTest/t.register.local --overwrite -o \
input="/hdata/fjernanalyse2/Sentinel2/Sentinel2jobs/workdir/s2import/" \
suffix="nc" units="reflectance" output="Sentinel_2" \
semantic_labels="/hdata/fjernanalyse3/CopernicusUtviklingOgTest/data_import/semantic_labels_S2.txt" \
long_name="Sentinel-2 images, selected bands" nprocs=25 time_format="%Y%m%d"

# Create mapset if it does not exist
rm -rf /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_2_snow_cover
/localhome/actiniad/.local/bin/grass -c -e /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_2_snow_cover

# Run import / registration of all data
/localhome/actiniad/.local/bin/grass /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_2_snow_cover \
--exec /hdata/fjernanalyse3/CopernicusUtviklingOgTest/t.register.local --overwrite -o \
input="/hdata/fjernanalyse2/Sentinel2/Sentinel2jobs/workdir/snowcover/" \
suffix="nc" units="%" output="Sentinel_2_snow_cover" \
semantic_labels="/hdata/fjernanalyse3/CopernicusUtviklingOgTest/data_import/semantic_labels_snow_cover.txt" \
long_name="Snow cover from Sentinel-2, classification and fraction" nprocs=5 time_format="%Y%m%d"


# Create mapset if it does not exist
rm -rf /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_2_swath_mask
/localhome/actiniad/.local/bin/grass -c -e /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_2_swath_mask

# Run import / registration of all data
/localhome/actiniad/.local/bin/grass /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_2_swath_mask \
--exec /hdata/fjernanalyse3/CopernicusUtviklingOgTest/t.register.local --overwrite -o \
input="/hdata/fjernanalyse2/Sentinel2/Sentinel2jobs/workdir/mask_swath" \
suffix="nc" units="classification" output="Sentinel_2_swath_mask" \
semantic_labels="/hdata/fjernanalyse3/CopernicusUtviklingOgTest/data_import/semantic_labels_swath_mask.txt" \
long_name="Sentinel-2 swath masks" nprocs=15 nodata=255 time_format="%Y%m%d"

# Create mapset if it does not exist
rm -rf /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_1_floods
/localhome/actiniad/.local/bin/grass -c -e /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_1_floods

# Run import / registration of all data
/localhome/actiniad/.local/bin/grass /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_1_floods \
--exec /hdata/fjernanalyse3/CopernicusUtviklingOgTest/t.register.local --overwrite -o \
input="/hdata/fjernanalyse3/flomtjeneste/work/detections" \
suffix="tif" units="classification" output="Sentinel_1_floods" \
semantic_labels="/hdata/fjernanalyse3/CopernicusUtviklingOgTest/data_import/semantic_labels_S1_floods.txt" \
long_name="Detected floods from Sentinel-1" nprocs=9 nodata=255 time_format="%Y%m%d_%H%M" \
file_pattern="*/[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_[0-9][0-9][0-9][0-9]_*_*_floods"


# Create mapset if it does not exist
rm -rf /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_1_flood_coverage
/localhome/actiniad/.local/bin/grass -c -e /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_1_flood_coverage

# Run import / registration of all data
/localhome/actiniad/.local/bin/grass /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_1_flood_coverage \
--exec /hdata/fjernanalyse3/CopernicusUtviklingOgTest/t.register.local --overwrite -o \
input="/hdata/fjernanalyse3/flomtjeneste/results" \
suffix="tif" units="classification" output="Sentinel_1_flood_coverage" \
semantic_labels="/hdata/fjernanalyse3/CopernicusUtviklingOgTest/data_import/semantic_labels_coverage.txt" \
long_name="flood coverage from Sentinel-1" nprocs=9 nodata=255 time_format="%Y%m%d" \
file_pattern="*/[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_[0-9][0-9][0-9][0-9]_*_*_coverage"

/localhome/actiniad/.local/bin/grass /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_1_flood_coverage \
--exec t.info Sentinel_1_flood_coverage

# Create mapset if it does not exist
rm -rf /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_1_flood_pseudocolor_hillshade
/localhome/actiniad/.local/bin/grass -c -e /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_1_flood_pseudocolor_hillshade

# Run import / registration of all data
/localhome/actiniad/.local/bin/grass /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_1_flood_pseudocolor_hillshade \
--exec /hdata/fjernanalyse3/CopernicusUtviklingOgTest/t.register.local --overwrite -o \
input="/hdata/fjernanalyse3/flomtjeneste/results" \
suffix="tif" units="classification" output="Sentinel_1_flood_pseudocolor_hillshade" \
semantic_labels="/hdata/fjernanalyse3/CopernicusUtviklingOgTest/data_import/semantic_labels_pseudocolor_hillshade.txt" \
long_name="flood coverage pseudocolor with hillshade from Sentinel-1" nprocs=9 nodata=255 time_format="%Y%m%d" \
file_pattern="*/[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_[0-9][0-9][0-9][0-9]_*_*_pseudocolor-hs"

# Create mapset if it does not exist
rm -rf /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_1_flood_pseudocolor
/localhome/actiniad/.local/bin/grass -c -e /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_1_flood_pseudocolor

# Run import / registration of all data
/localhome/actiniad/.local/bin/grass /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_1_flood_pseudocolor \
--exec /hdata/fjernanalyse3/CopernicusUtviklingOgTest/t.register.local --overwrite -o \
input="/hdata/fjernanalyse3/flomtjeneste/results" \
suffix="tif" units="classification" output="Sentinel_1_flood_pseudocolor" \
semantic_labels="/hdata/fjernanalyse3/CopernicusUtviklingOgTest/data_import/semantic_labels_pseudocolor.txt" \
long_name="flood coverage pseudocolor from Sentinel-1" nprocs=5 nodata=255 time_format="%Y%m%d" \
file_pattern="*/[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_[0-9][0-9][0-9][0-9]_*_*_pseudocolor"

# Create mapset if it does not exist
rm -rf /localhome/actiniad/actinia/userdata/user/ETRS_33N/S3vsS2_snow_500
/localhome/actiniad/.local/bin/grass -c -e /localhome/actiniad/actinia/userdata/user/ETRS_33N/S3vsS2_snow_500

# Run import / registration of all data
/localhome/actiniad/.local/bin/grass /localhome/actiniad/actinia/userdata/user/ETRS_33N/S3vsS2_snow_500 \
--exec /hdata/fjernanalyse3/CopernicusUtviklingOgTest/t.register.local --overwrite -o \
input="/hdata/gis-srv15/ImageServer/Data/s3/S3vsS2_snow_500" \
suffix="tif" units="classification" output="S3vsS2_snow_500" \
semantic_labels="/hdata/fjernanalyse3/CopernicusUtviklingOgTest/data_import/semantic_labels_S2vsS3.txt" \
long_name="Difference between Sentinel-2 and Sentinel-3 snow coverage" nprocs=5 nodata=255 time_format="%Y%m%d"

# Create mapset if it does not exist
rm -rf /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_3_SLSTR_fractional_snow_cover_sca
/localhome/actiniad/.local/bin/grass -c -e /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_3_SLSTR_fractional_snow_cover_sca

# Run import / registration of all data
/localhome/actiniad/.local/bin/grass /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_3_SLSTR_fractional_snow_cover_sca \
--exec t.register.local --overwrite -o \
input="/hdata/gis-srv15/ImageServer/Data/s3/SLSTR_sca" \
suffix="tif" units="classification" output="Sentinel_3_SLSTR_fractional_snow_cover_sca" \
semantic_labels="/hdata/fjernanalyse3/CopernicusUtviklingOgTest/data_import/semantic_labels_S3_fsc.txt" \
file_pattern="*s3*slstr*sca-snomap-color*_500*" \
long_name="Fractional snow cover from SLSTR instrument on Sentinel-3" nprocs=5 nodata=255 time_format="%Y%m%d_%H%M%S"

python3 -c 'import grass.script as gs
reclass_rules = "\n".join([f"{i + 100} = {i}" for i in range(0, 101)])
reclass_rules = f"0 thru 99 = NULL\n{reclass_rules}\n* = NULL\n"

reclass_file_path = gs.tempfile(create=False)
with open(reclass_file_path, "w") as register_file:
    register_file.write(reclass_rules)

gs.run_command("t.rast.reclass",
               input="Sentinel_3_SLSTR_fractional_snow_cover_sca@Sentinel_3_SLSTR_fractional_snow_cover_sca",
               semantic_label="percent",
               nprocs=25,
               output="Sentinel_3_SLSTR_fractional_snow_cover_sca_perc",
               rules=reclass_file_path,
               title="Sentinel-3 fractional snow cover",
               description="Sentinel-3 fractional snow cover",
               overwrite=True,
               verbose=True,
               )

# Create mapset if it does not exist
rm -rf /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_3_SLSTR_fractional_snow_cover_sca_klein
/localhome/actiniad/.local/bin/grass -c -e /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_3_SLSTR_fractional_snow_cover_sca_klein

# Run import / registration of all data
/localhome/actiniad/.local/bin/grass /localhome/actiniad/actinia/userdata/user/ETRS_33N/Sentinel_3_SLSTR_fractional_snow_cover_sca_klein \
--exec /hdata/fjernanalyse3/CopernicusUtviklingOgTest/t.register.local --overwrite -o \
input="/hdata/gis-srv15/ImageServer/Data/s3/SLSTR_sca" \
suffix="tif" units="classification" output="Sentinel_3_SLSTR_fractional_snow_cover_sca_klein" \
semantic_labels="/hdata/fjernanalyse3/CopernicusUtviklingOgTest/data_import/semantic_labels_S3_fsc.txt" \
file_pattern="*sca-snomap-klein-color*" \
long_name="Fractional snow cover from SLSTR instrument on Sentinel-3 (Klein algorithm)" nprocs=25 nodata=255 time_format="%Y%m%d_%H%M%S"

python3 -c 'import grass.script as gs
reclass_rules = "\n".join([f"{i + 100} = {i}" for i in range(0, 101)])
reclass_rules = f"0 thru 99 = NULL\n{reclass_rules}\n* = NULL\n"

reclass_file_path = gs.tempfile(create=False)
with open(reclass_file_path, "w") as register_file:
    register_file.write(reclass_rules)

gs.run_command("t.rast.reclass",
               input="Sentinel_3_SLSTR_fractional_snow_cover_sca_klein@Sentinel_3_SLSTR_fractional_snow_cover_sca_klein",
               semantic_label="percent",
               nprocs=25,
               output="Sentinel_3_SLSTR_fractional_snow_cover_sca_klein_perc",
               rules=reclass_file_path,
               title="Sentinel-3 fractional snow cover (Klein algorithm)",
               description="Sentinel-3 fractional snow cover (Klein algorithm)",
               overwrite=True,
               verbose=True,
               )



/hdata/gis-srv15/ImageServer/Data/s3/SLSTR_sca_klein
/hdata/gis-srv15/ImageServer/Data/s3/slstr_fsc_sa
