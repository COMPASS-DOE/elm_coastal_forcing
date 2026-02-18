import pandas as pd
import xml.etree.ElementTree as et


df = pd.read_csv('../../data/buoys/noaa/coaa_coops_activestations.csv')

# Convert to GeoDataFrame
gdf = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(df.Longitude, df.Latitude),
    crs="EPSG:4326") # Specify coordinate reference system (WGS84)


gdf.to_file("../../data/buoys/noaa/coaa_coops_activestations.geojson", mode='w') #, driver='ESRI Shapefile')


#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# NONE OF THIS BELOW WORKS;  XML structure is weird and prevents getting the coordinate attributes.
fname = '../../data/stationsXML.jsp.xml'

# Parse the XML file
tree = et.parse(fname)
root = tree.getroot()

root.tag
root.attrib

for child in root:
    print(child.tag, child.attrib)

[elem.tag for elem in root.iter()]

result = pd.DataFrame([ dict(it.attrib) for it in root.find('.//station') ])

print(ET.tostring(root, encoding='utf8'))#.decode('utf8'))


for movie in root.iter('ns0:metadata'):
    print(movie.attrib)


#--------------------------------------------
# Also shite below here
wl_stations = pd.read_xml(#, xpath=".//stations")  #, attrs_only=True)#, parser='etree')
wl_stations.info()

wl_stations.metadata

# Initialize a list to store records
records = []

# Iterate over each 'record' element and extract field values
for record in root.findall('record'):
    print(record)

    # Construct a dictionary for each record using tag names and text
    record_data = {child.tag: child.text for child in record}
    records.append(record_data)

# Convert the list of records into a DataFrame
df = pd.DataFrame(records)
