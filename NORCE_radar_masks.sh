#!/bin/bash

source_dir=/hdata/fjernanalyse3/CopernicusUtviklingOgTest/Vaatsnoe_NORCE
cd /tmp

tracks=$(find $source_dir -name "*Mask*.tif" -exec basename {} \; | cut -f2 -d"_" | cut -f1 -d"." | sort | uniq)

mosaics="Mean|bilinear|Average backscatter intensity
Mask|nearest|Shadow, layover and no data mask
Linc|bilinear|Local incidence angle in degree
"

eval "$(g.region -ug raster=DTM_20m_Norge_Sverige@DTM)"

for t in $tracks
do
  t_id=$(echo $t | sed 's/^0*//')
  echo $t $t_id
  while read -r m
  do
    echo "$m"
    m_id=$(echo $m | cut -f1 -d"|")
    resample=$(echo $m | cut -f2 -d"|")
    title=$(echo $m | cut -f3 -d"|")
    if [ $m_id == "Mean" ] ; then
      pols="VV VH"
    else
      pols="."
    fi
    for p in $pols
    do
      find $source_dir -wholename "*NVE_*z*${m_id}_${t}*${p}*tif" > "vrt_input_${m_id}_${t}.txt"
      if [ "$p" == "." ] ; then
        raster_map="Sentinel_1_${m_id}_${t_id}"
        semantic_label="S1_${m_id}_${t_id}"
      else
        raster_map="Sentinel_1_${p}_${t_id}_${m_id}"
        semantic_label="S1_${p}_${t_id}_${m_id}"
        title="${title} with ${p} polarization"
      fi
      #maps=$(find $source_dir -wholename "*NVE_*z*${m_id}_${t}*${p}*tif")
      #i=0
      #for ma in $maps
      #do
      #  r.in.gdal --o --v -o input="$ma" output="${raster_map}_t${i}" memory=2048
      #  i=$((i+1))
      #done
      #emaps=$(g.list type=raster pattern="${raster_map}_t*" sep=",")
      #g.region -p raster="$emaps" align=DTM_20m_Norge_Sverige@DTM
      #r.patch --o --v input="$emaps" output="$raster_map" nprocs=1
      # r.out.gdal --o --v input="$raster_map" output="/hdata/fjernanalyse3/Sentinel1/NORCE_masks_wetsnow/${raster_map}" format=COG createopt="BIGTIFF=YES,PREDICTOR=2,COMPRESS=ZSTD,LEVEL=9,OVERVIEW_COUNT=8,OVERVIEW_RESAMPLING=NEAREST,STATISTICS=YES"
      gdalbuildvrt -r "$resample" -tap -tr "$ewres" "$nsres" -input_file_list "vrt_input_${m_id}_${t}.txt" "/tmp/${raster_map}.vrt"
      gdal_translate -of COG -co "BIGTIFF=YES" -co "PREDICTOR=2" -co "COMPRESS=ZSTD" -co "LEVEL=9" -co "OVERVIEW_COUNT=8" -co "OVERVIEW_RESAMPLING=NEAREST" -co "STATISTICS=YES" "/tmp/${raster_map}.vrt" "/tmp/${raster_map}.tif"
      r.in.gdal -o --o --v input="/tmp/${raster_map}.tif" output="$raster_map" title="$title" memory=2048
      r.support map="$raster_map" semantic_label="$semantic_label"
      mv "/tmp/${raster_map}.tif" /hdata/fjernanalyse3/Sentinel1/NORCE_masks/
      rm "vrt_input_${m_id}_${t}.txt"
    done
  done < <(printf "$mosaics")
done
