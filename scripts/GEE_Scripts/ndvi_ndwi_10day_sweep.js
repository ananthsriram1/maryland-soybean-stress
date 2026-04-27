/**
 * Maryland soybean NDVI + NDWI 10-day county time series (sweep export).
 *
 * What this does
 * - For each year in [START_YEAR, END_YEAR], builds 10-day composites over the growing season
 * - Computes NDVI and NDWI, masks to soybean pixels using that year's USDA CDL
 * - Reduces to county means and exports a single CSV per year to Google Drive
 *
 * Notes
 * - Uses Sentinel-2 SR Harmonized when available (2017+), otherwise Landsat 8/9 Collection 2 L2.
 * - Keeps all branching server-side via ee.Algorithms.If to avoid getInfo().
 *
 * Run
 * - Paste into the GEE Code Editor
 * - Set parameters in the CONFIG block
 * - Click Run, then start Exports in the Tasks tab
 */

// =========================
// CONFIG (edit as needed)
// =========================
var START_YEAR = 2008;
var END_YEAR = 2024;

// Growing season bounds (inclusive start, exclusive end)
var SEASON_START_MM_DD = '05-01';
var SEASON_END_MM_DD = '10-01';

// Composite interval length
var INTERVAL_DAYS = 10;

// Sentinel-2 cloud probability threshold (lower is stricter)
var S2_CLOUD_PROB_LT = 35;

// CDL soybean class values (matches your existing scripts)
var CDL_SOYBEAN_VALUES = [5, 26, 239, 240, 241, 254];

// Export settings
var DRIVE_FOLDER = 'GEE_Exports';
var EXPORT_PREFIX = 'MD_Soybean_10Day_TimeSeries';

// =========================
// Study area: Maryland + counties
// =========================
var states = ee.FeatureCollection('TIGER/2018/States');
var counties = ee.FeatureCollection('TIGER/2016/Counties');
var maryland = states.filter(ee.Filter.eq('NAME', 'Maryland'));
var marylandCounties = counties.filterBounds(maryland.geometry());

// =========================
// Helpers
// =========================
function dateFromYearAndMMDD(year, mmdd) {
  var parts = ee.String(mmdd).split('-');
  var month = ee.Number.parse(parts.get(0));
  var day = ee.Number.parse(parts.get(1));
  return ee.Date.fromYMD(year, month, day);
}

function soybeanMaskForYear(yearNum) {
  var start = ee.Date.fromYMD(yearNum, 1, 1);
  var end = ee.Date.fromYMD(yearNum, 12, 31);
  var cdl = ee.ImageCollection('USDA/NASS/CDL')
    .filterDate(start, end)
    .first()
    .select('cropland');

  var ones = ee.List.repeat(1, CDL_SOYBEAN_VALUES.length);
  return cdl.remap(CDL_SOYBEAN_VALUES, ones, 0).eq(1);
}

// Sentinel-2: join cloud probability + QA60
function s2CompositeMasked(region, start, end) {
  var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(region)
    .filterDate(start, end);

  var s2Cloud = ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY')
    .filterBounds(region)
    .filterDate(start, end);

  var joined = ee.ImageCollection(ee.Join.saveFirst('cloud_mask').apply({
    primary: s2,
    secondary: s2Cloud,
    condition: ee.Filter.equals({leftField: 'system:index', rightField: 'system:index'})
  }));

  var masked = joined.map(function(img) {
    img = ee.Image(img);
    var cloudProb = ee.Image(img.get('cloud_mask')).select('probability');
    var mask = cloudProb.lt(S2_CLOUD_PROB_LT).and(img.select('QA60').lt(1));
    return img.updateMask(mask).divide(10000);
  });

  return masked.median();
}

// Landsat 8/9 C2 L2: mask clouds/shadows; scale SR
function l8l9CompositeMasked(region, start, end) {
  var l8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2');
  var l9 = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2');

  var col = l8.merge(l9)
    .filterBounds(region)
    .filterDate(start, end)
    .map(function(img) {
      img = ee.Image(img);
      var qa = img.select('QA_PIXEL');
      // Bit 3: cloud, bit 4: cloud shadow (keep where both are 0)
      var mask = qa.bitwiseAnd(1 << 3).eq(0).and(qa.bitwiseAnd(1 << 4).eq(0));
      // Scale factors per USGS C2 L2 (SR)
      var sr = img.select('SR_B.').multiply(0.0000275).add(-0.2);
      return sr.updateMask(mask);
    });

  return col.median();
}

function indicesFromS2(comp) {
  var ndvi = comp.normalizedDifference(['B8', 'B4']).rename('NDVI');
  var ndwi = comp.normalizedDifference(['B8', 'B11']).rename('NDWI');
  return ndvi.addBands(ndwi);
}

function indicesFromLandsat(comp) {
  // Landsat: NIR=SR_B5, Red=SR_B4, SWIR1=SR_B6
  var ndvi = comp.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI');
  var ndwi = comp.normalizedDifference(['SR_B5', 'SR_B6']).rename('NDWI');
  return ndvi.addBands(ndwi);
}

function countyReduce(indicesImg, soybeanMask, startDate) {
  var masked = indicesImg.updateMask(soybeanMask);
  return masked.reduceRegions({
    collection: marylandCounties,
    reducer: ee.Reducer.mean(),
    scale: 30
  }).map(function(f) {
    return ee.Feature(f).set('date', ee.Date(startDate).format('YYYY-MM-dd'));
  });
}

function buildYearFeatureCollection(yearNum) {
  yearNum = ee.Number(yearNum);
  var seasonStart = dateFromYearAndMMDD(yearNum, SEASON_START_MM_DD);
  var seasonEnd = dateFromYearAndMMDD(yearNum, SEASON_END_MM_DD);

  var nDays = seasonEnd.difference(seasonStart, 'day');
  var offsets = ee.List.sequence(0, nDays.subtract(1), INTERVAL_DAYS);

  var soybeanMask = soybeanMaskForYear(yearNum);

  var perInterval = offsets.map(function(dayOffset) {
    dayOffset = ee.Number(dayOffset);
    var start = seasonStart.advance(dayOffset, 'day');
    var end = start.advance(INTERVAL_DAYS, 'day');

    var s2Col = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
      .filterBounds(maryland)
      .filterDate(start, end);

    // Server-side switch: S2 if there are images, otherwise Landsat
    var indices = ee.Image(ee.Algorithms.If(
      s2Col.size().gt(0),
      indicesFromS2(s2CompositeMasked(maryland, start, end)),
      indicesFromLandsat(l8l9CompositeMasked(maryland, start, end))
    ));

    return countyReduce(indices, soybeanMask, start);
  });

  return ee.FeatureCollection(perInterval).flatten()
    .map(function(f) { return ee.Feature(f).set('year', yearNum); });
}

// =========================
// Exports (client-side loop)
// =========================
var years = ee.List.sequence(START_YEAR, END_YEAR);
print('Years queued for export', years);

years.getInfo().forEach(function(y) {
  var year = ee.Number(y);
  var fc = buildYearFeatureCollection(year);

  Export.table.toDrive({
    collection: fc,
    description: EXPORT_PREFIX + '_' + y,
    folder: DRIVE_FOLDER,
    fileNamePrefix: EXPORT_PREFIX + '_' + y,
    fileFormat: 'CSV',
    selectors: ['NAME', 'date', 'year', 'NDVI', 'NDWI']
  });
});

print('Initialized exports. Start Tasks in the Exports tab.');
