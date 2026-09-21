"""Reference lists used to generate the realistic synthetic dataset.

Per SRS 2.4, real MPLAD data is not available for the hackathon, so a
realistic synthetic dataset with deliberately injected anomalies is used.
Names of Members of Parliament below are fictional.
"""
from __future__ import annotations

STATES = {
    "Maharashtra": [
        ("Pune", "Pune"),
        ("Nagpur", "Nagpur"),
        ("Nashik", "Nashik"),
        ("Aurangabad", "Aurangabad"),
        ("Solapur", "Solapur"),
        ("Kolhapur", "Kolhapur"),
    ],
    "Uttar Pradesh": [
        ("Lucknow", "Lucknow"),
        ("Varanasi", "Varanasi"),
        ("Kanpur Nagar", "Kanpur"),
        ("Gorakhpur", "Gorakhpur"),
        ("Prayagraj", "Phulpur"),
        ("Meerut", "Meerut"),
    ],
    "Karnataka": [
        ("Bengaluru Urban", "Bangalore North"),
        ("Mysuru", "Mysore"),
        ("Belagavi", "Belgaum"),
        ("Kalaburagi", "Gulbarga"),
        ("Dharwad", "Dharwad"),
    ],
    "Tamil Nadu": [
        ("Chennai", "Chennai South"),
        ("Coimbatore", "Coimbatore"),
        ("Madurai", "Madurai"),
        ("Tiruchirappalli", "Tiruchirappalli"),
        ("Salem", "Salem"),
    ],
    "West Bengal": [
        ("Kolkata", "Kolkata Dakshin"),
        ("Howrah", "Howrah"),
        ("Darjeeling", "Darjeeling"),
        ("Murshidabad", "Murshidabad"),
    ],
    "Rajasthan": [
        ("Jaipur", "Jaipur Rural"),
        ("Jodhpur", "Jodhpur"),
        ("Udaipur", "Udaipur"),
        ("Kota", "Kota"),
    ],
    "Bihar": [
        ("Patna", "Patna Sahib"),
        ("Gaya", "Gaya"),
        ("Muzaffarpur", "Muzaffarpur"),
        ("Bhagalpur", "Bhagalpur"),
    ],
    "Gujarat": [
        ("Ahmedabad", "Ahmedabad East"),
        ("Surat", "Surat"),
        ("Rajkot", "Rajkot"),
        ("Vadodara", "Vadodara"),
    ],
    "Madhya Pradesh": [
        ("Bhopal", "Bhopal"),
        ("Indore", "Indore"),
        ("Jabalpur", "Jabalpur"),
        ("Gwalior", "Gwalior"),
    ],
    "Kerala": [
        ("Thiruvananthapuram", "Thiruvananthapuram"),
        ("Ernakulam", "Ernakulam"),
        ("Kozhikode", "Kozhikode"),
    ],
    "Odisha": [("Khordha", "Bhubaneswar"), ("Cuttack", "Cuttack"), ("Ganjam", "Berhampur")],
    "Punjab": [("Ludhiana", "Ludhiana"), ("Amritsar", "Amritsar"), ("Jalandhar", "Jalandhar")],
    "Assam": [("Kamrup Metropolitan", "Gauhati"), ("Dibrugarh", "Dibrugarh")],
    "Telangana": [("Hyderabad", "Secunderabad"), ("Warangal", "Warangal")],
    "Haryana": [("Gurugram", "Gurgaon"), ("Faridabad", "Faridabad"), ("Hisar", "Hisar")],
}

# Fictional MP names, one per constituency, assigned deterministically.
MP_FIRST = [
    "Anil", "Sunita", "Rajesh", "Meera", "Vikram", "Kavita", "Sanjay", "Priya",
    "Ramesh", "Anjali", "Deepak", "Lata", "Mohan", "Rekha", "Arun", "Shalini",
    "Prakash", "Nandini", "Harish", "Geeta", "Suresh", "Asha", "Naveen", "Bhavna",
    "Kiran", "Manoj", "Pooja", "Rahul", "Sneha", "Vijay", "Usha", "Yogesh",
    "Divya", "Gopal", "Indira", "Jayant", "Kamala", "Lalit", "Madhuri", "Nitin",
    "Omkar", "Padma", "Ravi", "Seema", "Tarun", "Uma", "Varun", "Waseem",
]
MP_LAST = [
    "Deshmukh", "Sharma", "Iyer", "Banerjee", "Patel", "Reddy", "Nair", "Chauhan",
    "Yadav", "Joshi", "Menon", "Rathore", "Kulkarni", "Mishra", "Pillai", "Gowda",
    "Sen", "Bhatia", "Naidu", "Thakur", "Das", "Kaur", "Mukherjee", "Saxena",
]

