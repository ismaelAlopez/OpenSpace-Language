import pandas
import re


input_csv = "exoplanets_with_additional_columns.csv"
input_speck = "expl.speck"
input_label = "expl.label"
output_speck = "hwc.speck"
output_label = "hwc.label"

columns = [
    "Name",
    "Star",
    "S_RA",
    "S_DEC",
    "P_DISTANCE",
]

#clean star names in the CSV file
def clean_name(name):
    return re.sub(r"\s*\(.*\)", "", name).strip().lower()

# read files
exoplanetsCSV = pandas.read_csv(input_csv, usecols=columns)
starName = set(clean_name(name) for name in exoplanetsCSV["Star"].unique())
print(starName)
star_set = set(clean_name(s) for s in exoplanetsCSV["Star"].astype(str))

# Write hwc.speck
with open(input_speck, "r", encoding="utf-8") as speckFile, \
     open(output_speck, "w", encoding="utf-8") as outSpeck:
    for line in speckFile:
        if "#" in line:
            name = line.split("#", 1)[1].strip()
            data = line.split("#")[0].strip()
            fields = data.split()
            if len(fields) >= 3 and clean_name(name) in star_set:
                outSpeck.write(f"{fields[0]} {fields[1]} {fields[2]} # {name}\n")

# Write hwc.label
with open(input_label, "r", encoding="utf-8") as labelFile, \
     open(output_label, "w", encoding="utf-8") as outLabel:
    for line in labelFile:
        if "text" in line:
            name = line.split("text", 1)[1].strip()
            data = line.split("text")[0].strip()
            fields = data.split()
            if len(fields) >= 3 and clean_name(name) in star_set:
                outLabel.write(f"{fields[0]} {fields[1]} {fields[2]} text {name}\n")