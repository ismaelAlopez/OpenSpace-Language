# PHL Habitability Catalog (HWC) Exoplanets Task
# This task uses the PHL Habitability Catalog (HWC) data a CSV file downloaded from the PHL website
# It will create asset files for each exoplanet in the dataset, which can be used in OpenSpace.
# web page: https://phl.upr.edu/hwc/data
# It will use the NASA Exoplanet Archive to fetch additional parameters for the host stars of the exoplanets.
# This script requires the following Python packages:
# pandas, numpy, requests, io, os, glob, and StringIO.
# Author: Ismael A. Lopez Perez
# In collaboration with PHL (Planetary Habitability Laboratory) and OpenSpace

import pandas as pd
import os
import glob
import numpy as np
from io import StringIO
import requests

EXOPLANET_DATA_HWC = "hwc_table_all.csv"
FULL_EXOPLANET_DATA_HWC = "hwc.csv"
OUTPUT_DIR = "../../../user/data/assets/Exoplanets"


# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Remove old asset files in the output directory
for old_asset in glob.glob(os.path.join(OUTPUT_DIR, "*.asset")):
    os.remove(old_asset)

# Read the CSV file from the PHL Habitability Catalog (HWC)
EXOPLANET_DATA_HWC_columns = [
    "Name",
    "Type",
    "Detection Method",
    "Mass<br>(M<sub>E</sub>)",
    "Flux<br>(S<sub>E</sub>)",
    "<i>T<sub>surf</sub></i><br>(K)",
    "Period<br>(days)",
    "Age<br>(Gy)",
    "ESI",
    "Star",
]
exoplanetData = pd.read_csv(EXOPLANET_DATA_HWC, usecols=EXOPLANET_DATA_HWC_columns)

# Read the full CSV file with additional columns
FULL_EXOPLANET_DATA_HWC_columns = [
    "P_NAME",               # Exoplanet name
    "P_YEAR",               # Year of discovery
    "S_RA",                 # Right Ascension
    "S_DEC",                # Declination
    "S_DISTANCE",           # Distance of the star
    "P_RADIUS",             # Planetary radius
    "P_DISCOVERY_FACILITY", # Discovery facility
    "P_TYPE_TEMP",          # Host star temperature
    "P_DISTANCE"            # Distance of the exoplanet

]
data_full = pd.read_csv(FULL_EXOPLANET_DATA_HWC, usecols=FULL_EXOPLANET_DATA_HWC_columns)

# New data with the additional columns 
exoplanetData = pd.merge(exoplanetData, data_full, left_on="Name", right_on="P_NAME", how="left")
exoplanetData = exoplanetData.drop(columns=["P_NAME"])
# Make a CSV file to save the data with the additional columns
exoplanetData.to_csv("exoplanets_with_additional_columns.csv", index=False)
print("Saved exoplanet data with additional columns to exoplanets_with_additional_columns.csv")

# Find the stars for each of the exoplanets in HWC
HOST_STARS = exoplanetData["Star"].unique()

# Prepare results
results = []
# Loop through each host star and query the NASA Exoplanet Archive for parameters
# This will fetch the host star parameters such as RA, DEC, distance, and radius
for star in HOST_STARS:
    # NASA Exoplanet Archive TAP query for host star parameters
    query = (
        "select hostname,ra,dec,sy_dist,st_rad "
        "from ps "
        f"where hostname='{star.replace('\'', '\'\'')}'"
    )
    url = (
        "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?"
        f"query={query}&format=csv"
    )
    try:
        r = requests.get(url)
        if r.status_code == 200 and len(r.text.splitlines()) > 1:
            df = pd.read_csv(StringIO(r.text))
            if not df.empty:
                row = df.iloc[0]
                results.append({
                    "Star": row['hostname'],
                    "RA": row['ra'],
                    "DEC": row['dec'],
                    "Distance_pc": row['sy_dist'],
                    "Radius_solar": row['st_rad']
                })
            else:
                results.append({"Star": star, "RA": None, "DEC": None, "Distance_pc": None, "Radius_solar": None})
        else:
            results.append({"Star": star, "RA": None, "DEC": None, "Distance_pc": None, "Radius_solar": None})
    except Exception as e:
        print(f"Error for {star}: {e}")
        results.append({"Star": star, "RA": None, "DEC": None, "Distance_pc": None, "Radius_solar": None})

# Save to CSV
pd.DataFrame(results).to_csv("host_stars_from_nasa.csv", index=False)
print("Saved host star data to host_stars_from_nasa.csv")

