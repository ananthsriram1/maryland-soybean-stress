var states = ee.FeatureCollection("TIGER/2018/States")
var countyDataset = ee.FeatureCollection("TIGER/2016/Counties")

// --- 1. Define Time Frame ---
var startDate = '2021-01-01';
var endDate = '2024-11-30'; 


var roi = ee.FeatureCollection(states)
print(roi.limit(10))

Map.addLayer(roi, {}, "States")

var Maryland = roi.filter(ee.Filter.eq('NAME', 'Maryland'))
Map.addLayer(Maryland, {color:'red'}, 'Maryland')

var marylandCounties = countyDataset.filterBounds(Maryland.geometry());
Map.addLayer(marylandCounties, {color: '808080'}, 'Maryland Counties');

Map.centerObject(Maryland, 8);
Map.addLayer(ee.Image().byte().paint(marylandCounties, 0, 2), {palette: '000000'}, 'Maryland Counties');


// --- 2. Define Helper Functions ---
function maskS2clouds(image) {
  var scl = image.select('SCL');
  var mask = scl.eq(4).or(scl.eq(5));
  return image.updateMask(mask).divide(10000);
}
function addNDVI(image) {
  var ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI');
  return image.addBands(ndvi);
}

// --- 3. Load and Process Satellite Data for a Single Month ---
// Using June 2023 as the example month
var sentinel2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
  .filterBounds(Maryland.geometry())
  .filterDate('2024-11-01', '2024-11-30')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20));

var sentinel2_ndvi = sentinel2.map(maskS2clouds).map(addNDVI);
var ndvi_median = sentinel2_ndvi.select('NDVI').median().clip(marylandCounties);

// =================================================================
//      NEW SECTION: Create and Apply the Soybean Mask
// =================================================================

// 4. Load the USDA Cropland Data Layer (CDL) for the same year.
var cdl = ee.ImageCollection('USDA/NASS/CDL')
              .filter(ee.Filter.date('2024-01-01', '2024-12-31'))
              .first()
              .select('cropland');

// 5. Create a binary mask where soybean pixels are 1 and everything else is 0.
var soybeanValues = [5, 26, 239, 240, 241, 254];
var soybeanMask = cdl.remap(soybeanValues, ee.List.repeat(1, soybeanValues.length)).unmask(0);

// 6. Apply this mask to your median NDVI image.
var soybean_ndvi = ndvi_median.updateMask(soybeanMask);

// --- Visualize the results to confirm the mask worked ---
var ndviParams = {min: 0, max: 1, palette: ['blue', 'white', 'green']};
Map.addLayer(soybean_ndvi, ndviParams, 'Soybean-Only NDVI');


// =================================================================
//      MODIFIED SECTION: Calculate Mean NDVI and Export
// =================================================================

print('Calculating mean NDVI for SOYBEAN-ONLY areas in each county...');

// 1. The function now uses the 'soybean_ndvi' image.
var calculateCountyMean = function(county) {
  var meanDictionary = soybean_ndvi.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: county.geometry(),
    scale: 30,
    maxPixels: 1e9
  });
  var meanNdvi = meanDictionary.get('NDVI');
  return county.set('meanSoybeanNDVI', meanNdvi);
};

// 2. Map the function over every county.
var ndviPerCounty = marylandCounties.map(calculateCountyMean);

// 3. Export the final FeatureCollection to Google Drive.
Export.table.toDrive({
  collection: ndviPerCounty,
  description: 'Export_MD_County_Soybean_NDVI_Nov2024',
  folder: 'GEE_Exports',
  fileNamePrefix: 'md_county_soybean_ndvi_nov_2024',
  fileFormat: 'CSV',
  selectors: ['NAME', 'meanSoybeanNDVI'] // Updated the column name
});