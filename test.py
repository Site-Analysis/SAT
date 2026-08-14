import ee

KEY_PATH = r"C:\Program Files\Json Keys\third-ridge-473908-h6-46cae993d64c.json"

try:
    credentials = ee.ServiceAccountCredentials(
        "karthikramoo55@gmail.com",
        KEY_PATH,
    )
    ee.Initialize(credentials)
    print("Earth Engine initialized successfully")
except Exception as e:
    print(e)
image = ee.Image("USGS/SRTMGL1_003")
print(image.getInfo())