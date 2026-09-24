/**
 * English and Hindi text for the map module.
 *
 * Kept inside the module instead of en.ts / hi.ts so the feature stays fully
 * isolated. It follows the same rule as the main dictionaries: the Hindi map is
 * typed against the English keys, so a missing translation is a compile error.
 */
import { useCallback } from 'react'
import { useI18n } from '@/i18n'

const EN = {
  navLabel: 'Map',
  mapAria: 'Map of MPLADS works',
  loading: 'Loading map data…',

  publicTitle: 'Works on the map',
  publicDescription:
    'Every MPLADS work with a recorded location, coloured by its current status. Select a marker for details.',
  adminTitle: 'Risk map',
  adminDescription:
    'Where the flagged works are. Colour shows the risk level and larger markers are higher risk. Select a marker to review the work or update its geotag.',

  filterDistrict: 'District',
  filterStatus: 'Status',
  filterRisk: 'Risk level',
  colourBy: 'Colour markers by',
  colourRisk: 'Risk level',
  colourStatus: 'Status',
  all: 'All',

  legendTitle: 'Legend',
  notAssessed: 'Not assessed',
  plotted: '{shown} of {total} works shown on the map',
  missing: '{count} works have no recorded location yet.',
  approxNote: 'Locations in the sample dataset are approximate (near the district headquarters).',
  tilesFailed:
    'The map background could not load (no internet connection). Marker positions are still correct.',

  openDetails: 'Open details',
  progress: 'Progress',
  utilisation: 'Utilisation',
  allocated: 'Allocated',

  listTitle: 'View as list',
  colWork: 'Work',
  colDistrict: 'District',
  colStatus: 'Status',
  colRisk: 'Risk',
  colLocation: 'Location',

  selectedTitle: 'Selected work',
  selectHint: 'Select a marker on the map to see the work here.',
  clearSelection: 'Clear selection',
  noLocationList: 'Works without a location',
  noLocationHint: 'Select one to geotag it.',

  geotagTitle: 'Geotag',
  geotagCurrent: 'Recorded location',
  geotagNone: 'No location recorded',
  useGps: 'Use my current location',
  locating: 'Getting location…',
  pickOnMap: 'Pick on map',
  pickingHint: 'Click the map where the work is located.',
  stopPicking: 'Stop picking',
  latitude: 'Latitude',
  longitude: 'Longitude',
  accuracy: 'GPS accuracy about {metres} m',
  draftNote: 'The dashed marker shows the new position. It is not saved yet.',
  save: 'Save geotag',
  saving: 'Saving…',
  discard: 'Discard',
  saved: 'Location saved. The change is recorded in the activity log.',
  outOfIndia: 'These coordinates are outside India. Check the values.',
  invalidNumber: 'Enter a valid number.',
  gpsDenied:
    'Location permission was denied. Allow location access in the browser, or pick on the map.',
  gpsUnavailable: 'This device could not provide a location. Pick on the map instead.',
  gpsInsecure: 'GPS works only when the site is opened over HTTPS or on localhost.',

  locationTab: 'Location',
  locationTitle: 'Work location',
  coordinates: 'Coordinates',
  getDirections: 'Get directions',
  noLocationPublic: 'The location of this work has not been recorded yet.',
  noLocationAdmin:
    'No location recorded. Use GPS at the site, or pick the spot on the map.',
}

export type MapTextKey = keyof typeof EN

