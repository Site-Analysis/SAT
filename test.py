import ee

KEY_PATH = r""

try:
    credentials = ee.ServiceAccountCredentials(
        "",
        KEY_PATH,
    )
    ee.Initialize(credentials)
    print("Earth Engine initialized successfully")
except Exception as e:
    print(e)
image = ee.Image("USGS/SRTMGL1_003")
print(image.getInfo())
