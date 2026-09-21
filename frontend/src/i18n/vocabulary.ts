/**
 * Hindi for the controlled vocabularies that arrive as data, not as enums.
 *
 * `enums.ts` covers values defined in `app/core/enums.py`. These four are
 * different: they are stored as plain strings on the `Project` row, so they look
 * like free text. They are not. Each is a closed list maintained in
 * `backend/seed/reference_data.py` - 15 states, 58 districts, 20 work categories
 * and 12 executing agencies - and MPLADS publishes all four in Hindi. Leaving
 * them in English meant a Hindi page showed "Drinking Water Facility" in the
 * category filter, which is exactly the leak `enums.ts` exists to prevent.
 *
 * What is deliberately NOT here: the title and description of an individual
 * work, the MP's name, the contractor, and the block. Those are genuinely
 * per-record free text entered by an officer. A government portal shows them as
 * they were entered, and machine-translating 600 unique strings would produce
 * worse Hindi than leaving them alone. That boundary - controlled vocabulary
 * translated, free text preserved - is the honest answer if anyone asks.
 *
 * As everywhere else, the English value is what travels on the wire. These maps
 * only change what is painted on screen, so filters and queries are untouched.
 */

type EnumMap = Record<string, string>

/** States represented in the dataset (reference_data.STATES keys). */
export const STATE_HI: EnumMap = {
  Maharashtra: 'महाराष्ट्र',
  'Uttar Pradesh': 'उत्तर प्रदेश',
  Karnataka: 'कर्नाटक',
  'Tamil Nadu': 'तमिलनाडु',
  'West Bengal': 'पश्चिम बंगाल',
  Rajasthan: 'राजस्थान',
  Bihar: 'बिहार',
  Gujarat: 'गुजरात',
  'Madhya Pradesh': 'मध्य प्रदेश',
  Kerala: 'केरल',
  Odisha: 'ओडिशा',
  Punjab: 'पंजाब',
  Assam: 'असम',
  Telangana: 'तेलंगाना',
  Haryana: 'हरियाणा',
}

/**
 * Districts (reference_data.STATES values) plus Sirohi, which has coordinates
 * and is used in the demo walkthrough.
 */
export const DISTRICT_HI: EnumMap = {
  // Maharashtra
  Pune: 'पुणे',
  Nagpur: 'नागपुर',
  Nashik: 'नासिक',
  Aurangabad: 'औरंगाबाद',
  Solapur: 'सोलापुर',
  Kolhapur: 'कोल्हापुर',
  // Uttar Pradesh
  Lucknow: 'लखनऊ',
  Varanasi: 'वाराणसी',
  'Kanpur Nagar': 'कानपुर नगर',
  Gorakhpur: 'गोरखपुर',
  Prayagraj: 'प्रयागराज',
  Meerut: 'मेरठ',
  // Karnataka
  'Bengaluru Urban': 'बेंगलुरु शहरी',
  Mysuru: 'मैसूरु',
  Belagavi: 'बेलगावी',
  Kalaburagi: 'कलबुरगी',
  Dharwad: 'धारवाड़',
  // Tamil Nadu
  Chennai: 'चेन्नई',
  Coimbatore: 'कोयंबटूर',
  Madurai: 'मदुरै',
  Tiruchirappalli: 'तिरुचिरापल्ली',
  Salem: 'सेलम',
  // West Bengal
  Kolkata: 'कोलकाता',
  Howrah: 'हावड़ा',
  Darjeeling: 'दार्जिलिंग',
  Murshidabad: 'मुर्शिदाबाद',
  // Rajasthan
  Jaipur: 'जयपुर',
  Jodhpur: 'जोधपुर',
  Udaipur: 'उदयपुर',
  Kota: 'कोटा',
  Sirohi: 'सिरोही',
  // Bihar
  Patna: 'पटना',
  Gaya: 'गया',
  Muzaffarpur: 'मुजफ्फरपुर',
  Bhagalpur: 'भागलपुर',
  // Gujarat
  Ahmedabad: 'अहमदाबाद',
  Surat: 'सूरत',
  Rajkot: 'राजकोट',
  Vadodara: 'वडोदरा',
  // Madhya Pradesh
  Bhopal: 'भोपाल',
  Indore: 'इंदौर',
  Jabalpur: 'जबलपुर',
  Gwalior: 'ग्वालियर',
  // Kerala
  Thiruvananthapuram: 'तिरुवनंतपुरम',
  Ernakulam: 'एर्नाकुलम',
  Kozhikode: 'कोझिकोड',
  // Odisha
  Khordha: 'खोरधा',
  Cuttack: 'कटक',
  Ganjam: 'गंजाम',
  // Punjab
  Ludhiana: 'लुधियाना',
  Amritsar: 'अमृतसर',
  Jalandhar: 'जालंधर',
  // Assam
  'Kamrup Metropolitan': 'कामरूप महानगर',
  Dibrugarh: 'डिब्रूगढ़',
  // Telangana
  Hyderabad: 'हैदराबाद',
  Warangal: 'वारंगल',
  // Haryana
  Gurugram: 'गुरुग्राम',
  Faridabad: 'फरीदाबाद',
  Hisar: 'हिसार',
}