# Read the created CSV file
EXOPLANET_DATA_HWC_NASA = "host_stars_from_nasa.csv"
OUTPUT_DIR = "../../../user/data/assets/Exoplanets"
# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)
# Read the updated CSV with host star data
EXOPLANET_DATA_HWC_NASA_columns = [
    "Star",
    "RA",
    "DEC",  
    "Distance_pc",
    "Radius_solar"
]
starData = pd.read_csv(EXOPLANET_DATA_HWC_NASA, usecols=EXOPLANET_DATA_HWC_NASA_columns)
#
# Template for exoplanet asset file
# 
# The PLANET_TEMPLATE is used to create the asset files for each exoplanet
# It includes the necessary parameters such as identifier, parent star, radii, name, and position in the scene graph.
#
# START_TEMPLATE is used to create the asset files for each star
# It includes the necessary parameters such as identifier, radii, name, and position in the scene graph.
#
STAR_TEMPLATE = """
local core = asset.require("spice/core")

local textures = asset.resource({{
  Type = "HttpSynchronization",
  Name = "Sun textures",
  Identifier = "sun_textures",
  Version = 4
}})

local {identifier}_texture = {{
    Identifier = "Texture",
    Name = "{name}",
    Enabled = true,
    ZIndex = 5,
    FilePath = textures .. "sun.jpg",
    CacheSettings = {{ Enabled = false }}
}}

local {identifier} = {{
    Identifier = "{identifier}",
    Parent =  "SolarSystemBarycenter",
    Transform = {{
       Translation = {{
            Type = "StaticTranslation",
            Position = {{  {x}, {y}, {z} }}  -- Distance in meters (1 light year = 9.461e15 meters);
        }}
   }},
    Renderable = {{
        Type = "RenderableGlobe",
        Radii = {radii},  -- Approximate radius of the Sun in meters
        PerformShading = false,
    }},
    ApproachFactor = 50.0,
    GUI = {{
        Name = "Estrella_{name}",
        Path = "/Vía Láctea/Catalogo de Planetas Habitables/Sistemas de Exoplanetas/Estrella_{name}"
    }}
}}

local {identifier}_label = {{
    Identifier = "{identifier}_label",
    Parent = {identifier}.Identifier,
    Renderable = {{
        Type = "RenderableLabel",
        Enabled = false,
        Text = "{name}",
        FontSize = 70.0,
        Size = 8.50,    
        MinMaxSize = {{1, 50}},
        OrientationOption = "Camera View Direction",
        BlendMode = "Normal",
        EnableFading = true,
        FadeUnit = "au",
        FadeDistances = {{ 1.0, 30.0 }},
        FadeWidths = {{ 1.0, 40.0 }}
    }},
    GUI = {{
        Name = "Etiqueta de Estrella {name}",
        Path = "/Vía Láctea/Catalogo de Planetas Habitables/Sistemas de Exoplanetas/Estrella_{name}"
    }}
}}
asset.onInitialize(function()
    openspace.addSceneGraphNode({identifier})
    openspace.addSceneGraphNode({identifier}_label)
    openspace.globebrowsing.addLayer({identifier}.Identifier, "ColorLayers", {identifier}_texture)
end)

asset.onDeinitialize(function()
    openspace.globebrowsing.deleteLayer({identifier}.Identifier, "ColorLayers", {identifier}_texture)
    openspace.removeSceneGraphNode({identifier}_label)
    openspace.removeSceneGraphNode({identifier})
end)

asset.export({identifier})
asset.export({identifier}_label)
asset.export({identifier}_texture)
"""
# TODO - Add the detail and Grayscale textures for the stars
PLANET_TEMPLATE = """
asset.require("./Estrella_{assetRequire}")

-- get the textures for the exoplanet
local textures = asset.resource({{
  Type = "HttpSynchronization",
  Name = "Texturas de HWC",
  Identifier = "hwc_textures",
  Version = 1
}})

-- detail texture for the exoplanet
local {identifier}_detail = {{
    Identifier = "DetailTexture",
    Name = "Detalle de {name}",
    Enabled = true,
    ZIndex = 5, 
    FilePath = textures .. "detail5.png",
    CacheSettings = {{ Enabled = false }}
}}

-- texture for the exoplanet
local {identifier}_texture = {{
    Identifier = "Texture",
    Name = "Textura de {name}",
    Enabled = true,
    ZIndex = 5,
    FilePath = textures .. "{temperature}",  -- Use the temperature to select the texture
    CacheSettings = {{ Enabled = false }}
}}

local {identifier} = {{
    Identifier = "{identifier}",
    Parent = "{parent}",
    PerformShading = false,
    Transform = {{
        Translation = {{
            Type = "StaticTranslation",
            Position = {{ {x}, {y}, {z} }}  -- Distance in meters (1 light year = 9.461e15 meters);
        }},
    }},
    Renderable = {{
        Type = "RenderableGlobe",
        Radii = {radii},
        PerformShading = false,
    }},
    ApproachFactor = 50.0,
    GUI = {{
        Name = "{name}",
        Path = "/Vía Láctea/Catalogo de Planetas Habitables/Sistemas de Exoplanetas/{name}"
    }},
}}

local {identifier}_label = {{
    Identifier = "{identifier}_label",
    Parent = {identifier}.Identifier,
    Renderable = {{
        Type = "RenderableLabel",
        Enabled = false,
        Text = "{name}",
        FontSize = 70.0,
        Size = 8.50,    
        MinMaxSize = {{1, 50}},
        OrientationOption = "Camera View Direction",
        BlendMode = "Additive",
        EnableFading = true,
        FadeUnit = "au",
        FadeDistances = {{ 1.5, 30.0 }},
        FadeWidths = {{ 1.0, 40.0 }},
    }},
    GUI = {{
        Name = "Etiqueta de {name}",
        Path = "/Vía Láctea/Catalogo de Planetas Habitables/Sistemas de Exoplanetas/{name}"
    }},
}}

asset.onInitialize(function()
    openspace.addSceneGraphNode({identifier})
    openspace.addSceneGraphNode({identifier}_label)

    openspace.globebrowsing.addLayer({identifier}.Identifier, "ColorLayers", {identifier}_texture)
    openspace.globebrowsing.addLayer({identifier}.Identifier, "ColorLayers", {identifier}_detail)
end)

asset.onDeinitialize(function()
    openspace.globebrowsing.deleteLayer({identifier}.Identifier, "ColorLayers", {identifier}_texture)
    openspace.globebrowsing.deleteLayer({identifier}.Identifier, "ColorLayers", {identifier}_detail)

    openspace.removeSceneGraphNode({identifier}_label)
    openspace.removeSceneGraphNode({identifier})
end)

asset.export({identifier})
asset.export({identifier}_label)
asset.export({identifier}_texture)
asset.export({identifier}_detail)

asset.meta = {{
    Name = "{name}",
    Description = "Asset for the exoplanet {name} in the PHL Habitability Catalog (HWC). It was detected using the {detection} method and discovered by {discovery_facility} in {discovery_year}.",
    Author = "PHL Habitability Catalog (HWC)",
    URL = "https://phl.upr.edu/hwc",
    Version = "1.0"
}}

"""
Master_ASSET_PATH = """
asset.require("./{identifier}.asset")
"""
#
# Functions to sanitize identifiers and to convert the RA, DEC, and distance to meters
#
# The Sanitize replaces the spaces, apostrophes, and hyphens in the name with underscores
# The toMeters function converts the RA, DEC, and distance in light years to meters
# 
def sanitize_identifier(name):
    return name.replace(" ", "_").replace("'", "").replace("-", "_").replace(".", "_").replace("\\", "_").replace("/", "_")