CATEGORIES = [
    "Drinking Water Facility",
    "Education - School Buildings",
    "Health & Family Welfare",
    "Roads, Pathways and Bridges",
    "Sanitation and Public Health",
    "Community Halls",
    "Electricity Facility - Street Lighting",
    "Sports and Recreation",
    "Public Libraries",
    "Irrigation Facility",
    "Railway Facilities",
    "Higher Education Facility",
    "Anganwadi and Child Care",
    "Solar and Non-conventional Energy",
    "Veterinary and Animal Husbandry",
    "Rainwater Harvesting",
    "Bus Shelters and Public Transport",
    "Cremation and Burial Grounds",
    "Skill Development Centres",
    "Disability Welfare Facilities",
]

AGENCIES = [
    "Public Works Department (PWD)",
    "Zilla Parishad Engineering Wing",
    "Municipal Corporation Works Division",
    "Rural Development Engineering Department",
    "Jal Jeevan Mission District Unit",
    "State Education Infrastructure Board",
    "District Health Society",
    "State Electricity Distribution Company",
    "Panchayati Raj Engineering Department",
    "State Sports Authority - District Wing",
    "Irrigation Department - Division Office",
    "District Rural Roads Agency",
]

CONTRACTORS = [
    "Shree Construction Co.",
    "Prabhat Infrastructure Pvt Ltd",
    "Konark Builders",
    "Ganga Engineering Works",
    "Sahyadri Constructions",
    "Vindhya Civil Projects",
    "Nalanda Infratech",
    "Coastal Engineering Services",
    "Deccan Works & Supplies",
    "Himalaya Civil Contractors",
    "Departmental Execution (no contractor)",
]

