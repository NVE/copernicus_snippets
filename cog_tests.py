from pathlib import Path
from datetime import datetime

from osgeo import gdal, gdalconst

gdal.UseExceptions()

# Convert files for tests

input_dir: Path = Path("//gis-srv15/SSD02/ImageServer/Data/S2/rgb11-8-4")
output_dir: Path = Path("//gis-srv15/SSD02/ImageServer/Data/S2_test/rgb11-8-4")

# Define variables
compression_levels: list[int] = [3, 9, 15]
days = ["20250305", "20250223", "20240916", "20240906", "20240827", "20240817", "20240807", "20240728", "20240718", "20240708"]

# Define translate options
translate_kwargs = {  # gdal.TranslateOptions()
    "format": "COG",
    "outputType": gdalconst.GDT_Byte,
    "creationOptions": {
        "BIGTIFF": "YES",
        "COMPRESS": "ZSTD",
        "PREDICTOR": 2,
        "STATISTICS": "YES",
        }
}

# Create output directory
output_dir.mkdir(parents=True, exist_ok=True)

# Run gdal_translate
with open(str(output_dir / "gdal_translate.log"), "w", encoding="UTF8") as of:
    for day in days:
        input_files = input_dir.glob(f"*{day}*.tif")
        for input_file in input_files:
            print(input_file)
            for level in compression_levels:
                out_dir = output_dir / str(level)
                out_dir.mkdir(parents=True, exist_ok=True)
                out_file = out_dir / f"{input_file.stem}_ZSTD_L{level}_P2.tif"
                translate_kwargs["creationOptions"]["LEVEL"] = level
                start_time = datetime.now()
                gdal.Translate(str(out_file), str(input_file), **translate_kwargs)
                end_time = datetime.now()
                print(f"Level {level} took {end_time - start_time}, output size is {out_file.stat().st_size}")
                of.write(f"{input_file},{level},{end_time - start_time},{out_file.stat().st_size}\n")


# Analyse conversion
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path

input_dir: Path = Path("//gis-srv15/SSD02/ImageServer/Data/S2/rgb11-8-4")
output_dir: Path = Path("//gis-srv15/SSD02/ImageServer/Data/S2_test/rgb11-8-4")
log = output_dir / "gdal_translate.log"
levels = [3,9,15]

def parse_time(x):
    return float(x.split(":")[0]) * 3600 + float(x.split(":")[1]) * 60 + float(x.split(":")[2])

def to_mb(x):
    return float(x) / (1024.0 * 1024.0)

df = pd.read_csv(
    str(log),
    names=["file_name", "compression_level", "write_time_sec", "file_size_mb"],
    dtype={
    "file_name": str,
    "compression_level": int,
    },
    converters={
    "write_time_sec": parse_time,
    "file_size_mb": to_mb}
)


df_n = pd.DataFrame({"write_time_3": [1.0 for r in df["compression_level"]  if r == 3]})
df_n["write_time_9"] = df["write_time_sec"][df["compression_level"] == 9].array / df["write_time_sec"][df["compression_level"] == 3].array
df_n["write_time_15"] = np.append(df["write_time_sec"][df["compression_level"] == 15].array, [np.nan]) / df["write_time_sec"][df["compression_level"] == 3].array
df_n["file_size_3"] = 1.0
df_n["file_size_9"] = df["file_size_mb"][df["compression_level"] == 9].array / df["file_size_mb"][df["compression_level"] == 3].array
df_n["file_size_15"] = np.append(df["file_size_mb"][df["compression_level"] == 15].array, [np.nan]) / df["file_size_mb"][df["compression_level"] == 3].array


df_n2 = df_n.loc[np.isnan(df_n["file_size_15"]) == False]
fig, ax = plt.subplots(figsize=(8,6))
ax.boxplot(x=[df_n2[f"write_time_{level}"] for level in levels],
           labels=levels)

plt.savefig(output_dir / "write_time_seconds_relative.png")
plt.show()


fig, ax = plt.subplots(figsize=(8,6))
ax.boxplot(x=[df_n2[f"file_size_{level}"] for level in [3,9,15]],
           labels=[3,9,15])
plt.savefig(output_dir / "file_size_relative.png")
plt.show()


print("write_time_sum", {l: np.sum(df["write_time_seconds"][df["compression_level"] == l].array) for l in levels})

sizes = {}
day = "20250305"
input_files = input_dir.glob(f"*{day}*.tif")
sizes["original"] = np.sum([float(input_file.stat().st_size) / (1024.0*1024.0) for input_file in input_files])
for level in levels:
    out_dir = output_dir / str(level)
    input_files = out_dir.glob(f"*{day}*.tif")
    sizes[f"zstd_level_{level}"] = np.sum([float(input_file.stat().st_size) / (1024.0*1024.0) for input_file in input_files])
sizes
print(sizes)
