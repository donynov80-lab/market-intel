"""
kbli_osm_rules.py — v3
Aturan pattern: SUBSTRING di title KBLI -> OSM tags.

Perbaikan v3:
  - Pertanian (tanam) dipisah dari Retail (jual)
  - Peternakan (ternak) dipisah dari Pet Shop (jual)
  - Penangkapan ikan dipisah dari Seafood Shop
  - Tambahan KBLI tanpa mapping (padi, tambang, dll.)
"""

RULES = [
    # ===== MAKANAN & MINUMAN (INDUSTRI) =====
    (["roti dan kue", "produk roti"], ["shop=bakery", "craft=bakery", "shop=pastry"]),
    (["makanan dan masakan olahan"], ["landuse=industrial", "industrial=food"]),
    (["pengolahan kopi", "teh dan herbal"], ["landuse=industrial", "industrial=food"]),
    (["makanan lainnya"], ["landuse=industrial", "industrial=food"]),
    (["makanan hewan"], ["landuse=industrial", "industrial=food", "shop=pet"]),
    (["minuman beralkohol"], ["landuse=industrial", "industrial=beverage"]),
    (["minuman ringan", "minuman lainnya"], ["landuse=industrial", "industrial=beverage"]),
    (["mesin pengolahan makanan"], ["landuse=industrial", "industrial=machine"]),
    (["pengolahan biota air", "industri kopra", "minyak goreng"], ["landuse=industrial", "industrial=food"]),
        # ===== INDUSTRI PENGOLAHAN PANGAN (untuk supply chain) =====
    (["pengolahan dan pengawetan ikan"], ["landuse=industrial", "industrial=food", "product=fish"]),
    (["pengolahan dan pengawetan biota air"], ["landuse=industrial", "industrial=food", "product=seafood"]),
    (["pengolahan dan pengawetan buah"], ["landuse=industrial", "industrial=food", "product=fruit"]),
    (["pengolahan sari buah"], ["landuse=industrial", "industrial=food", "product=juice"]),
    (["minyak dan lemak nabati", "minyak mentah dan lemak nabati"], ["landuse=industrial", "industrial=food", "product=oil"]),
    (["pengolahan susu segar", "susu bubuk", "susu kental"], ["landuse=industrial", "industrial=dairy"]),
    (["es krim"], ["landuse=industrial", "industrial=food", "product=ice_cream"]),
    (["pengolahan produk dari susu"], ["landuse=industrial", "industrial=dairy"]),
    (["penggilingan serelia", "penggilingan biji"], ["landuse=industrial", "industrial=food", "product=flour"]),
    (["penggilingan padi"], ["landuse=industrial", "industrial=food", "product=rice"]),
    (["industri tepung"], ["landuse=industrial", "industrial=food", "product=flour"]),
    (["industri gula"], ["landuse=industrial", "industrial=food", "product=sugar"]),
    (["industri kakao", "cokelat"], ["landuse=industrial", "industrial=food", "product=chocolate"]),
    (["industri makanan dari susu"], ["landuse=industrial", "industrial=dairy"]),
    (["industri mie", "industri makaroni"], ["landuse=industrial", "industrial=food", "product=pasta"]),
    (["industri pengolahan teh"], ["landuse=industrial", "industrial=beverage", "product=tea"]),
    (["industri pengolahan kopi"], ["landuse=industrial", "industrial=beverage", "product=coffee"]),
    (["industri bumbu", "industri rempah"], ["landuse=industrial", "industrial=food", "product=spice"]),
    (["industri makanan bayi"], ["landuse=industrial", "industrial=food"]),
    (["industri makanan diet"], ["landuse=industrial", "industrial=food"]),

    # ===== RESTORAN & CAFE =====
    (["restoran", "rumah makan", "penyediaan makanan"], ["amenity=restaurant", "amenity=fast_food"]),
    (["penyediaan minuman"], ["amenity=cafe", "amenity=bar", "amenity=pub", "shop=coffee"]),
    (["jasa boga", "katering"], ["craft=caterer"]),

    # ===== RETAIL MAKANAN/MINUMAN =====
    (["makanan minuman atau tembakau di toko"], ["shop=convenience", "shop=supermarket"]),
    (["makanan hasil industri di toko"], ["shop=bakery", "shop=pastry", "shop=confectionery"]),
    (["minuman di toko"], ["shop=beverages", "shop=alcohol"]),
    (["makanan dari hasil pertanian"], ["shop=greengrocer", "shop=farm"]),
    (["kaki lima", "los pasar makanan"], ["amenity=fast_food", "amenity=marketplace"]),
    (["berbagai macam barang"], ["shop=department_store", "shop=variety_store"]),
    (["supermarket", "hipermarket"], ["shop=supermarket"]),
    (["minimarket", "kelontong"], ["shop=convenience"]),
    (["pasar"], ["amenity=marketplace"]),

    # ===== RETAIL LAINNYA =====
    (["apotek", "farmasi"], ["amenity=pharmacy", "shop=chemist"]),
    (["kosmetik"], ["shop=cosmetics", "shop=beauty"]),
    (["perdagangan pakaian", "toko pakaian"], ["shop=clothes"]),
    (["perdagangan sepatu", "toko sepatu"], ["shop=shoes"]),
    (["perdagangan tekstil", "toko kain"], ["shop=fabric"]),
    (["perdagangan perabot", "toko mebel"], ["shop=furniture"]),
    (["perdagangan elektronik"], ["shop=electronics", "shop=computer"]),
    (["telepon seluler"], ["shop=mobile_phone"]),
    (["perdagangan bahan bangunan", "toko bangunan"], ["shop=doityourself", "shop=hardware"]),
    (["perdagangan buku", "toko buku"], ["shop=books", "shop=stationery"]),
    (["mainan"], ["shop=toys"]),
    (["perhiasan", "emas"], ["shop=jewelry"]),
    (["obat tradisional", "jamu"], ["shop=herbalist"]),
    (["bahan bakar", "bbm"], ["amenity=fuel"]),
    (["daging", "butcher"], ["shop=butcher"]),
    (["penjual ikan", "toko ikan", "seafood"], ["shop=seafood"]),
    (["perdagangan buah", "toko buah", "perdagangan eceran buah"], ["shop=greengrocer"]),
    (["perdagangan sayur", "toko sayur", "perdagangan eceran sayur"], ["shop=greengrocer"]),
    (["toko hewan", "pet shop"], ["shop=pet"]),
    (["bunga"], ["shop=florist"]),
    (["optik", "kacamata"], ["shop=optician"]),

    # ===== INDUSTRI & PABRIK =====
    (["industri makanan"], ["landuse=industrial", "industrial=food"]),
    (["industri minuman"], ["landuse=industrial", "industrial=beverage"]),
    (["industri tembakau"], ["landuse=industrial", "industrial=tobacco"]),
    (["industri tekstil"], ["landuse=industrial", "industrial=textile"]),
    (["industri pakaian"], ["landuse=industrial", "industrial=clothes"]),
    (["industri kulit"], ["landuse=industrial", "industrial=shoe"]),
    (["industri kayu"], ["landuse=industrial", "industrial=wood"]),
    (["industri kertas"], ["landuse=industrial", "industrial=paper"]),
    (["industri pencetakan"], ["landuse=industrial", "industrial=printing"]),
    (["pengilangan minyak", "batu bara"], ["landuse=industrial", "industrial=oil"]),
    (["industri bahan kimia"], ["landuse=industrial", "industrial=chemical"]),
    (["industri farmasi"], ["landuse=industrial", "industrial=pharmaceutical"]),
    (["industri karet", "plastik"], ["landuse=industrial", "industrial=plastic"]),
    (["barang galian bukan logam"], ["landuse=industrial", "industrial=mineral"]),
    (["industri logam dasar"], ["landuse=industrial", "industrial=metal"]),
    (["barang logam"], ["landuse=industrial", "industrial=metal"]),
    (["industri komputer", "barang elektronik"], ["landuse=industrial", "industrial=electronics"]),
    (["peralatan listrik"], ["landuse=industrial", "industrial=electronics"]),
    (["industri mesin"], ["landuse=industrial", "industrial=machine"]),
    (["kendaraan bermotor", "trailer"], ["landuse=industrial", "industrial=vehicle"]),
    (["alat angkutan lainnya"], ["landuse=industrial", "industrial=vehicle"]),
    (["industri furnitur"], ["landuse=industrial", "industrial=furniture"]),
    (["pengolahan lainnya"], ["landuse=industrial"]),
    (["reparasi dan pemasangan mesin"], ["landuse=industrial", "industrial=machine", "shop=repair"]),

    # ===== PERTANIAN (TANAM) — bukan retail =====
    (["pertanian ", "perkebunan "], ["landuse=farmland", "landuse=orchard"]),
    (["pertanian serealia", "pertanian padi"], ["landuse=farmland"]),
    (["pertanian tanaman hias"], ["landuse=farmland", "shop=garden_centre"]),
    (["jasa penunjang pertanian", "jasa pasca panen"], ["office=company"]),
    (["pemilihan benih", "perbenihan tanaman"], ["shop=garden_centre"]),
    (["kehutanan", "penebangan", "pemanenan dan pemungutan kayu"], ["landuse=forest"]),
    (["jasa penunjang kehutanan"], ["office=company"]),
    (["perburuan", "penangkapan satwa"], ["landuse=forest"]),
    (["penangkaran tumbuhan"], ["landuse=forest"]),
        (["pemanfaatan hutan tanaman", "pemanfaatan hutan alam"], ["landuse=forest"]),
    (["pemanfaatan hasil hutan"], ["landuse=forest"]),
    (["pemungutan hasil hutan"], ["landuse=forest"]),
    (["penangkapan jenis ikan yang dilindungi"], ["office=government"]),
    (["pengembangbiakan jenis ikan"], ["landuse=aquaculture"]),

    # ===== PETERNAKAN & PERIKANAN =====
    (["peternakan", "ternak "], ["landuse=farmyard"]),
    (["jasa penunjang peternakan"], ["office=company"]),
    (["penangkapan ikan", "budidaya ikan", "tambak"], ["landuse=aquaculture"]),
    (["jasa penangkapan ikan"], ["office=company"]),

    # ===== PERTAMBANGAN & PENGGALIAN =====
    (["pertambangan batu bara"], ["landuse=quarry", "industrial=mining"]),
    (["pertambangan lignit"], ["landuse=quarry", "industrial=mining"]),
    (["pertambangan minyak", "gas alam", "panas bumi"], ["landuse=industrial", "industrial=oil"]),
    (["pertambangan pasir", "pertambangan bijih", "pertambangan logam"], ["landuse=quarry", "industrial=mining"]),
    (["pertambangan dan penggalian"], ["landuse=quarry", "industrial=mining"]),
    (["penggalian batu", "penggalian pasir", "penggalian tanah"], ["landuse=quarry"]),
    (["ekstraksi garam"], ["landuse=saltern"]),
    (["ekstraksi tanah gemuk", "peat"], ["landuse=quarry"]),
    (["pertambangan mineral", "bahan pupuk"], ["landuse=quarry", "industrial=mining"]),
    (["jasa penunjang pertambangan"], ["office=company"]),

    # ===== INDUSTRI MANUFAKTUR LAINNYA (untuk supply chain B2B) =====
    # Tembakau (Madura, Temanggung, Kudus)
    (["industri rokok", "produk tembakau"], ["landuse=industrial", "industrial=tobacco"]),
    (["pengolahan tembakau"], ["landuse=industrial", "industrial=tobacco"]),
    (["industri pengeringan tembakau"], ["landuse=industrial", "industrial=tobacco"]),

    # Tekstil (Garut, Magetan, Solo, Bandung)
    (["pemintalan serat tekstil", "pertenunan tekstil"], ["landuse=industrial", "industrial=textile"]),
    (["penyempurnaan tekstil", "pewarnaan tekstil"], ["landuse=industrial", "industrial=textile"]),
    (["kain rajutan", "sulaman"], ["landuse=industrial", "industrial=textile"]),
    (["barang tekstil, bukan pakaian"], ["landuse=industrial", "industrial=textile"]),
    (["karpet dan permadani"], ["landuse=industrial", "industrial=textile"]),
    (["tali dan barang dari tali"], ["landuse=industrial", "industrial=textile"]),
    (["penjahitan", "pembuatan pakaian"], ["landuse=industrial", "industrial=clothes", "shop=tailor"]),
    (["perlengkapan pakaian"], ["landuse=industrial", "industrial=clothes"]),
    (["industri pakaian jadi"], ["landuse=industrial", "industrial=clothes"]),

    # Kulit & Alas Kaki (Garut, Yogyakarta, Sidoarjo)
    (["barang dari kulit", "koper", "tas"], ["landuse=industrial", "industrial=leather", "shop=bag"]),
    (["industri alas kaki"], ["landuse=industrial", "industrial=leather", "shop=shoes"]),
    (["penyamakan kulit"], ["landuse=industrial", "industrial=leather"]),

    # Kayu, Rotan, Bambu (Kalimantan, Sulawesi, Bali)
    (["penggergajian kayu", "pengawetan kayu"], ["landuse=industrial", "industrial=wood", "landuse=forest"]),
    (["veneer", "kayu lapis", "kayu laminasi"], ["landuse=industrial", "industrial=wood"]),
    (["barang bangunan dari kayu"], ["landuse=industrial", "industrial=wood"]),
    (["wadah dari kayu"], ["landuse=industrial", "industrial=wood"]),
    (["barang anyaman", "rotan", "bambu"], ["landuse=industrial", "industrial=wood", "shop=craft"]),
    (["industri kayu"], ["landuse=industrial", "industrial=wood"]),
    (["industri furnitur"], ["landuse=industrial", "industrial=furniture", "shop=furniture"]),

    # Kimia, Farmasi, Karet
    (["industri bahan kimia"], ["landuse=industrial", "industrial=chemical"]),
    (["industri farmasi", "produk obat"], ["landuse=industrial", "industrial=pharmaceutical"]),
    (["obat tradisional", "herbal"], ["landuse=industrial", "industrial=pharmaceutical"]),
    (["industri karet", "barang dari karet"], ["landuse=industrial", "industrial=plastic"]),
    (["industri plastik", "barang dari plastik"], ["landuse=industrial", "industrial=plastic"]),

    # Logam, Mesin, Elektronik
    (["industri logam dasar"], ["landuse=industrial", "industrial=metal"]),
    (["barang logam, bukan mesin"], ["landuse=industrial", "industrial=metal"]),
    (["industri komputer"], ["landuse=industrial", "industrial=electronics"]),
    (["barang elektronik", "komponen elektronik"], ["landuse=industrial", "industrial=electronics"]),
    (["peralatan listrik"], ["landuse=industrial", "industrial=electronics"]),
    (["industri mesin dan perlengkapan"], ["landuse=industrial", "industrial=machine"]),
    (["industri kendaraan bermotor"], ["landuse=industrial", "industrial=vehicle"]),
    (["industri alat angkutan"], ["landuse=industrial", "industrial=vehicle"]),

    # Kerajinan & Industri Kreatif
    (["industri kerajinan"], ["landuse=industrial", "shop=craft"]),
    (["industri perhiasan", "barang berharga"], ["landuse=industrial", "craft=jeweller"]),
    (["industri alat musik"], ["landuse=industrial", "craft=musical_instrument"]),
    (["industri mainan"], ["landuse=industrial", "industrial=toys"]),
    (["industri alat olahraga"], ["landuse=industrial", "industrial=sports_equipment"]),
    (["industri alat kedokteran"], ["landuse=industrial", "industrial=medical_equipment"]),

    # Kertas, Percetakan, Penerbitan
    (["industri kertas", "barang dari kertas"], ["landuse=industrial", "industrial=paper"]),
    (["industri pencetakan"], ["landuse=industrial", "industrial=printing", "shop=copyshop"]),
    (["reproduksi media rekaman"], ["landuse=industrial", "industrial=printing"]),
    (["industri furnitur kayu"], ["landuse=industrial", "industrial=furniture"]),

    # Pengolahan Air & Minuman Fermentasi
    (["industri malt"], ["landuse=industrial", "industrial=beverage"]),
    (["industri minuman fermentasi"], ["landuse=industrial", "industrial=beverage"]),

    # Industri Pengolahan Lainnya
    (["industri pengolahan lainnya"], ["landuse=industrial"]),
    (["industri barang galian bukan logam"], ["landuse=industrial", "industrial=mineral"]),
    (["industri semen", "kapur", "gipsum"], ["landuse=industrial", "industrial=cement"]),
    (["industri kaca", "barang dari kaca"], ["landuse=industrial", "industrial=glass"]),
    (["industri keramik", "porselen", "tanah liat"], ["landuse=industrial", "industrial=ceramic"]),

    # Reparasi & Pemasangan
    (["reparasi produk logam pabrikasi"], ["shop=repair", "industrial=metal"]),
    (["reparasi mesin"], ["shop=repair", "industrial=machine"]),
    (["reparasi peralatan elektronik"], ["shop=repair", "industrial=electronics"]),
    (["reparasi peralatan listrik"], ["shop=repair"]),
    (["reparasi alat angkutan"], ["shop=repair"]),
    (["pemasangan mesin dan peralatan"], ["shop=repair", "industrial=machine"]),

    # Percetakan & Fotokopi
    (["fotokopi", "penyiapan dokumen"], ["shop=copyshop"]),

    # ==== TAMBAHAN PETERNAKAN SPESIFIK ====
    (["peternakan sapi", "peternakan kerbau"], ["landuse=farmyard"]),
    (["peternakan kuda"], ["landuse=farmyard"]),
    (["peternakan domba", "peternakan kambing"], ["landuse=farmyard"]),
    (["peternakan babi"], ["landuse=farmyard"]),
    (["peternakan unggas", "peternakan ayam"], ["landuse=farmyard"]),
    (["budidaya udang", "budidaya tambak"], ["landuse=aquaculture"]),
    (["pembenihan ikan"], ["landuse=aquaculture"]),

    # ==== PERIKANAN TANGKAP (bukan retail) ====
    (["penangkapan ikan di laut"], ["harbour=yes", "landuse=industrial"]),
    (["penangkapan ikan di perairan darat"], ["landuse=aquaculture"]),


    # ===== UTILITAS =====
    (["pengadaan listrik"], ["power=plant"]),
    (["treatment air", "air minum"], ["man_made=water_works"]),
    (["treatment air limbah", "limbah"], ["man_made=wastewater_plant"]),
    (["pengumpulan", "pembuangan limbah", "sampah"], ["amenity=recycling", "landuse=landfill"]),
    (["aktivitas remediasi"], ["landuse=landfill"]),

    # ===== KONSTRUKSI =====
    (["konstruksi gedung", "konstruksi bangunan sipil", "konstruksi khusus"], ["office=construction_company"]),

    # ===== OTOMOTIF =====
    (["perdagangan, reparasi dan perawatan mobil"], ["shop=car_repair", "shop=car"]),
    (["reparasi dan perawatan mobil"], ["shop=car_repair"]),
    (["reparasi dan perawatan sepeda motor"], ["shop=motorcycle_repair"]),
    (["suku cadang"], ["shop=car_parts"]),

    # ===== PERDAGANGAN BESAR & GUDANG =====
    (["perdagangan besar"], ["shop=wholesale"]),
    (["pergudangan"], ["landuse=industrial", "industrial=warehouse"]),

    # ===== TRANSPORTASI =====
    (["angkutan darat"], ["amenity=bus_station", "amenity=taxi"]),
    (["angkutan perairan"], ["amenity=ferry_terminal"]),
    (["angkutan udara"], ["aeroway=aerodrome"]),
    (["penunjang angkutan"], ["amenity=warehouse"]),
    (["pos dan kurir"], ["amenity=post_office"]),

    # ===== AKOMODASI =====
    (["hotel bintang", "hotel melati", "penginapan", "losmen"], ["tourism=hotel", "tourism=guest_house"]),
    (["pondok wisata", "homestay"], ["tourism=guest_house"]),

    # ===== REPARASI =====
    (["reparasi komputer"], ["shop=computer"]),
    (["reparasi peralatan komunikasi"], ["shop=mobile_phone"]),
    (["reparasi alas kaki", "reparasi kulit"], ["shop=shoe_repair"]),
    (["reparasi furnitur"], ["craft=carpenter"]),
    (["reparasi peralatan listrik"], ["shop=repair"]),
    (["reparasi barang keperluan pribadi"], ["shop=repair"]),
    (["reparasi peralatan rumah tangga"], ["shop=repair"]),

    # ===== KECANTIKAN & PERAWATAN =====
    (["pangkas rambut", "salon kecantikan"], ["shop=hairdresser", "shop=beauty"]),
    (["pijat", "spa"], ["shop=massage", "leisure=spa"]),
    (["laundry", "binatu"], ["shop=laundry"]),

    # ===== FOTOGRAFI =====
    (["fotografi", "fotokopi"], ["shop=photo", "craft=photographer"]),

    # ===== PENDIDIKAN =====
    (["pendidikan anak usia dini", "paud"], ["amenity=kindergarten"]),
    (["pendidikan dasar"], ["amenity=school"]),
    (["pendidikan menengah"], ["amenity=school"]),
    (["pendidikan tinggi", "universitas", "kampus"], ["amenity=university", "amenity=college"]),
    (["pesantren"], ["amenity=place_of_worship"]),
    (["pendidikan olahraga"], ["leisure=sports_centre"]),
    (["pendidikan kebudayaan"], ["amenity=school"]),
    (["pendidikan lainnya"], ["amenity=school"]),
    (["sertifikasi hasil pendidikan"], ["office=educational_institution"]),

    # ===== KESEHATAN =====
    (["rumah sakit"], ["amenity=hospital"]),
    (["klinik", "dokter"], ["amenity=clinic", "amenity=doctors"]),
    (["kesehatan hewan", "dokter hewan"], ["amenity=veterinary"]),
    (["kesehatan manusia"], ["amenity=doctors"]),
    (["administrasi pelayanan pemerintah bidang kesehatan"], ["office=government"]),

    # ===== HIBURAN & REKREASI =====
    (["bioskop", "film"], ["amenity=cinema"]),
    (["karaoke", "hiburan malam"], ["amenity=nightclub"]),
    (["kebugaran", "gym", "fitness"], ["leisure=fitness_centre"]),
    (["taman bertema", "taman hiburan"], ["tourism=theme_park"]),
    (["olahraga", "rekreasi"], ["leisure=sports_centre"]),
    (["perpustakaan", "arsip"], ["amenity=library"]),
    (["museum"], ["tourism=museum"]),
    (["keanggotaan organisasi"], ["office=association"]),
    (["hiburan, seni dan kreativitas"], ["amenity=arts_centre"]),

    # ===== KEUANGAN =====
    (["jasa keuangan", "bank"], ["amenity=bank"]),
    (["koperasi"], ["office=financial"]),
    (["asuransi"], ["office=insurance"]),
    (["penunjang jasa keuangan"], ["office=financial"]),

    # ===== PEMERINTAHAN =====
    (["administrasi pemerintahan", "pertahanan"], ["office=government"]),
    (["ketertiban dan keamanan", "kepolisian"], ["amenity=police"]),
    (["pemadam kebakaran"], ["amenity=fire_station"]),

    # ===== TEKNOLOGI & PROFESIONAL =====
    (["pemrograman", "konsultasi komputer"], ["office=it"]),
    (["periklanan", "penelitian pasar"], ["office=advertising_agency"]),
    (["kantor pusat", "konsultasi manajemen"], ["office=company"]),
    (["hukum", "akuntansi"], ["office=lawyer", "office=accountant"]),
    (["arsitektur", "keinsinyuran"], ["office=architect", "office=engineer"]),
    (["agen perjalanan"], ["shop=travel_agency"]),
    (["real estat", "properti"], ["office=estate_agent"]),
    (["penyewaan", "sewa guna"], ["shop=rental"]),
    (["ketenagakerjaan"], ["office=employment_agency"]),
    (["keamanan dan penyelidikan"], ["office=security"]),
    (["perawatan taman", "pemeliharaan taman"], ["shop=garden_centre"]),
    (["administrasi kantor"], ["office=company"]),
    (["penelitian dan pengembangan"], ["office=research"]),
    (["jasa informasi"], ["office=company"]),
    (["penerbitan"], ["office=publisher"]),
    (["telekomunikasi"], ["office=telecommunication"]),
    (["penyiaran"], ["office=media"]),

    # ===== OLAHRAGA =====
    (["futsal", "badminton", "bola"], ["leisure=pitch", "leisure=sports_centre"]),
    (["kolam renang"], ["leisure=swimming_pool"]),

    # ===== SOSIAL =====
    (["sosial di dalam panti", "panti"], ["amenity=social_facility"]),
    (["sosial tanpa akomodasi"], ["amenity=social_facility"]),

    # ===== RUMAH TANGGA & LAINNYA =====
    (["rumah tangga sebagai pemberi kerja"], ["office=company"]),
    (["menghasilkan barang dan jasa oleh rumah tangga"], ["office=company"]),
    (["badan internasional"], ["office=international_organization"]),
]


def suggest_osm_tags(kbli_title: str) -> list:
    """Berdasarkan title KBLI, return list OSM tags yang disarankan."""
    if not kbli_title:
        return []
    title_lower = kbli_title.lower()
    tags = set()
    for keywords, osm_tags in RULES:
        if any(kw in title_lower for kw in keywords):
            tags.update(osm_tags)
    return sorted(tags)