# Category -> (title template, description template) pairs.
WORK_TEMPLATES = {
    "Drinking Water Facility": [
        (
            "Construction of overhead water tank at {place}",
            "Construction of a {capacity} litre reinforced-cement-concrete overhead water "
            "tank with distribution pipeline at {place}, {block} block, to provide piped "
            "drinking water to approximately {ben} residents.",
        ),
        (
            "Installation of community borewell and pump house at {place}",
            "Sinking of a deep borewell with submersible pump and construction of a pump "
            "house at {place}, {block} block, including electrical connection and "
            "distribution standposts.",
        ),
    ],
    "Education - School Buildings": [
        (
            "Construction of additional classrooms at Government School, {place}",
            "Construction of {rooms} additional classrooms with flooring, electrification "
            "and furniture at the Government Higher Primary School, {place}, {block} block.",
        ),
        (
            "Construction of compound wall and toilet block at school, {place}",
            "Construction of a compound wall of {length} running metres and a two-unit "
            "toilet block with water connection at the government school in {place}.",
        ),
    ],
    "Health & Family Welfare": [
        (
            "Construction of waiting hall at Primary Health Centre, {place}",
            "Construction of a covered patient waiting hall with seating, fans and "
            "drinking water facility at the Primary Health Centre, {place}, {block} block.",
        ),
        (
            "Supply of medical equipment to Community Health Centre, {place}",
            "Supply and installation of diagnostic and patient-care equipment at the "
            "Community Health Centre, {place}, benefiting approximately {ben} patients "
            "annually.",
        ),
    ],
    "Roads, Pathways and Bridges": [
        (
            "Construction of concrete road from {place} to {block} link road",
            "Construction of a cement-concrete village road of {length} running metres "
            "with side drains connecting {place} to the {block} link road.",
        ),
        (
            "Construction of culvert and approach road at {place}",
            "Construction of a box culvert with approach roads on either side at {place}, "
            "{block} block, to restore connectivity during the monsoon.",
        ),
    ],
    "Sanitation and Public Health": [
        (
            "Construction of community sanitation complex at {place}",
            "Construction of a community sanitation complex with {rooms} units, septic "
            "tank and water connection at {place}, {block} block.",
        ),
        (
            "Construction of covered drainage at {place}",
            "Construction of {length} running metres of covered RCC drainage along the "
            "main street at {place} to prevent waterlogging.",
        ),
    ],
    "Community Halls": [
        (
            "Construction of community hall at {place}",
            "Construction of a community hall of approximately {area} square metres with "
            "flooring, electrification and toilet facility at {place}, {block} block.",
        ),
    ],
    "Electricity Facility - Street Lighting": [
        (
            "Installation of LED street lights at {place}",
            "Supply and installation of {rooms} LED street light fittings with poles and "
            "wiring along the main approach road at {place}, {block} block.",
        ),
    ],
    "Sports and Recreation": [
        (
            "Development of playground at {place}",
            "Levelling, fencing and development of a playground with a jogging track at "
            "{place}, {block} block, for use by local schools and youth clubs.",
        ),
    ],
    "Public Libraries": [
        (
            "Construction of public library building at {place}",
            "Construction of a public library building of approximately {area} square "
            "metres with reading hall, book racks and furniture at {place}.",
        ),
    ],
    "Irrigation Facility": [
        (
            "Renovation of irrigation tank at {place}",
            "Desilting, bund strengthening and sluice repair of the irrigation tank at "
            "{place}, {block} block, serving approximately {ben} hectares of command area.",
        ),
    ],
    "Railway Facilities": [
        (
            "Construction of passenger shed at {place} railway station",
            "Construction of a covered passenger waiting shed with seating and drinking "
            "water facility on platform at {place} railway station.",
        ),
    ],
    "Higher Education Facility": [
        (
            "Construction of computer laboratory at Government College, {place}",
            "Construction and furnishing of a computer laboratory with networking and "
            "power backup at the Government Degree College, {place}.",
        ),
    ],
    "Anganwadi and Child Care": [
        (
            "Construction of Anganwadi centre building at {place}",
            "Construction of an Anganwadi centre with kitchen, store and child-friendly "
            "toilet at {place}, {block} block.",
        ),
    ],
    "Solar and Non-conventional Energy": [
        (
            "Installation of solar street lighting system at {place}",
            "Supply and installation of {rooms} standalone solar street lighting units "
            "with LED fittings and battery backup at {place}.",
        ),
    ],
    "Veterinary and Animal Husbandry": [
        (
            "Construction of veterinary dispensary building at {place}",
            "Construction of a veterinary dispensary with examination room and medicine "
            "store at {place}, {block} block.",
        ),
    ],
    "Rainwater Harvesting": [
        (
            "Rainwater harvesting structures at government buildings, {place}",
            "Construction of rooftop rainwater harvesting structures with recharge pits "
            "at government buildings in {place}, {block} block.",
        ),
    ],
    "Bus Shelters and Public Transport": [
        (
            "Construction of bus shelters at {place}",
            "Construction of {rooms} passenger bus shelters with seating and lighting "
            "along the state highway at {place}.",
        ),
    ],
    "Cremation and Burial Grounds": [
        (
            "Development of cremation ground shed at {place}",
            "Construction of a covered shed, approach path and boundary wall at the "
            "cremation ground in {place}, {block} block.",
        ),
    ],
    "Skill Development Centres": [
        (
            "Construction of skill development centre at {place}",
            "Construction and equipping of a skill development centre with two training "
            "halls at {place}, benefiting approximately {ben} trainees annually.",
        ),
    ],
    "Disability Welfare Facilities": [
        (
            "Construction of ramps and accessible toilets at public buildings, {place}",
            "Construction of accessibility ramps with handrails and accessible toilets at "
            "government buildings in {place}, {block} block.",
        ),
    ],
}

PLACES = [
    "Shivajinagar", "Ramnagar", "Gandhi Chowk", "Nehru Colony", "Bhagat Singh Ward",
    "Subhash Nagar", "Indira Nagar", "Vivekananda Ward", "Ambedkar Nagar", "Tilak Ward",
    "Patel Nagar", "Sardar Colony", "Vidyanagar", "Krishnapuram", "Laxminagar",
    "Govindpur", "Mahatma Ward", "Sarojini Nagar", "Rajendra Nagar", "Bose Colony",
    "Chandranagar", "Devipuram", "Hariharpur", "Jankipuram", "Kalyanpur",
    "Madhavpura", "Narsinghpur", "Panchvati", "Raghunathpur", "Sundarnagar",
]

BLOCKS = [
    "North", "South", "East", "West", "Central", "Rural-I", "Rural-II",
    "Urban-I", "Urban-II", "Sadar", "Kasba", "Taluka",
]

MILESTONES = [
    "Administrative approval issued",
    "Tender awarded",
    "Site handed over",
    "Foundation completed",
    "Structure work in progress",
    "Roofing completed",
    "Finishing work in progress",
    "Electrical and plumbing completed",
    "Work completed, inspection pending",
    "Completion certificate issued",
]