/**
 * Parliamentary constituencies (the second element of each STATES tuple).
 * Most match their district; these are the ones that differ.
 */
export const CONSTITUENCY_HI: EnumMap = {
  ...DISTRICT_HI,
  'Ahmedabad East': 'अहमदाबाद पूर्व',
  'Bangalore North': 'बंगलौर उत्तर',
  Belgaum: 'बेलगाम',
  Berhampur: 'बरहमपुर',
  Bhubaneswar: 'भुवनेश्वर',
  'Chennai South': 'चेन्नई दक्षिण',
  Gauhati: 'गुवाहाटी',
  Gulbarga: 'गुलबर्गा',
  Gurgaon: 'गुड़गांव',
  'Jaipur Rural': 'जयपुर ग्रामीण',
  Kanpur: 'कानपुर',
  'Kolkata Dakshin': 'कोलकाता दक्षिण',
  Mysore: 'मैसूर',
  'Patna Sahib': 'पटना साहिब',
  Phulpur: 'फूलपुर',
  Secunderabad: 'सिकंदराबाद',
}

/** MPLADS work categories (reference_data.CATEGORIES). */
export const CATEGORY_HI: EnumMap = {
  'Drinking Water Facility': 'पेयजल सुविधा',
  'Education - School Buildings': 'शिक्षा – विद्यालय भवन',
  'Health & Family Welfare': 'स्वास्थ्य एवं परिवार कल्याण',
  'Roads, Pathways and Bridges': 'सड़क, मार्ग एवं पुल',
  'Sanitation and Public Health': 'स्वच्छता एवं सार्वजनिक स्वास्थ्य',
  'Community Halls': 'सामुदायिक भवन',
  'Electricity Facility - Street Lighting': 'विद्युत सुविधा – पथ प्रकाश',
  'Sports and Recreation': 'खेल एवं मनोरंजन',
  'Public Libraries': 'सार्वजनिक पुस्तकालय',
  'Irrigation Facility': 'सिंचाई सुविधा',
  'Railway Facilities': 'रेलवे सुविधाएँ',
  'Higher Education Facility': 'उच्च शिक्षा सुविधा',
  'Anganwadi and Child Care': 'आंगनवाड़ी एवं शिशु देखभाल',
  'Solar and Non-conventional Energy': 'सौर एवं गैर-पारंपरिक ऊर्जा',
  'Veterinary and Animal Husbandry': 'पशु चिकित्सा एवं पशुपालन',
  'Rainwater Harvesting': 'वर्षा जल संचयन',
  'Bus Shelters and Public Transport': 'बस आश्रय एवं सार्वजनिक परिवहन',
  'Cremation and Burial Grounds': 'श्मशान एवं कब्रिस्तान',
  'Skill Development Centres': 'कौशल विकास केंद्र',
  'Disability Welfare Facilities': 'दिव्यांग कल्याण सुविधाएँ',
}

