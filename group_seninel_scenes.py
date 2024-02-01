def parse_s3_file_name(file_name):
    """Extract info from file name according to naming onvention:
    https://sentinels.copernicus.eu/web/sentinel/user-guides/sentinel-3-slstr/naming-convention
    """
    return {
        "mission_id": file_name[0:3],
        "instrument": file_name[4:6],
        "start_time": datetime.strptime(file_name[16:31], "%Y%m%dT%H%M%S"),
        "end_time": datetime.strptime(file_name[32:47], "%Y%m%dT%H%M%S"),
        "ingestion_time": datetime.strptime(file_name[48:63], "%Y%m%dT%H%M%S"),
        "duration": file_name[64:68],
        "cycle": file_name[69:72],
        "relative_orbit": file_name[73:76],
        "frame": file_name[77:81],
    }

def group_scenes(s3_files, granularity="1 day"):
    """
    Group scenes by information from the file name:
     1. mission ID
     2. product type
     3. temporal granule
     4. duration
     5. cycle
     6. relative orbit
     : param s3_filesv: list of pathlib.Path objects with Sentine1-3 files
    """
    for sfile in s3_files:
        s3_name_dict = parse_s3_file_name(sfile.name)
        group_id = "_".join([
            s3_name_dict['mission_id'],
            options["product_type"][2:],
            create_suffix_from_datetime(s3_name_dict['start_time'], granularity).replace("_", ""),
            s3_name_dict['duration'],
            s3_name_dict['cycle'],
            s3_name_dict["relative_orbit"]
        ])
        if group_id in groups:
            groups[group_id]["files"].append(sfile)
            if s3_name_dict["start_time"] < groups[group_id]["start_time"]:
                groups[group_id]["start_time"] = s3_name_dict["start_time"]
            if s3_name_dict["end_time"] > groups[group_id]["end_time"]:
                groups[group_id]["end_time"] = s3_name_dict["end_time"]
            groups[group_id]["frames"].append(s3_name_dict["frame"])
        else:
            groups[group_id] = {"files": [sfile],
                                "start_time": s3_name_dict["start_time"],
                                "end_time": s3_name_dict["end_time"],
                                "frames": [s3_name_dict["frame"]],
                               }
    return groups
