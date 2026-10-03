"""tag_kbli_priority.py — Override mapping tag OSM -> KBLI untuk tag populer.

Aturan: kalau tag ada di sini, JANGAN pakai kbli_osm_mapping.json.
Pakai KBLI di sini — sudah diverifikasi manual.
"""

PRIORITY = {
    # ==== KESEHATAN ====
    "amenity=pharmacy":           "4772",   # Perdagangan Eceran Obat
    "shop=chemist":                "4772",
    "amenity=clinic":              "8620",   # Praktik Dokter
    "amenity=doctors":             "8620",
    "amenity=hospital":            "8610",   # Rumah Sakit
    "amenity=dentist":             "8620",
    "amenity=veterinary":          "7500",   # Kesehatan Hewan
    
    # ==== MAKANAN & MINUMAN ====
    "amenity=restaurant":          "5610",
    "amenity=fast_food":           "5610",
    "amenity=food_court":          "5610",
    "amenity=cafe":                "5630",
    "amenity=bar":                 "5630",
    "amenity=pub":                 "5630",
    "amenity=biergarten":          "5630",
    "amenity=ice_cream":           "5610",
    "shop=coffee":                 "5630",
    "shop=tea":                    "5630",
    "shop=juice":                  "5630",
    "shop=beverages":              "4722",   # Eceran Minuman
    "shop=alcohol":                "4722",
    "shop=wine":                   "4722",
    
    # ==== BAKERY & KUE ====
    "shop=bakery":                 "4724",   # Eceran Roti & Kue
    "shop=pastry":                 "4724",
    "shop=confectionery":          "4724",
    "craft=bakery":                "4724",
    
    # ==== RETAIL UMUM ====
    "shop=convenience":            "4711",   # Eceran Makanan/Minuman/Tembakau
    "shop=supermarket":            "4711",
    "shop=greengrocer":            "4721",   # Eceran Hasil Pertanian
    "shop=butcher":                "4721",
    "shop=seafood":                "4721",
    "shop=farm":                   "4721",
    "shop=cheese":                 "4724",
    "shop=deli":                   "4724",
    "shop=department_store":       "4719",   # Eceran Berbagai Macam Barang
    "shop=variety_store":          "4719",
    "shop=mall":                   "4719",
    "shop=clothes":                "4771",   # Eceran Pakaian
    "shop=shoes":                  "4772",
    "shop=bag":                    "4771",
    "shop=jewelry":                "4773",
    "shop=electronics":            "4741",
    "shop=computer":               "4741",
    "shop=mobile_phone":           "4742",
    "shop=furniture":              "4752",
    "shop=doityourself":           "4752",
    "shop=hardware":               "4752",
    "shop=books":                  "4761",
    "shop=stationery":             "4761",
    "shop=toys":                   "4764",
    "shop=cosmetics":              "4775",
    "shop=beauty":                 "4775",
    "shop=optician":               "4774",
    "shop=herbalist":              "4774",
    "shop=florist":                "4776",
    "shop=pet":                    "4776",
    "shop=motorcycle":             "4540",
    "shop=car":                    "4510",
    "shop=car_repair":             "4520",
    "shop=car_parts":              "4530",
    "shop=motorcycle_repair":      "4540",
    "shop=tyres":                  "4530",
    "shop=repair":                 "4520",
    "shop=copyshop":               "8219",
    "shop=laundry":                "9620",
    "shop=hairdresser":            "9611",   # Pangkas Rambut & Salon
    "shop=massage":                "9612",   # Kebugaran & Pijat
    "shop=photo":                  "7420",
    "shop=travel_agency":          "7911",
    "shop=rental":                 "7710",
    
    # ==== FUEL ====
    "amenity=fuel":                "4730",   # Eceran Bahan Bakar
    
    # ==== JASA KESEHATAN & KEBUGARAN ====
    "leisure=spa":                 "9612",
    "leisure=fitness_centre":      "9311",
    "leisure=sports_centre":       "9311",
    "leisure=swimming_pool":       "9311",
    "leisure=pitch":               "9311",
    "leisure=stadium":             "9311",
    "leisure=playground":          "9329",
    
    # ==== PENDIDIKAN ====
    "amenity=school":              "8511",
    "amenity=kindergarten":        "8513",
    "amenity=university":          "8531",
    "amenity=college":             "8532",
    "amenity=library":             "9101",
    
    # ==== HIBURAN ====
    "amenity=nightclub":           "9329",
    "amenity=karaoke_box":         "9329",
    "amenity=cinema":              "5914",
    "amenity=theatre":             "9001",
    "amenity=arts_centre":         "9001",
    "tourism=theme_park":          "9321",
    "tourism=museum":              "9102",
    
    # ==== AKOMODASI ====
    "tourism=hotel":               "5511",
    "tourism=motel":               "5511",
    "tourism=hostel":              "5512",
    "tourism=guest_house":         "5512",
    "tourism=apartment":           "5519",
    
    # ==== PEMERINTAHAN ====
    "office=government":           "8411",
    "amenity=police":              "8412",
    "amenity=fire_station":        "8423",
    "amenity=post_office":         "5310",
    "amenity=courthouse":          "8412",
    "amenity=townhall":            "8411",
    
    # ==== KEUANGAN ====
    "amenity=bank":                "6411",
    "amenity=atm":                 "6411",
    "office=financial":            "6419",
    "office=insurance":            "6512",
    
    # ==== TEMPAT IBADAH ====
    "amenity=place_of_worship":    "9491",
    
    # ==== PROFESIONAL ====
    "office=company":              "7010",
    "office=it":                   "6210",
    "office=lawyer":               "6910",
    "office=accountant":           "6920",
    "office=architect":            "7110",
    "office=engineer":             "7110",
    "office=advertising_agency":   "7310",
    "office=estate_agent":         "6811",
    "office=employment_agency":    "7810",
    "office=security":             "8010",
    "office=educational_institution": "8549",
    "office=association":          "9411",
    "office=research":             "7210",
    "office=telecommunication":    "6110",
    "office=media":                "6020",
    "office=publisher":            "5810",
    "office=diplomatic":           "9900",
    "office=administrative":       "8411",
    "office=international_organization": "9900",
    
    # ==== PERTANIAN ====
    "landuse=farmland":            "0111",
    "landuse=farmyard":            "0141",
    "landuse=orchard":             "0121",
    "landuse=forest":              "0211",
    "landuse=aquaculture":         "0311",
    "landuse=quarry":              "0810",
    "landuse=industrial":          "1071",
    "landuse=construction":        "4100",
    "landuse=landfill":            "3821",
    "landuse=saltern":             "1077",
    
    # ==== TRANSPORTASI ====
    "amenity=bus_station":         "4921",
    "amenity=taxi":                "4922",
    "amenity=ferry_terminal":      "5011",
    "aeroway=aerodrome":           "5110",
    "railway=station":             "4911",
    "amenity=parking":             "5210",
    "amenity=warehouse":           "5210",
    "harbour=yes":                 "5011",
    
    # ==== UTILITAS ====
    "man_made=water_works":        "3600",
    "man_made=wastewater_plant":   "3700",
    "power=plant":                 "3510",
    "amenity=recycling":           "3830",
    
    # ==== OTHER ====
    "amenity=marketplace":         "4781",
    "amenity=social_facility":     "8710",
    "amenity=community_centre":    "9329",
    "amenity=place_of_mourning":   "9603",
    "amenity=archive":             "9101",
    "craft=caterer":               "5621",
    "craft=carpenter":             "1622",
    "craft=photographer":          "7420",
    "craft=jeweller":              "3212",
    "craft=musical_instrument":    "3221",
    "craft=shoemaker":             "1520",
    "craft=tailor":                "1412",
    "industrial=food":             "1071",
    "industrial=beverage":         "1101",
    "industrial=textile":          "1311",
    "industrial=wood":             "1610",
    "industrial=leather":          "1511",
    "industrial=tobacco":          "1201",
    "industrial=paper":            "1701",
    "industrial=printing":         "1811",
    "industrial=chemical":         "2011",
    "industrial=pharmaceutical":   "2101",
    "industrial=plastic":          "2220",
    "industrial=mineral":          "2310",
    "industrial=metal":            "2410",
    "industrial=electronics":      "2610",
    "industrial=machine":          "2810",
    "industrial=vehicle":          "2910",
    "industrial=furniture":        "3101",
    "industrial=mining":           "0510",
    "industrial=oil":              "1921",
    "industrial=warehouse":        "5210",
    "industrial=toys":             "3240",
    "industrial=sports_equipment": "3230",
    "industrial=medical_equipment":"3250",
    "industrial=dairy":            "1051",
    "industrial=cement":           "2391",
    "industrial=glass":            "2310",
    "industrial=ceramic":          "2392",
    "industrial=clothes":          "1411",
    "industrial=shoe":             "1520",
    "industrial=metal":            "2410",
    "product=fish":                "1021",
    "product=seafood":             "1021",
    "product=fruit":               "1031",
    "product=juice":               "1033",
    "product=oil":                 "1041",
    "product=ice_cream":           "1053",
    "product=flour":               "1061",
    "product=rice":                "1062",
    "product=sugar":               "1072",
    "product=chocolate":           "1073",
    "product=pasta":               "1074",
    "product=tea":                 "1076",
    "product=coffee":              "1076",
    "product=spice":               "1077",
}