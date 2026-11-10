"""Generates 20 synthetic Marathi deed text files in Kruti Dev encoding for converter testing."""

from pathlib import Path

# Mapping table of Unicode to Kruti Dev for generating realistic synthetic samples
# Inverted from standard Kruti Dev character pairs
UNICODE_TO_KRUTI_SAMPLE_DATA = [
    (
        "01_plot_sale_deed_header.txt",
        # "दस्ताऐवज खरेदीखत - भूखंड - नागपूर"
        "nLrkvSot [kjnh[kr & Hkw[kaM & ukxiwj",
        "दस्ताऐवज खरेदीखत - भूखंड - नागपूर",
    ),
    (
        "02_parties_individual_male.txt",
        # "विक्रेता: श्री. रमेश विठ्ठलराव पाटील, वय 45 वर्षे, धंदा नोकरी"
        "foØsrk% Jh- jes'k foB~Byjko ikVhy] o; 45 o"ksZ] /kank ukSdjh",
        "विक्रेता: श्री. रमेश विठ्ठलराव पाटील, वय 45 वर्षे, धंदा नोकरी",
    ),
    (
        "03_parties_individual_female.txt",
        # "खरेदीदार: सौ. सुनीता गजानन जोशी, वय 42 वर्षे, धंदा घरकाम"
        "[kjhnkj% lkS- lquhrk xtkuu tks'kh] o; 42 o"ksZ] /kank ?kjrke",
        "खरेदीदार: सौ. सुनीता गजानन जोशी, वय 42 वर्षे, धंदा घरकाम",
    ),
    (
        "04_parties_multiple_sellers.txt",
        # "सर्व संयुक्त मालक व हिस्सेदार"
        "loZ la;qDr ekyd o fgLlsnkj",
        "सर्व संयुक्त मालक व हिस्सेदार",
    ),
    (
        "05_property_mouza_khasra.txt",
        # "मौजे: सोनेगाव, पटवारी हल्का क्र. 45, खसरा क्र. 12/2"
        "ekSts% lksusxko] iVokjh gydk Ø- 45] [kljk Ø- 12@2",
        "मौजे: सोनेगाव, पटवारी हल्का क्र. 45, खसरा क्र. 12/2",
    ),
    (
        "06_four_boundaries_chaturseema.txt",
        # "चतुःसीमा: पूर्व रस्ता, पश्चिम भूखंड क्र. 15, उत्तर मोकळी जागा, दक्षिण रस्ता"
        "prq%lhek% iwoZ jLrk] if'pe Hkw[kaM Ø- 15] mRrj eksdGh tkxk] nf{k.k jLrk",
        "चतुःसीमा: पूर्व रस्ता, पश्चिम भूखंड क्र. 15, उत्तर मोकळी जागा, दक्षिण रस्ता",
    ),
    (
        "07_consideration_payment_terms.txt",
        # "एकूण मोबदला रक्कम रु. 15,50,000/- अक्षरी पंधरा लाख पन्नास हजार"
        ",dw.k eksocnyk jDde :- 15]50]000@& v{kjh ia/kjk yk[k iUuhl gtkj",
        "एकूण मोबदला रक्कम रु. 15,50,000/- अक्षरी पंधरा लाख पन्नास हजार",
    ),
    (
        "08_earnest_money_advance.txt",
        # "इसार पावती रक्कम रु. 2,00,000/- रोख स्वरूपात प्राप्त झाली"
        "blkj ikorh jDde :- 2]00]000@& jks[k Lo:ikr izkIr >kyh",
        "इसार पावती रक्कम रु. 2,00,000/- रोख स्वरूपात प्राप्त झाली",
    ),
    (
        "09_possession_clause.txt",
        # "सदर भूखंडाचा प्रत्यक्ष व शांततामय ताबा आज रोजी खरेदीदार यांना दिला आहे"
        "lnj Hkw[kaMkpk izR;{k o 'kkarre; rkck vkt jkstn [kjhnkj ;kauk fnyk vkgs",
        "सदर भूखंडाचा प्रत्यक्ष व शांततामय ताबा आज रोजी खरेदीदार यांना दिला आहे",
    ),
    (
        "10_witness_block.txt",
        # "साक्षीदार 1 व साक्षीदार 2 यांचे समक्ष स्वाक्षऱ्या केल्या"
        "lk{khnkj 1 o lk{khnkj 2 ;kaPks le{k Lok{k&;k dsY;k",
        "साक्षीदार 1 व साक्षीदार 2 यांचे समक्ष स्वाक्षऱ्या केल्या",
    ),
    (
        "11_general_power_of_attorney.txt",
        # "आमच्या वतीने सर्व व्यवहार करण्यासाठी कुलमुखत्यार नेमले आहे"
        "vkeP;k orhus loZ O;ogkj dj.;klkBh dqyeq[kR;kj useys vkgs",
        "आमच्या वतीने सर्व व्यवहार करण्यासाठी कुलमुखत्यार नेमले आहे",
    ),
    (
        "12_agreement_to_sell_flat.txt",
        # "सदनिका विक्रीचा इसारनामा करार"
        "lnfudk foØhpk blkjukek djkj",
        "सदनिका विक्रीचा इसारनामा करार",
    ),
    (
        "13_nit_sanction_order.txt",
        # "नागपूर सुधार प्रन्यास मंजूर लेआउट"
        "ukxiwj lq/kkj izU;kl eatwj ysDvkÅV",
        "नागपूर सुधार प्रन्यास मंजूर लेआउट",
    ),
    (
        "14_city_survey_sheet.txt",
        # "नगर भूमापन पत्रिका पत्रक क्र. 14"
        "uxj Hkwlekiu if=dk i=d Ø- 14",
        "नगर भूमापन पत्रिका पत्रक क्र. 14",
    ),
    (
        "15_encumbrance_free_warranty.txt",
        # "सदर मिळकत सर्व प्रकारच्या बोजा व कर्जापासून पूर्णपणे मुक्त आहे"
        "lnj feGdr loZ izdkjP;k ckstk o dtZkiklwu iw.kZi.ks eqDr vkgs",
        "सदर मिळकत सर्व प्रकारच्या बोजा व कर्जापासून पूर्णपणे मुक्त आहे",
    ),
    (
        "16_registration_statutory_duty.txt",
        # "मुद्रांक शुल्क व नोंदणी फी नियमानुसार भरली आहे"
        "eqnzkad 'kqYd o ukSan.kh QhStewart Hkjyh vkgs",
        "मुद्रांक शुल्क व नोंदणी फी नियमानुसार भरली आहे",
    ),
    (
        "17_agricultural_land_clause.txt",
        # "शेती जमीन क्षेत्रफळ 1 हेक्टर 20 आर"
        "'ksrh tehu {ks=QG 1 gsDVj 20 vkj",
        "शेती जमीन क्षेत्रफळ 1 हेक्टर 20 आर",
    ),
    (
        "18_commercial_shop_lease.txt",
        # "दुकान गाळा क्र. 5 तळमजला"
        "nqdkUk xkGk Ø- 5 rGeTnyk",
        "दुकान गाळा क्र. 5 तळमजला",
    ),
    (
        "19_latin_in_kruti_warning_pan.txt",
        # Accidental Latin text typed in Kruti run (PAN and Mobile)
        "विक्रेता PAN ABCDE1234F मोबाईल 9876543210 PLOT KHASRA",
        "विक्रेता PAN ABCDE1234F मोबाईल 9876543210 PLOT KHASRA",
    ),
    (
        "20_marathi_special_eyelash_reph.txt",
        # "निर्मळ पाणी व सकळ जन" (with Marathi retroflex L 'ळ')
        "fueZG ik.kh o ldG tu",
        "निर्मळ पाणी व सकळ जन",
    ),
]


def generate_samples(base_dir: Path) -> list[Path]:
    """Generates the 20 synthetic Kruti sample files on disk."""
    base_dir.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    for filename, kruti_content, _ in UNICODE_TO_KRUTI_SAMPLE_DATA:
        file_path = base_dir / filename
        file_path.write_text(kruti_content, encoding="utf-8")
        created.append(file_path)
    return created


if __name__ == "__main__":
    out_dir = Path(__file__).parent / "fixtures" / "synthetic_samples"
    files = generate_samples(out_dir)
    print(f"Created {len(files)} synthetic Marathi Kruti files in {out_dir}")