def sanitize_star_name(name):
    return name.replace("'", "").replace(" ", "_").replace("-", "_").replace(".", "_").replace("\\", "_").replace("/", "_")

def toMeters(RA, DEC, distance_ly):
    """
    Convert RA, DEC, and distance in light years to meters.
    RA and DEC are in degrees, distance is in light years.
    """
    # Convert RA and DEC from degrees to radians
    RA_rad = np.radians(RA)
    DEC_rad = np.radians(DEC)
    
    # Convert distance from light years to meters
    distance_meters = distance_ly * 9.461e15  # 1 light year = 9.461e15 meters
    
    # Calculate the position in Cartesian coordinates
    x = distance_meters * np.cos(DEC_rad) * np.cos(RA_rad)
    y = distance_meters * np.cos(DEC_rad) * np.sin(RA_rad)
    z = distance_meters * np.sin(DEC_rad)
    
    return x, y, z
#
# Loops throught the data and data2 
# to create the asset files for each exoplanet, its host star
# and the master asset file
#

# Define the colors for the exoplanets based on their equilibrium temperature
# The colors are used to create the texture for the exoplanets
colors = {
    "warm": "warm.jpg",
    "hot": "hot.jpg",
    "cold": "cold.jpg",
}
planet_offset = 1e10 # Offset to avoid overlap in positions
for i, row in exoplanetData.iterrows():
    name = row["Name"]
    star = row["Star"]
    temp = row["<i>T<sub>surf</sub></i><br>(K)"] if pd.notnull(row["<i>T<sub>surf</sub></i><br>(K)"]) else 0.0
    # get the radii and distances, using default values if not available
    ra = row["S_RA"] if pd.notnull(row["S_RA"]) else 0.0
    dec = row["S_DEC"] if pd.notnull(row["S_DEC"]) else 0.0
    exoplanetRadii = float(row["P_RADIUS"]) * 6371000 if pd.notnull(row["P_RADIUS"]) else 6371000
    exoplanetDistance = float(row["P_DISTANCE"]) if pd.notnull(row["P_DISTANCE"]) else 0.0

    # Ensure theres is no overlap in positions
    # Call sanitize_identifier to create a valid identifier
    starIdentifier = sanitize_star_name(star)
    planetIdentifier = sanitize_identifier(name)
    # Convert RA and DEC to meters
    x, y, z = toMeters(ra, dec, exoplanetDistance) # This commented to have the of the exoplanet close to the star

    # Choose the texture based on the equilibrium temperature
    if temp < 240:
        exoplanetTexture = colors["cold"]
    elif temp >= 240 and temp <= 370:
        exoplanetTexture = colors["warm"]
    elif temp > 370:
        exoplanetTexture = colors["hot"]
    else:
        exoplanetTexture = "unknown.jpg"

    exoplanet_content = PLANET_TEMPLATE.format(
        assetRequire=starIdentifier,
        identifier=planetIdentifier,
        parent=starIdentifier,
        radii=exoplanetRadii,
        name=name,
        x=x,
        y=y,
        z=z,
        # name of the texture file for the exoplanet
        temperature= exoplanetTexture,
        # Add the additional parameters if they exist, it is use for the asset.meta
        detection = row["Detection Method"] if pd.notnull(row["Detection Method"]) else "Unknown",
        discovery_facility = row["P_DISCOVERY_FACILITY"] if pd.notnull(row["P_DISCOVERY_FACILITY"]) else "Unknown",
        discovery_year = row["P_YEAR"] if pd.notnull(row["P_YEAR"]) else "Unknown",

    )
    # Change the offset for the next exoplanet
    planet_offset += 1e10  # Increment the offset for the next exoplanet
    # Write to file
    with open(os.path.join(OUTPUT_DIR, f"{planetIdentifier}.asset"), "w", encoding="utf-8") as f:
        f.write(exoplanet_content)