const HI: Record<MapTextKey, string> = {
  navLabel: 'मानचित्र',
  mapAria: 'एमपीलैड्स कार्यों का मानचित्र',
  loading: 'मानचित्र डेटा लोड हो रहा है…',

  publicTitle: 'मानचित्र पर कार्य',
  publicDescription:
    'दर्ज स्थान वाले सभी एमपीलैड्स कार्य, उनकी वर्तमान स्थिति के अनुसार रंगे हुए। विवरण के लिए किसी चिह्न को चुनें।',
  adminTitle: 'जोखिम मानचित्र',
  adminDescription:
    'चिह्नित कार्य कहाँ हैं। रंग जोखिम स्तर दर्शाता है और बड़े चिह्न अधिक जोखिम वाले हैं। कार्य की समीक्षा या उसका जियोटैग अद्यतन करने के लिए किसी चिह्न को चुनें।',

  filterDistrict: 'ज़िला',
  filterStatus: 'स्थिति',
  filterRisk: 'जोखिम स्तर',
  colourBy: 'चिह्नों का रंग',
  colourRisk: 'जोखिम स्तर',
  colourStatus: 'स्थिति',
  all: 'सभी',

  legendTitle: 'संकेत',
  notAssessed: 'आकलन नहीं हुआ',
  plotted: 'कुल {total} में से {shown} कार्य मानचित्र पर दिखाए गए',
  missing: '{count} कार्यों का स्थान अभी दर्ज नहीं है।',
  approxNote: 'नमूना डेटा में स्थान अनुमानित हैं (ज़िला मुख्यालय के आसपास)।',
  tilesFailed:
    'मानचित्र की पृष्ठभूमि लोड नहीं हो सकी (इंटरनेट कनेक्शन नहीं)। चिह्नों के स्थान फिर भी सही हैं।',

  openDetails: 'विवरण खोलें',
  progress: 'प्रगति',
  utilisation: 'उपयोग',
  allocated: 'आवंटित',

  listTitle: 'सूची के रूप में देखें',
  colWork: 'कार्य',
  colDistrict: 'ज़िला',
  colStatus: 'स्थिति',
  colRisk: 'जोखिम',
  colLocation: 'स्थान',

  selectedTitle: 'चयनित कार्य',
  selectHint: 'यहाँ कार्य देखने के लिए मानचित्र पर कोई चिह्न चुनें।',
  clearSelection: 'चयन हटाएँ',
  noLocationList: 'बिना स्थान वाले कार्य',
  noLocationHint: 'जियोटैग करने के लिए किसी एक को चुनें।',

  geotagTitle: 'जियोटैग',
  geotagCurrent: 'दर्ज स्थान',
  geotagNone: 'कोई स्थान दर्ज नहीं',
  useGps: 'मेरा वर्तमान स्थान लें',
  locating: 'स्थान प्राप्त हो रहा है…',
  pickOnMap: 'मानचित्र पर चुनें',
  pickingHint: 'मानचित्र पर वहाँ क्लिक करें जहाँ कार्य स्थित है।',
  stopPicking: 'चुनना बंद करें',
  latitude: 'अक्षांश',
  longitude: 'देशांतर',
  accuracy: 'जीपीएस सटीकता लगभग {metres} मी',
  draftNote: 'बिंदीदार घेरे वाला चिह्न नया स्थान दिखाता है। यह अभी सहेजा नहीं गया है।',
  save: 'जियोटैग सहेजें',
  saving: 'सहेजा जा रहा है…',
  discard: 'रद्द करें',
  saved: 'स्थान सहेजा गया। यह बदलाव गतिविधि लॉग में दर्ज है।',
  outOfIndia: 'ये निर्देशांक भारत से बाहर हैं। कृपया मान जाँचें।',
  invalidNumber: 'मान्य संख्या दर्ज करें।',
  gpsDenied:
    'स्थान की अनुमति नहीं दी गई। ब्राउज़र में स्थान की अनुमति दें, या मानचित्र पर चुनें।',
  gpsUnavailable: 'यह डिवाइस स्थान नहीं दे सका। कृपया मानचित्र पर चुनें।',
  gpsInsecure: 'जीपीएस केवल तभी काम करता है जब साइट HTTPS या localhost पर खुली हो।',

  locationTab: 'स्थान',
  locationTitle: 'कार्य का स्थान',
  coordinates: 'निर्देशांक',
  getDirections: 'रास्ता देखें',
  noLocationPublic: 'इस कार्य का स्थान अभी दर्ज नहीं किया गया है।',
  noLocationAdmin:
    'कोई स्थान दर्ज नहीं है। स्थल पर जीपीएस का उपयोग करें, या मानचित्र पर स्थान चुनें।',
}

export type MapText = (key: MapTextKey, vars?: Record<string, string | number>) => string

/** `tm('missing', { count: 4 })` - English fallback, `{name}` placeholders. */
export function useMapText(): MapText {
  const { language } = useI18n()
  return useCallback(
    (key: MapTextKey, vars?: Record<string, string | number>) => {
      let text = (language === 'hi' ? HI[key] : undefined) ?? EN[key]
      if (vars) {
        for (const [name, value] of Object.entries(vars)) {
          text = text.split(`{${name}}`).join(String(value))
        }
      }
      return text
    },
    [language],
  )
}
