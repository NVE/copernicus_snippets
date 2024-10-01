#!/bin/bash

source_dir=/hdata/fjernanalyse3/CopernicusUtviklingOgTest/Vaatsnoe_NORCE
cd $source_dir

r.external.out directory=/hdata/fjernanalyse3/Sentinel1/NORCE_masks format=GTiff options="COMPRESS=LZW" extension=tif
r.external.out -p

tracks=$(find $source_dir -name "*Mask*.tif" -exec basename {} \; | cut -f2 -d"_" | cut -f1 -d"." | sort | uniq)

mosaics="Mean|bilinear|Average backscatter intensity
Mask|nearest|Shadow, layover and no data mask
Linc|bilinear|Local incidence angle in degree
"

eval `g.region -ug raster=DTM_20m_Norge_Sverige@DTM`

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
      find $source_dir -name "*${m_id}_${t}*${p}*tif" > vrt_input_${m_id}_${t}.txt
      if [ "$p" == "." ] ; then
        raster_map="Sentinel_1_${m_id}_${t_id}"
        semantic_label="S1_${m_id}_${t_id}"
      else
        raster_map="Sentinel_1_${p}_${t_id}_${m_id}"
        semantic_label="S1_${p}_${t_id}_${m_id}"
        title="${title} with ${p} polarization"
      fi
      gdalbuildvrt -r $resample -te $w $s $e $n -tr $ewres $nsres -input_file_list vrt_input_${m_id}_${t}.txt "${raster_map}.vrt"
      r.in.gdal -o --o --v input="${raster_map}.vrt" output="$raster_map" title="$title" memory=2048
      r.support map="$raster_map" semantic_label="$semantic_label"
      rm vrt_input_${m_id}_${t}.txt
    done
  done < <(printf "$mosaics")
done