/** Executing agencies (reference_data.AGENCIES). */
export const AGENCY_HI: EnumMap = {
  'Public Works Department (PWD)': 'लोक निर्माण विभाग (पीडब्ल्यूडी)',
  'Zilla Parishad Engineering Wing': 'जिला परिषद अभियांत्रिकी शाखा',
  'Municipal Corporation Works Division': 'नगर निगम कार्य प्रभाग',
  'Rural Development Engineering Department': 'ग्रामीण विकास अभियांत्रिकी विभाग',
  'Jal Jeevan Mission District Unit': 'जल जीवन मिशन जिला इकाई',
  'State Education Infrastructure Board': 'राज्य शिक्षा अवसंरचना बोर्ड',
  'District Health Society': 'जिला स्वास्थ्य समिति',
  'State Electricity Distribution Company': 'राज्य विद्युत वितरण कंपनी',
  'Panchayati Raj Engineering Department': 'पंचायती राज अभियांत्रिकी विभाग',
  'State Sports Authority - District Wing': 'राज्य खेल प्राधिकरण – जिला शाखा',
  'Irrigation Department - Division Office': 'सिंचाई विभाग – मंडल कार्यालय',
  'District Rural Roads Agency': 'जिला ग्रामीण सड़क अभिकरण',
}

/**
 * Risk-factor titles (FR9). Each is a fixed string emitted by a rule in
 * `app/risk/rules.py`, `statistical.py` or `anomaly.py` - eighteen in all, not
 * free text - so they translate cleanly and they are the first thing an officer
 * reads on a flagged work.
 *
 * The *description* underneath each one is not translated: it embeds the
 * measured numbers ("progress is 34% against a planned 71%") and is generated
 * per record. So Hindi mode shows a Hindi finding with the English evidence
 * line beneath it, which is the same split a bilingual government report uses.
 */
export const RISK_FACTOR_TITLE_HI: EnumMap = {
  'Physical progress is behind the planned schedule':
    'भौतिक प्रगति नियोजित समय-सारणी से पीछे है',
  'Deadline approaching with substantial work outstanding':
    'समय-सीमा निकट है और बड़ा कार्य शेष है',
  'Project is past its planned completion date and still open':
    'कार्य नियोजित पूर्णता तिथि पार कर चुका है और अब भी खुला है',
  'Work has been formally marked as Delayed': 'कार्य औपचारिक रूप से विलंबित घोषित है',
  'Work is suspended': 'कार्य रोका गया है',
  'Expenditure is materially ahead of physical progress':
    'व्यय भौतिक प्रगति से काफ़ी आगे है',
  'Sanctioned funds remain largely unspent late in the project window':
    'अवधि के अंतिम चरण में स्वीकृत निधि बड़े पैमाने पर अव्ययित है',
  'Expenditure has exceeded the sanctioned amount': 'व्यय स्वीकृत राशि से अधिक हो गया है',
  'No progress has been reported for an extended period':
    'लंबे समय से कोई प्रगति दर्ज नहीं की गई',
  'No expenditure recorded despite the work having commenced':
    'कार्य आरंभ होने के बावजूद कोई व्यय दर्ज नहीं',
  'Work certified complete with a large unspent balance':
    'कार्य पूर्ण प्रमाणित, किंतु बड़ी राशि अव्ययित',
  'Completion status conflicts with the recorded physical progress':
    'पूर्णता स्थिति दर्ज भौतिक प्रगति से मेल नहीं खाती',
  'Mandatory monitoring fields are missing from the record':
    'अभिलेख में अनिवार्य निगरानी फ़ील्ड अनुपस्थित हैं',
  'Multiple unresolved citizen reports against this work':
    'इस कार्य पर अनेक अनसुलझी नागरिक शिकायतें',
  'Description closely matches another sanctioned work in the same district':
    'विवरण उसी ज़िले के अन्य स्वीकृत कार्य से काफ़ी मिलता-जुलता है',
  'Sanctioned amount is a statistical outlier for this category':
    'इस श्रेणी के लिए स्वीकृत राशि सांख्यिकीय रूप से असामान्य है',
  'Cost per beneficiary is far above the category norm':
    'प्रति लाभार्थी लागत श्रेणी के मानक से कहीं अधिक है',
  'Record is a statistical outlier across several measures at once':
    'अभिलेख एक साथ कई मापों पर सांख्यिकीय रूप से असामान्य है',
}

/**
 * Bucket labels produced by the analytics service. Ranges like "20-40%" are
 * digits and need no translation; only the worded bucket does.
 */
export const BUCKET_HI: EnumMap = {
  'Over 100%': '100% से अधिक',
}
