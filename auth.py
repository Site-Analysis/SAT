import ee

credentials = ee.ServiceAccountCredentials(
    "",
    ""
)

ee.Initialize(credentials)
