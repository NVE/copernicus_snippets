#!/bin/bash


# Example on STAC support in actinia for import and export
# See: https://mundialis.github.io/fossgis2022/stac-openeo-actinia/index.html for more details

# Please note that the following requests will fail if run again, as objects have already been created

# Set up connection
export ACTINIA_URL=http://nve-actinia.westeurope.cloudapp.azure.com:5000/api/v3
export AUTH='-u username:password'

# Create DLR STAC instance
STAC_JSON='{
"stac_instance_id": "dlr"
}'
curl ${AUTH} -X POST -i "${ACTINIA_URL}/stac/instances" -H "accept: application/json" -H "content-type: application/json" -d "$STAC_JSON"

# Register Sentinel-5P cloud data from DLR STAC instance
STAC_JSON='{
"stac_instance_id": "dlr",
"stac_url": "https://geoserver.dlr.loose.eox.at/ogc/stac/collections/S5P_TROPOMI_L2_OFFL_CLOUD"
}'

curl ${AUTH} -X POST -i "${ACTINIA_URL}/stac/collections" -H "accept: application/json" -H "content-type: application/json" -d "$STAC_JSON"

# Register Sentinel-1 L1 GRD from DLR STAC instance
STAC_JSON='{
"stac_instance_id": "dlr",
"stac_url": "https://geoserver.dlr.loose.eox.at/ogc/stac/collections/S1_L1_GRD"
}'

curl ${AUTH} -X POST -i "${ACTINIA_URL}/stac/collections" -H "accept: application/json" -H "content-type: application/json" -d "$STAC_JSON"

# Create AWS STAC instance
STAC_JSON='{
"stac_instance_id": "aws"
}'
curl ${AUTH} -X POST -i "${ACTINIA_URL}/stac/instances" -H "accept: application/json" -H "content-type: application/json" -d "$STAC_JSON"



# Register Sentinel-2 L2A data from AWS STAC instance
STAC_JSON='{
"stac_instance_id": "aws",
"stac_url": "https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a"
}'

curl ${AUTH} -X POST -i "${ACTINIA_URL}/stac/collections" -H "accept: application/json" -H "content-type: application/json" -d "$STAC_JSON"

# Now data from those STAC collections can be imported and used for processing
# Need to add an example

# Get some more information about the registered STACs
curl ${AUTH} "${ACTINIA_URL}/stac/collections/stac.aws.rastercube.sentinel-s2-l2a"
# Unfortunately it is in a "requester pays bucket"

# This is how import from STAC would work
STAC_IMPORT_JSON='{"list":[{
  "module": "importer",
  "id": "importer_DLR_S1_L1_GRD",
  "inputs":[
      {"import_descr": {
          "source": "stac.dlr.rastercube.S1_L1_GRD",
          "type": "stac",
          "semantic_label": "VH",
          "extent": {
               "spatial": {
                   "bbox": [[10.08057,59.61553,10.93976,60.17929]]},
               "temporal": {
                   "interval": [["2020-06-25", "2020-07-10"]]
                   }
            },
            "filter": {}
        },
    "param": "map",
    "value": "S1_L1_GRD_VH"
    }]
}],
   "version": "3"
}'
curl ${AUTH} -X POST -i "${ACTINIA_URL}/locations/ETRS_33N/mapsets/S1_L1_GRD_STAC_test/processing_async" -H "accept: application/json" -H "content-type: application/json" -d "$STAC_IMPORT_JSON"



# This is how import from STAC would work
STAC_IMPORT_JSON='{"list":[{
  "module": "importer",
  "id": "importer_S2_AWS_1",
  "inputs":[
      {"import_descr": {
          "source": "stac.aws.rastercube.sentinel-s2-l2a",
          "type": "stac",
          "semantic_label": "B01",
          "extent": {
               "spatial": {
                   "bbox": [[10.08057,59.61553,10.93976,60.17929]]},
               "temporal": {
                   "interval": [["2022-07-05", "2022-07-10"]]
                   }
            },
            "filter": {}
        },
    "param": "map",
    "value": "S2_B01"
    }]
}],
   "version": "3"
}'
curl ${AUTH} -X POST -i "${ACTINIA_URL}/locations/ETRS_33N/mapsets/S2_AWS_STAC_test/processing_async" -H "accept: application/json" -H "content-type: application/json" -d "$STAC_IMPORT_JSON"


# Register Sentinel-2 L2A data from AWS STAC instance
STAC_JSON='{
"stac_instance_id": "tamn",
}'
curl ${AUTH} -X POST -i "${ACTINIA_URL}/stac/instances" -H "accept: application/json" -H "content-type: application/json" -d "$STAC_JSON"

# Register Sentinel-2 L2A data from AWS STAC instance
STAC_JSON='{
"stac_instance_id": "tamn",
"stac_url": "https://tamn.snapplanet.io/collections/S2"
}'

curl ${AUTH} -X POST -i "${ACTINIA_URL}/stac/collections" -H "accept: application/json" -H "content-type: application/json" -d "$STAC_JSON"


# This is how import from STAC would work
STAC_IMPORT_JSON='{"list":[{
  "module": "importer",
  "id": "importer_S2_TAMN_1",
  "inputs":[
      {"import_descr": {
          "source": "stac.tamn.rastercube.S2",
          "type": "stac",
          "semantic_label": "B01",
          "extent": {
               "spatial": {
                   "bbox": [[10.08057,59.61553,10.93976,60.17929]]},
               "temporal": {
                   "interval": [["2022-07-01", "2022-07-15"]]
                   }
            },
            "filter": {}
        },
    "param": "map",
    "value": "S2_B01"
    }]
}],
   "version": "3"
}'
curl ${AUTH} -X POST -i "${ACTINIA_URL}/locations/ETRS_33N/mapsets/S2_TAMN_STAC_test/processing_async" -H "accept: application/json" -H "content-type: application/json" -d "$STAC_IMPORT_JSON"