# ---------------------------------------------------------------------------
# District coordinates
#
# Approximate position of each district headquarters, in decimal degrees.
# The seed places a work by jittering around its own district's point, so a
# work in Sirohi appears in Sirohi. Generating a random point inside a
# bounding box of India - which is what this used to do - put markers in
# Pakistan, Nepal, China and the Bay of Bengal.
#
# These are headquarters coordinates, not district centroids, which is the
# right level of precision for a demonstration dataset: close enough that the
# map reads correctly, and never presented as a surveyed location.
# ---------------------------------------------------------------------------
DISTRICT_COORDINATES = {
    # Maharashtra
    "Pune": (18.5204, 73.8567),
    "Nagpur": (21.1458, 79.0882),
    "Nashik": (19.9975, 73.7898),
    "Aurangabad": (19.8762, 75.3433),
    "Solapur": (17.6599, 75.9064),
    "Kolhapur": (16.7050, 74.2433),
    # Uttar Pradesh
    "Lucknow": (26.8467, 80.9462),
    "Varanasi": (25.3176, 82.9739),
    "Kanpur Nagar": (26.4499, 80.3319),
    "Gorakhpur": (26.7606, 83.3732),
    "Prayagraj": (25.4358, 81.8463),
    "Meerut": (28.9845, 77.7064),
    # Karnataka
    "Bengaluru Urban": (12.9716, 77.5946),
    "Mysuru": (12.2958, 76.6394),
    "Belagavi": (15.8497, 74.4977),
    "Kalaburagi": (17.3297, 76.8343),
    "Dharwad": (15.4589, 75.0078),
    # Tamil Nadu
    "Chennai": (13.0827, 80.2707),
    "Coimbatore": (11.0168, 76.9558),
    "Madurai": (9.9252, 78.1198),
    "Tiruchirappalli": (10.7905, 78.7047),
    "Salem": (11.6643, 78.1460),
    # West Bengal
    "Kolkata": (22.5726, 88.3639),
    "Howrah": (22.5958, 88.2636),
    "Darjeeling": (27.0360, 88.2627),
    "Murshidabad": (24.1751, 88.2800),
    # Rajasthan
    "Jaipur": (26.9124, 75.7873),
    "Jodhpur": (26.2389, 73.0243),
    "Udaipur": (24.5854, 73.7125),
    "Kota": (25.2138, 75.8648),
    "Sirohi": (24.8853, 72.8619),
    # Bihar
    "Patna": (25.5941, 85.1376),
    "Gaya": (24.7914, 85.0002),
    "Muzaffarpur": (26.1209, 85.3647),
    "Bhagalpur": (25.2425, 86.9842),
    # Gujarat
    "Ahmedabad": (23.0225, 72.5714),
    "Surat": (21.1702, 72.8311),
    "Rajkot": (22.3039, 70.8022),
    "Vadodara": (22.3072, 73.1812),
    # Madhya Pradesh
    "Bhopal": (23.2599, 77.4126),
    "Indore": (22.7196, 75.8577),
    "Jabalpur": (23.1815, 79.9864),
    "Gwalior": (26.2183, 78.1828),
    # Kerala
    "Thiruvananthapuram": (8.5241, 76.9366),
    "Ernakulam": (9.9816, 76.2999),
    "Kozhikode": (11.2588, 75.7804),
    # Odisha
    "Khordha": (20.1301, 85.6967),
    "Cuttack": (20.4625, 85.8830),
    "Ganjam": (19.3860, 84.7941),
    # Punjab
    "Ludhiana": (30.9010, 75.8573),
    "Amritsar": (31.6340, 74.8723),
    "Jalandhar": (31.3260, 75.5762),
    # Assam
    "Kamrup Metropolitan": (26.1445, 91.7362),
    "Dibrugarh": (27.4728, 94.9120),
    # Telangana
    "Hyderabad": (17.3850, 78.4867),
    "Warangal": (17.9689, 79.5941),
    # Haryana
    "Gurugram": (28.4595, 77.0266),
    "Faridabad": (28.4089, 77.3178),
    "Hisar": (29.1492, 75.7217),
}

#: Works are spread around the district headquarters by up to this many
#: degrees (~20 km), so markers do not stack on a single point while staying
#: inside the district.
COORDINATE_JITTER_DEGREES = 0.18
