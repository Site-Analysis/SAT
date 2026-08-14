import ee

credentials = ee.ServiceAccountCredentials(
    "karthikramoo55@gmail.com",
    "C:\\Program Files\\Json Keys\\third-ridge-473908-h6-46cae993d64c.json"
)

ee.Initialize(credentials)