# Star data is in the starData
for _, row in starData.iterrows():
    star = row["Star"]
    # Call sanitize_star_name to create a valid identifier
    starIdentifier = sanitize_star_name(star)
    # Get the star parameters, using default values if not available
    starRadii = float(row["Radius_solar"]) * 695700000 if pd.notnull(row["Radius_solar"]) else 695700000
    starDistance = float(row["Distance_pc"]) * 3.26156 if pd.notnull(row["Distance_pc"]) else 0.0
    starDEC = float(row["DEC"]) if pd.notnull(row["DEC"]) else 0.0
    starRA = float(row["RA"]) if pd.notnull(row["RA"]) else 0.0
    # Convert RA and DEC to meters
    star_x, star_y, star_z = toMeters(starRA, starDEC, starDistance)
# Create the asset content
    star_content = STAR_TEMPLATE.format(
        identifier=starIdentifier,
        radii=starRadii,
        name=star,
        x= star_x,  
        y= star_y,  
        z= star_z  
    )
    # Write to file
    star_asset_path = os.path.join(OUTPUT_DIR, f"Estrella_{starIdentifier}.asset")
    with open(star_asset_path, "w", encoding="utf-8") as f:
            f.write(star_content)

# Create a master asset file that includes all generated exoplanet assets
master_asset_path = os.path.join(OUTPUT_DIR, "all_exoplanets.asset")
with open(master_asset_path, "w", encoding="utf-8") as master_file:
    for _, row in exoplanetData.iterrows():
        identifier = sanitize_identifier(row["Name"])
        master_file.write(Master_ASSET_PATH.format(identifier=identifier))

print("Asset files created in", OUTPUT_DIR)