// Auto-generated bundled template manifests for offline / static hosting
export const BUNDLED_MANIFESTS: Record<string, any> = {
  "agreement_to_sell_flat_en": {
    "manifest_schema": 1,
    "template_id": "agreement_to_sell_flat_en",
    "name_en": "Agreement to Sell (Flat / Apartment)",
    "name_mr": "साठेखत - सदनिका / फ्लॅट (इंग्रजी)",
    "version": 1,
    "status": "draft",
    "document_type": "agreement_to_sell",
    "property_type": "flat",
    "language": "en",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "promoters": {
        "role": "prospective_seller",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Vendor / Prospective Seller(s)",
        "label_mr": "विक्रेता / इसार घेणार"
      },
      "purchasers": {
        "role": "prospective_purchaser",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Purchaser / Prospective Buyer(s)",
        "label_mr": "खरेदीदार / इसार देणार"
      }
    },
    "repeaters": {
      "instalments": {
        "name": "instalments",
        "min": 1,
        "max": 6,
        "label_en": "Instalment Payment Schedule",
        "label_mr": "हप्त्यांचा तपशील"
      },
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "apartment_schedule",
        "title_en": "Apartment / Unit Details",
        "title_mr": "सदनिकेचे तपशील",
        "field_names": [
          "property.flat_no",
          "property.floor_no",
          "property.building_name",
          "property.mouza",
          "property.khasra_no",
          "property.carpet_area_sqm"
        ]
      },
      {
        "id": "agreement_terms",
        "title_en": "Agreed Consideration & Timeline",
        "title_mr": "मोबदला व अटी",
        "field_names": [
          "financial.total_consideration",
          "financial.earnest_amount",
          "terms.months_to_complete"
        ]
      }
    ],
    "fields": {
      "property.flat_no": {
        "name": "property.flat_no",
        "type": "string",
        "label_en": "Flat / Unit No.",
        "label_mr": "फ्लॅट क्र.",
        "required": true
      },
      "property.floor_no": {
        "name": "property.floor_no",
        "type": "string",
        "label_en": "Floor No.",
        "label_mr": "मजला",
        "required": true
      },
      "property.building_name": {
        "name": "property.building_name",
        "type": "string",
        "label_en": "Building / Wing Name",
        "label_mr": "इमारतीचे नाव",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Survey / Khasra No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.carpet_area_sqm": {
        "name": "property.carpet_area_sqm",
        "type": "decimal",
        "label_en": "RERA Carpet Area (sq. metres)",
        "label_mr": "रेरा चटई क्षेत्र (चौ. मी.)",
        "required": true
      },
      "financial.total_consideration": {
        "name": "financial.total_consideration",
        "type": "decimal",
        "label_en": "Total Agreed Consideration (Rs.)",
        "label_mr": "एकूण मान्य मोबदला (रुपये)",
        "required": true
      },
      "financial.earnest_amount": {
        "name": "financial.earnest_amount",
        "type": "decimal",
        "label_en": "Earnest / Token Money Paid (Rs.)",
        "label_mr": "इसार रक्कम (रुपये)",
        "required": true
      },
      "terms.months_to_complete": {
        "name": "terms.months_to_complete",
        "type": "integer",
        "label_en": "Time to Execute Sale Deed (Months)",
        "label_mr": "खरेदीखत नोंदणीची मुदत (महिने)",
        "required": true,
        "default": 3
      },
      "execution_date": {
        "name": "execution_date",
        "type": "date",
        "label_en": "Execution Date",
        "label_mr": "साठेखताची तारीख",
        "required": true
      }
    },
    "derived_fields": {
      "financial.balance_due": {
        "name": "financial.balance_due",
        "type": "decimal",
        "expression": "financial.total_consideration - financial.earnest_amount",
        "label_en": "Balance Consideration Due",
        "label_mr": "देय शिल्लक रक्कम"
      },
      "property.carpet_area_sqft": {
        "name": "property.carpet_area_sqft",
        "type": "decimal",
        "expression": "property.carpet_area_sqm * 10.7639104",
        "label_en": "Carpet Area (Sq. Feet)",
        "label_mr": "कार्पेट क्षेत्रफळ (चौ.फूट)"
      }
    },
    "validations": [
      {
        "id": "earnest_le_total",
        "condition": "financial.earnest_amount <= financial.total_consideration",
        "message_en": "Earnest money cannot exceed total agreed consideration.",
        "message_mr": "इसार रक्कम एकूण मोबदल्यापेक्षा जास्त असू शकत नाही.",
        "severity": "error"
      }
    ]
  },
  "agreement_to_sell_flat_hi": {
    "manifest_schema": 1,
    "template_id": "agreement_to_sell_flat_hi",
    "name_en": "Agreement to Sell (Flat / Apartment)",
    "name_mr": "सदनिका / फ्लैट विक्रय अनुबंध व बयाना रसीद",
    "version": 1,
    "status": "draft",
    "document_type": "agreement_to_sell",
    "property_type": "flat",
    "language": "hi",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "prospective_sellers": {
        "role": "prospective_seller",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Prospective Seller(s)",
        "label_mr": "प्रस्तावित विक्रेता"
      },
      "prospective_purchasers": {
        "role": "prospective_purchaser",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Prospective Purchaser(s)",
        "label_mr": "प्रस्तावित क्रेता"
      }
    },
    "repeaters": {
      "instalments": {
        "name": "instalments",
        "min": 1,
        "max": 6,
        "label_en": "Instalment Schedule",
        "label_mr": "हप्त्यांचा तपशील"
      },
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "apartment_schedule",
        "title_en": "Flat Schedule",
        "title_mr": "सदनिकेचे तपशील",
        "field_names": [
          "property.flat_no",
          "property.floor_no",
          "property.building_name",
          "property.mouza",
          "property.khasra_no",
          "property.carpet_area_sqm"
        ]
      },
      {
        "id": "agreement_terms",
        "title_en": "Consideration & Terms",
        "title_mr": "मोबदला व अटी",
        "field_names": [
          "financial.total_consideration",
          "financial.earnest_amount",
          "terms.months_to_complete"
        ]
      }
    ],
    "fields": {
      "property.flat_no": {
        "name": "property.flat_no",
        "type": "string",
        "label_en": "Flat No.",
        "label_mr": "सदनिका क्र.",
        "required": true
      },
      "property.floor_no": {
        "name": "property.floor_no",
        "type": "string",
        "label_en": "Floor No.",
        "label_mr": "मजला क्र.",
        "required": true
      },
      "property.building_name": {
        "name": "property.building_name",
        "type": "string",
        "label_en": "Building Name",
        "label_mr": "इमारतीचे नाव",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra No.",
        "label_mr": "खसरा क्र.",
        "required": true
      },
      "property.carpet_area_sqm": {
        "name": "property.carpet_area_sqm",
        "type": "decimal",
        "label_en": "Carpet Area (Sq. Metres)",
        "label_mr": "कार्पेट क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "financial.total_consideration": {
        "name": "financial.total_consideration",
        "type": "decimal",
        "label_en": "Total Agreed Price (Rs.)",
        "label_mr": "एकूण ठरलेला मोबदला (रु.)",
        "required": true
      },
      "financial.earnest_amount": {
        "name": "financial.earnest_amount",
        "type": "decimal",
        "label_en": "Earnest Money Received (Rs.)",
        "label_mr": "मिळालेली इसार रक्कम (रु.)",
        "required": true
      },
      "terms.months_to_complete": {
        "name": "terms.months_to_complete",
        "type": "integer",
        "label_en": "Months to Execute Final Sale Deed",
        "label_mr": "अंतिम खरेदीखतासाठी कालावधी (महिने)",
        "required": true,
        "default": 3
      },
      "execution_date": {
        "name": "execution_date",
        "type": "date",
        "label_en": "Execution Date",
        "label_mr": "साठेखताची तारीख",
        "required": true
      }
    },
    "derived_fields": {
      "financial.balance_due": {
        "name": "financial.balance_due",
        "type": "decimal",
        "expression": "financial.total_consideration - financial.earnest_amount",
        "label_en": "Balance Due",
        "label_mr": "देय शिल्लक रक्कम"
      },
      "property.carpet_area_sqft": {
        "name": "property.carpet_area_sqft",
        "type": "decimal",
        "expression": "property.carpet_area_sqm * 10.7639104",
        "label_en": "Carpet Area (Sq. Feet)",
        "label_mr": "कार्पेट क्षेत्रफळ (चौ.फूट)"
      }
    },
    "validations": [
      {
        "id": "earnest_le_total",
        "condition": "financial.earnest_amount <= financial.total_consideration",
        "message_en": "Earnest money cannot exceed total consideration",
        "message_mr": "इसार रक्कम एकूण मोबदल्यापेक्षा जास्त असू शकत नाही",
        "severity": "error"
      }
    ]
  },
  "agreement_to_sell_flat_mr": {
    "manifest_schema": 1,
    "template_id": "agreement_to_sell_flat_mr",
    "name_en": "Agreement to Sell (Flat / Apartment in Marathi)",
    "name_mr": "साठेखत / इसारपावती (सदनिका / फ्लॅट)",
    "version": 1,
    "status": "draft",
    "document_type": "agreement_to_sell",
    "property_type": "flat",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "prospective_sellers": {
        "role": "prospective_seller",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Prospective Seller(s)",
        "label_mr": "लिहून देणार / इसार घेणार"
      },
      "prospective_purchasers": {
        "role": "prospective_purchaser",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Prospective Purchaser(s)",
        "label_mr": "लिहून घेणार / इसार देणार"
      }
    },
    "repeaters": {
      "instalments": {
        "name": "instalments",
        "min": 1,
        "max": 6,
        "label_en": "Instalment Schedule",
        "label_mr": "हप्त्यांचा तपशील"
      },
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "apartment_schedule",
        "title_en": "Flat Schedule",
        "title_mr": "सदनिकेचे तपशील",
        "field_names": [
          "property.flat_no",
          "property.floor_no",
          "property.building_name",
          "property.mouza",
          "property.khasra_no",
          "property.carpet_area_sqm"
        ]
      },
      {
        "id": "agreement_terms",
        "title_en": "Consideration & Terms",
        "title_mr": "मोबदला व अटी",
        "field_names": [
          "financial.total_consideration",
          "financial.earnest_amount",
          "terms.months_to_complete"
        ]
      }
    ],
    "fields": {
      "property.flat_no": {
        "name": "property.flat_no",
        "type": "string",
        "label_en": "Flat No.",
        "label_mr": "सदनिका क्र.",
        "required": true
      },
      "property.floor_no": {
        "name": "property.floor_no",
        "type": "string",
        "label_en": "Floor No.",
        "label_mr": "मजला क्र.",
        "required": true
      },
      "property.building_name": {
        "name": "property.building_name",
        "type": "string",
        "label_en": "Building Name",
        "label_mr": "इमारतीचे नाव",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra No.",
        "label_mr": "खसरा क्र.",
        "required": true
      },
      "property.carpet_area_sqm": {
        "name": "property.carpet_area_sqm",
        "type": "decimal",
        "label_en": "Carpet Area (Sq. Metres)",
        "label_mr": "कार्पेट क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "financial.total_consideration": {
        "name": "financial.total_consideration",
        "type": "decimal",
        "label_en": "Total Agreed Price (Rs.)",
        "label_mr": "एकूण ठरलेला मोबदला (रु.)",
        "required": true
      },
      "financial.earnest_amount": {
        "name": "financial.earnest_amount",
        "type": "decimal",
        "label_en": "Earnest Money Received (Rs.)",
        "label_mr": "मिळालेली इसार रक्कम (रु.)",
        "required": true
      },
      "terms.months_to_complete": {
        "name": "terms.months_to_complete",
        "type": "integer",
        "label_en": "Months to Execute Final Sale Deed",
        "label_mr": "अंतिम खरेदीखतासाठी कालावधी (महिने)",
        "required": true,
        "default": 3
      },
      "execution_date": {
        "name": "execution_date",
        "type": "date",
        "label_en": "Execution Date",
        "label_mr": "साठेखताची तारीख",
        "required": true
      }
    },
    "derived_fields": {
      "financial.balance_due": {
        "name": "financial.balance_due",
        "type": "decimal",
        "expression": "financial.total_consideration - financial.earnest_amount",
        "label_en": "Balance Due",
        "label_mr": "देय शिल्लक रक्कम"
      },
      "property.carpet_area_sqft": {
        "name": "property.carpet_area_sqft",
        "type": "decimal",
        "expression": "property.carpet_area_sqm * 10.7639104",
        "label_en": "Carpet Area (Sq. Feet)",
        "label_mr": "कार्पेट क्षेत्रफळ (चौ.फूट)"
      }
    },
    "validations": [
      {
        "id": "earnest_le_total",
        "condition": "financial.earnest_amount <= financial.total_consideration",
        "message_en": "Earnest money cannot exceed total consideration",
        "message_mr": "इसार रक्कम एकूण मोबदल्यापेक्षा जास्त असू शकत नाही",
        "severity": "error"
      }
    ]
  },
  "agreement_to_sell_plot_hi": {
    "manifest_schema": 1,
    "template_id": "agreement_to_sell_plot_hi",
    "name_en": "Agreement to Sell (Plot)",
    "name_mr": "बयाना इकरारनामा / विक्रय अनुबंध (भूखंड)",
    "version": 1,
    "status": "draft",
    "document_type": "agreement_to_sell",
    "property_type": "plot",
    "language": "hi",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "prospective_sellers": {
        "role": "prospective_seller",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Prospective Seller(s)",
        "label_mr": "प्रस्तावित विक्रेता"
      },
      "prospective_purchasers": {
        "role": "prospective_purchaser",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Prospective Purchaser(s)",
        "label_mr": "प्रस्तावित क्रेता"
      }
    },
    "repeaters": {
      "instalments": {
        "name": "instalments",
        "min": 1,
        "max": 8,
        "label_en": "Agreed Instalments",
        "label_mr": "ठरलेले हप्ते"
      },
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे तपशील",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.plot_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "agreement_terms",
        "title_en": "Terms & Consideration",
        "title_mr": "व्यवहाराच्या अटी व मोबदला",
        "field_names": [
          "financial.total_consideration",
          "financial.earnest_amount",
          "financial.has_bank_loan",
          "financial.bank_loan_amount",
          "terms.months_to_complete"
        ]
      }
    ],
    "fields": {
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra No.",
        "label_mr": "खसरा क्र.",
        "required": true
      },
      "property.plot_no": {
        "name": "property.plot_no",
        "type": "string",
        "label_en": "Plot No.",
        "label_mr": "प्लॉट क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "financial.total_consideration": {
        "name": "financial.total_consideration",
        "type": "decimal",
        "label_en": "Total Agreed Price (Rs.)",
        "label_mr": "एकूण ठरलेला मोबदला (रु.)",
        "required": true
      },
      "financial.earnest_amount": {
        "name": "financial.earnest_amount",
        "type": "decimal",
        "label_en": "Earnest / Token Received (Rs.)",
        "label_mr": "मिळालेली इसार रक्कम (रु.)",
        "required": true
      },
      "financial.has_bank_loan": {
        "name": "financial.has_bank_loan",
        "type": "boolean",
        "label_en": "Purchaser Availing Bank Loan?",
        "label_mr": "खरेदीदार बँक कर्ज घेणार आहे का?",
        "required": true,
        "default": false
      },
      "financial.bank_loan_amount": {
        "name": "financial.bank_loan_amount",
        "type": "decimal",
        "label_en": "Proposed Bank Loan Amount (Rs.)",
        "label_mr": "बँक कर्ज रक्कम (रु.)",
        "required": false,
        "visible_when": "financial.has_bank_loan == true"
      },
      "terms.months_to_complete": {
        "name": "terms.months_to_complete",
        "type": "integer",
        "label_en": "Time to Execute Final Sale Deed (Months)",
        "label_mr": "अंतिम खरेदीखत करण्याचा कालावधी (महिने)",
        "required": true,
        "default": 3
      },
      "execution_date": {
        "name": "execution_date",
        "type": "date",
        "label_en": "Agreement Date",
        "label_mr": "साठेखताची तारीख",
        "required": true
      }
    },
    "derived_fields": {
      "financial.balance_due": {
        "name": "financial.balance_due",
        "type": "decimal",
        "expression": "financial.total_consideration - financial.earnest_amount",
        "label_en": "Remaining Balance Due",
        "label_mr": "देय शिल्लक रक्कम"
      },
      "property.area_sqft": {
        "name": "property.area_sqft",
        "type": "decimal",
        "expression": "property.area_sqm * 10.7639104",
        "label_en": "Area (Sq. Feet)",
        "label_mr": "क्षेत्रफळ (चौ.फूट)"
      }
    },
    "validations": [
      {
        "id": "earnest_less_than_total",
        "condition": "financial.earnest_amount < financial.total_consideration",
        "message_en": "Earnest amount must be less than total consideration",
        "message_mr": "इसार रक्कम एकूण मोबदल्यापेक्षा कमी असणे आवश्यक आहे",
        "severity": "error"
      },
      {
        "id": "valid_period",
        "condition": "terms.months_to_complete > 0",
        "message_en": "Completion period must be at least 1 month",
        "message_mr": "कालावधी किमान १ महिना असणे आवश्यक आहे",
        "severity": "error"
      }
    ]
  },
  "agreement_to_sell_plot_mr": {
    "manifest_schema": 1,
    "template_id": "agreement_to_sell_plot_mr",
    "name_en": "Agreement to Sell (Plot)",
    "name_mr": "साठेखत / इसारपावती (भूखंड)",
    "version": 1,
    "status": "draft",
    "document_type": "agreement_to_sell",
    "property_type": "plot",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "prospective_sellers": {
        "role": "prospective_seller",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Prospective Seller(s)",
        "label_mr": "लिहून देणार / इसार घेणार"
      },
      "prospective_purchasers": {
        "role": "prospective_purchaser",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Prospective Purchaser(s)",
        "label_mr": "लिहून घेणार / इसार देणार"
      }
    },
    "repeaters": {
      "instalments": {
        "name": "instalments",
        "min": 1,
        "max": 8,
        "label_en": "Agreed Instalments",
        "label_mr": "ठरलेले हप्ते"
      },
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे तपशील",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.plot_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "agreement_terms",
        "title_en": "Terms & Consideration",
        "title_mr": "व्यवहाराच्या अटी व मोबदला",
        "field_names": [
          "financial.total_consideration",
          "financial.earnest_amount",
          "financial.has_bank_loan",
          "financial.bank_loan_amount",
          "terms.months_to_complete"
        ]
      }
    ],
    "fields": {
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra No.",
        "label_mr": "खसरा क्र.",
        "required": true
      },
      "property.plot_no": {
        "name": "property.plot_no",
        "type": "string",
        "label_en": "Plot No.",
        "label_mr": "प्लॉट क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "financial.total_consideration": {
        "name": "financial.total_consideration",
        "type": "decimal",
        "label_en": "Total Agreed Price (Rs.)",
        "label_mr": "एकूण ठरलेला मोबदला (रु.)",
        "required": true
      },
      "financial.earnest_amount": {
        "name": "financial.earnest_amount",
        "type": "decimal",
        "label_en": "Earnest / Token Received (Rs.)",
        "label_mr": "मिळालेली इसार रक्कम (रु.)",
        "required": true
      },
      "financial.has_bank_loan": {
        "name": "financial.has_bank_loan",
        "type": "boolean",
        "label_en": "Purchaser Availing Bank Loan?",
        "label_mr": "खरेदीदार बँक कर्ज घेणार आहे का?",
        "required": true,
        "default": false
      },
      "financial.bank_loan_amount": {
        "name": "financial.bank_loan_amount",
        "type": "decimal",
        "label_en": "Proposed Bank Loan Amount (Rs.)",
        "label_mr": "बँक कर्ज रक्कम (रु.)",
        "required": false,
        "visible_when": "financial.has_bank_loan == true"
      },
      "terms.months_to_complete": {
        "name": "terms.months_to_complete",
        "type": "integer",
        "label_en": "Time to Execute Final Sale Deed (Months)",
        "label_mr": "अंतिम खरेदीखत करण्याचा कालावधी (महिने)",
        "required": true,
        "default": 3
      },
      "execution_date": {
        "name": "execution_date",
        "type": "date",
        "label_en": "Agreement Date",
        "label_mr": "साठेखताची तारीख",
        "required": true
      }
    },
    "derived_fields": {
      "financial.balance_due": {
        "name": "financial.balance_due",
        "type": "decimal",
        "expression": "financial.total_consideration - financial.earnest_amount",
        "label_en": "Remaining Balance Due",
        "label_mr": "देय शिल्लक रक्कम"
      },
      "property.area_sqft": {
        "name": "property.area_sqft",
        "type": "decimal",
        "expression": "property.area_sqm * 10.7639104",
        "label_en": "Area (Sq. Feet)",
        "label_mr": "क्षेत्रफळ (चौ.फूट)"
      }
    },
    "validations": [
      {
        "id": "earnest_less_than_total",
        "condition": "financial.earnest_amount < financial.total_consideration",
        "message_en": "Earnest amount must be less than total consideration",
        "message_mr": "इसार रक्कम एकूण मोबदल्यापेक्षा कमी असणे आवश्यक आहे",
        "severity": "error"
      },
      {
        "id": "valid_period",
        "condition": "terms.months_to_complete > 0",
        "message_en": "Completion period must be at least 1 month",
        "message_mr": "कालावधी किमान १ महिना असणे आवश्यक आहे",
        "severity": "error"
      }
    ]
  },
  "agri_lease_en": {
    "manifest_schema": 1,
    "template_id": "agri_lease_en",
    "name_en": "Agricultural Land Lease Deed (Khandpatra)",
    "name_mr": "शेतजमीन खंडपत्र करार (कौलिक करार)",
    "version": 1,
    "status": "draft",
    "document_type": "agri_lease",
    "property_type": "agricultural",
    "language": "en",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "land_owners": {
        "role": "land_owner",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Agricultural Landowner(s)",
        "label_mr": "जमीन मालक (शेतमालक)"
      },
      "cultivators": {
        "role": "cultivator",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Cultivator / Tenant Farmer",
        "label_mr": "खंडकरी / वहिवाटदार शेतकरी"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "agri_lease_mr": {
    "manifest_schema": 1,
    "template_id": "agri_lease_mr",
    "name_en": "Agricultural Land Lease Deed (Khandpatra)",
    "name_mr": "शेतजमीन खंडपत्र करार (कौलिक करार)",
    "version": 1,
    "status": "draft",
    "document_type": "agri_lease",
    "property_type": "agricultural",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "land_owners": {
        "role": "land_owner",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Agricultural Landowner(s)",
        "label_mr": "जमीन मालक (शेतमालक)"
      },
      "cultivators": {
        "role": "cultivator",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Cultivator / Tenant Farmer",
        "label_mr": "खंडकरी / वहिवाटदार शेतकरी"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "exchange_deed_en": {
    "manifest_schema": 1,
    "template_id": "exchange_deed_en",
    "name_en": "Deed of Exchange (Immoveable Property)",
    "name_mr": "अदलाबदल पत्र (मिळकत अदलाबदल दस्त)",
    "version": 1,
    "status": "draft",
    "document_type": "exchange_deed",
    "property_type": "plot",
    "language": "en",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "first_parties": {
        "role": "first_party",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Party of First Part",
        "label_mr": "प्रथम पक्षकार"
      },
      "second_parties": {
        "role": "second_party",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Party of Second Part",
        "label_mr": "द्वितीय पक्षकार"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "title_warranty",
      "witness_attestation"
    ]
  },
  "exchange_deed_mr": {
    "manifest_schema": 1,
    "template_id": "exchange_deed_mr",
    "name_en": "Deed of Exchange (Immoveable Property)",
    "name_mr": "अदलाबदल पत्र (मिळकत अदलाबदल दस्त)",
    "version": 1,
    "status": "draft",
    "document_type": "exchange_deed",
    "property_type": "plot",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "first_parties": {
        "role": "first_party",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Party of First Part",
        "label_mr": "प्रथम पक्षकार"
      },
      "second_parties": {
        "role": "second_party",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Party of Second Part",
        "label_mr": "द्वितीय पक्षकार"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "title_warranty",
      "witness_attestation"
    ]
  },
  "family_partition_en": {
    "manifest_schema": 1,
    "template_id": "family_partition_en",
    "name_en": "Deed of Family Partition (Coparcenary Property)",
    "name_mr": "कौटुंबिक वाटणीपत्र (सहहिस्सेदार वाटप दस्त)",
    "version": 1,
    "status": "draft",
    "document_type": "family_partition",
    "property_type": "agricultural",
    "language": "en",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "first_sharers": {
        "role": "coparcener_1",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "First Coparcener",
        "label_mr": "प्रथम वाटणीदार"
      },
      "second_sharers": {
        "role": "coparcener_2",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Second Coparcener",
        "label_mr": "द्वितीय वाटणीदार"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "family_partition_mr": {
    "manifest_schema": 1,
    "template_id": "family_partition_mr",
    "name_en": "Deed of Family Partition (Coparcenary Property)",
    "name_mr": "कौटुंबिक वाटणीपत्र (सहहिस्सेदार वाटप दस्त)",
    "version": 1,
    "status": "draft",
    "document_type": "family_partition",
    "property_type": "agricultural",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "first_sharers": {
        "role": "coparcener_1",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "First Coparcener",
        "label_mr": "प्रथम वाटणीदार"
      },
      "second_sharers": {
        "role": "coparcener_2",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Second Coparcener",
        "label_mr": "द्वितीय वाटणीदार"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "family_settlement_en": {
    "manifest_schema": 1,
    "template_id": "family_settlement_en",
    "name_en": "Family Settlement Agreement (Dispute Resolution)",
    "name_mr": "कौटुंबिक समजोता पत्र (आपसातील समझोता करार)",
    "version": 1,
    "status": "draft",
    "document_type": "family_settlement",
    "property_type": "residential",
    "language": "en",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "first_parties": {
        "role": "first_party",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Party of First Part",
        "label_mr": "प्रथम पक्षकार"
      },
      "second_parties": {
        "role": "second_party",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Party of Second Part",
        "label_mr": "द्वितीय पक्षकार"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "family_settlement_mr": {
    "manifest_schema": 1,
    "template_id": "family_settlement_mr",
    "name_en": "Family Settlement Agreement (Dispute Resolution)",
    "name_mr": "कौटुंबिक समजोता पत्र (आपसातील समझोता करार)",
    "version": 1,
    "status": "draft",
    "document_type": "family_settlement",
    "property_type": "residential",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "first_parties": {
        "role": "first_party",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Party of First Part",
        "label_mr": "प्रथम पक्षकार"
      },
      "second_parties": {
        "role": "second_party",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Party of Second Part",
        "label_mr": "द्वितीय पक्षकार"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "flat_leave_licence_en": {
    "manifest_schema": 1,
    "template_id": "flat_leave_licence_en",
    "name_en": "Apartment Leave and Licence Agreement",
    "name_mr": "सदनिका लिव्ह अँड लायसन्स करार (अपार्टमेंट परवाना)",
    "version": 1,
    "status": "draft",
    "document_type": "leave_and_licence",
    "property_type": "flat",
    "language": "en",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "licensors": {
        "role": "licensor",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Licensor(s)",
        "label_mr": "परवाना देणारे (सदनिका मालक)"
      },
      "licensees": {
        "role": "licensee",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Licensee(s)",
        "label_mr": "परवाना घेणारे (वापरकर्ते)"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "flat_leave_licence_mr": {
    "manifest_schema": 1,
    "template_id": "flat_leave_licence_mr",
    "name_en": "Apartment Leave and Licence Agreement",
    "name_mr": "सदनिका लिव्ह अँड लायसन्स करार (अपार्टमेंट परवाना)",
    "version": 1,
    "status": "draft",
    "document_type": "leave_and_licence",
    "property_type": "flat",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "licensors": {
        "role": "licensor",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Licensor(s)",
        "label_mr": "परवाना देणारे (सदनिका मालक)"
      },
      "licensees": {
        "role": "licensee",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Licensee(s)",
        "label_mr": "परवाना घेणारे (वापरकर्ते)"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "general_agreement_en": {
    "manifest_schema": 1,
    "template_id": "general_agreement_en",
    "name_en": "General Agreement / Memorandum of Understanding",
    "name_mr": "सर्वसाधारण करारनामा",
    "version": 1,
    "status": "draft",
    "document_type": "general_agreement",
    "property_type": "general",
    "language": "en",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "first_parties": {
        "role": "first_party",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "First Party",
        "label_mr": "प्रथम पक्षकार"
      },
      "second_parties": {
        "role": "second_party",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Second Party",
        "label_mr": "द्वितीय पक्षकार"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "agreement_terms",
        "title_en": "Agreement Terms",
        "title_mr": "कराराच्या अटी व तपशील",
        "field_names": [
          "execution_date"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "general_agreement_mr": {
    "manifest_schema": 1,
    "template_id": "general_agreement_mr",
    "name_en": "General Agreement / Memorandum of Understanding",
    "name_mr": "सर्वसाधारण करारनामा",
    "version": 1,
    "status": "draft",
    "document_type": "general_agreement",
    "property_type": "general",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "first_parties": {
        "role": "first_party",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "First Party",
        "label_mr": "प्रथम पक्षकार"
      },
      "second_parties": {
        "role": "second_party",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Second Party",
        "label_mr": "द्वितीय पक्षकार"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "agreement_terms",
        "title_en": "Agreement Terms",
        "title_mr": "कराराच्या अटी व तपशील",
        "field_names": [
          "execution_date"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "general_poa_en": {
    "manifest_schema": 1,
    "template_id": "general_poa_en",
    "name_en": "General Power of Attorney",
    "name_mr": "कुलमुखत्यारपत्र (General POA - इंग्रजी)",
    "version": 1,
    "status": "draft",
    "document_type": "general_poa",
    "property_type": "general",
    "language": "en",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "principals": {
        "role": "principal",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Principal(s) / Executant(s)",
        "label_mr": "मुखत्यारपत्र लिहून देणारे"
      },
      "attorneys": {
        "role": "attorney",
        "min_parties": 1,
        "max_parties": 2,
        "label_en": "Appointed Attorney(s) / Agent(s)",
        "label_mr": "नेमलेले मुखत्यार"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_reference",
        "title_en": "Subject Matter / Property Particulars",
        "title_mr": "मिळकतीचा संदर्भ",
        "field_names": [
          "property.description",
          "property.mouza",
          "property.khasra_no"
        ]
      },
      {
        "id": "powers_schedule",
        "title_en": "Powers Conferred Upon Attorney",
        "title_mr": "प्रदत्त अधिकार",
        "field_names": [
          "powers.can_sell",
          "powers.can_mortgage",
          "powers.can_appear_court",
          "powers.can_sign_portal"
        ]
      }
    ],
    "fields": {
      "property.description": {
        "name": "property.description",
        "type": "string",
        "label_en": "Property / Matter Summary",
        "label_mr": "मिळकतीचे संक्षिप्त वर्णन",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Locality",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Survey / Khasra / CTS No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "powers.can_sell": {
        "name": "powers.can_sell",
        "type": "boolean",
        "label_en": "Power to sell, convey or transfer property",
        "label_mr": "विक्री अथवा हस्तांतरण करण्याचा अधिकार",
        "required": true,
        "default": true
      },
      "powers.can_mortgage": {
        "name": "powers.can_mortgage",
        "type": "boolean",
        "label_en": "Power to create mortgage / charge with financial institutions",
        "label_mr": "गहाणखत / बोजा नोंदविण्याचा अधिकार",
        "required": true,
        "default": false
      },
      "powers.can_appear_court": {
        "name": "powers.can_appear_court",
        "type": "boolean",
        "label_en": "Power to appear before Courts, Tribunals and Registrar",
        "label_mr": "न्यायालय व निबंधकांसमोर उपस्थित राहण्याचा अधिकार",
        "required": true,
        "default": true
      },
      "powers.can_sign_portal": {
        "name": "powers.can_sign_portal",
        "type": "boolean",
        "label_en": "Power to digitally sign e-filing portals & municipal records",
        "label_mr": "ऑनलाइन पोर्टल व नगररचना दस्त स्वाक्षरी अधिकार",
        "required": true,
        "default": true
      },
      "execution_date": {
        "name": "execution_date",
        "type": "date",
        "label_en": "Execution Date",
        "label_mr": "दस्त निष्पादनाची तारीख",
        "required": true
      }
    },
    "derived_fields": {},
    "validations": []
  },
  "general_poa_hi": {
    "manifest_schema": 1,
    "template_id": "general_poa_hi",
    "name_en": "General Power of Attorney (GPA)",
    "name_mr": "सामान्य मुख्तारनामा (जनरल पावर ऑफ अटॉर्नी)",
    "version": 1,
    "status": "draft",
    "document_type": "general_poa",
    "property_type": "general",
    "language": "hi",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "principals": {
        "role": "principal",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Principal(s)",
        "label_mr": "मुख्तारकर्ता (Principal)"
      },
      "attorneys": {
        "role": "attorney",
        "min_parties": 1,
        "max_parties": 2,
        "label_en": "Attorney(s)",
        "label_mr": "मुख्तारआम (Attorney)"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_reference",
        "title_en": "Property / Matter Subject",
        "title_mr": "मिळकतीचा संदर्भ",
        "field_names": [
          "property.description",
          "property.mouza",
          "property.khasra_no"
        ]
      },
      {
        "id": "powers_schedule",
        "title_en": "Powers Granted",
        "title_mr": "प्रदत्त अधिकार व अधिकारकक्षा",
        "field_names": [
          "powers.can_sell",
          "powers.can_mortgage",
          "powers.can_appear_court",
          "powers.can_sign_portal"
        ]
      }
    ],
    "fields": {
      "property.description": {
        "name": "property.description",
        "type": "string",
        "label_en": "Subject Property Summary",
        "label_mr": "मिळकतीचे संक्षिप्त वर्णन",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "powers.can_sell": {
        "name": "powers.can_sell",
        "type": "boolean",
        "label_en": "Power to Sell / Convey Property?",
        "label_mr": "विक्री अथवा हस्तांतरण करण्याचा अधिकार?",
        "required": true,
        "default": true
      },
      "powers.can_mortgage": {
        "name": "powers.can_mortgage",
        "type": "boolean",
        "label_en": "Power to Mortgage / Create Charge?",
        "label_mr": "गहाण ठेवणे किंवा बोजा निर्माण करण्याचा अधिकार?",
        "required": true,
        "default": false
      },
      "powers.can_appear_court": {
        "name": "powers.can_appear_court",
        "type": "boolean",
        "label_en": "Power to Represent in Courts / Tribunals?",
        "label_mr": "न्यायालयीन व महसूल कामांसाठी हजर राहण्याचा अधिकार?",
        "required": true,
        "default": true
      },
      "powers.can_sign_portal": {
        "name": "powers.can_sign_portal",
        "type": "boolean",
        "label_en": "Power to Sign Government / Portal Submissions?",
        "label_mr": "शासकीय कार्यालये व नोंदणी पोर्टलवर स्वाक्षरी करण्याचा अधिकार?",
        "required": true,
        "default": true
      },
      "execution_date": {
        "name": "execution_date",
        "type": "date",
        "label_en": "Execution Date",
        "label_mr": "दस्त निष्पादनाची तारीख",
        "required": true
      }
    },
    "derived_fields": {},
    "validations": []
  },
  "general_poa_mr": {
    "manifest_schema": 1,
    "template_id": "general_poa_mr",
    "name_en": "General Power of Attorney (Marathi)",
    "name_mr": "कुलमुखत्यारपत्र (General POA)",
    "version": 1,
    "status": "draft",
    "document_type": "general_poa",
    "property_type": "general",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "principals": {
        "role": "principal",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Principal(s) / मुखत्यारपत्र लिहून देणारे",
        "label_mr": "मुखत्यारपत्र लिहून देणारे"
      },
      "attorneys": {
        "role": "attorney",
        "min_parties": 1,
        "max_parties": 2,
        "label_en": "Appointed Attorney(s) / मुखत्यार",
        "label_mr": "नेमलेले मुखत्यार"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_reference",
        "title_en": "Property / Matter Subject",
        "title_mr": "मिळकतीचा संदर्भ",
        "field_names": [
          "property.description",
          "property.mouza",
          "property.khasra_no"
        ]
      },
      {
        "id": "powers_schedule",
        "title_en": "Powers Granted",
        "title_mr": "प्रदत्त अधिकार व अधिकारकक्षा",
        "field_names": [
          "powers.can_sell",
          "powers.can_mortgage",
          "powers.can_appear_court",
          "powers.can_sign_portal"
        ]
      }
    ],
    "fields": {
      "property.description": {
        "name": "property.description",
        "type": "string",
        "label_en": "Subject Property Summary",
        "label_mr": "मिळकतीचे संक्षिप्त वर्णन",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "powers.can_sell": {
        "name": "powers.can_sell",
        "type": "boolean",
        "label_en": "Power to Sell / Convey Property?",
        "label_mr": "विक्री अथवा हस्तांतरण करण्याचा अधिकार?",
        "required": true,
        "default": true
      },
      "powers.can_mortgage": {
        "name": "powers.can_mortgage",
        "type": "boolean",
        "label_en": "Power to Mortgage / Create Charge?",
        "label_mr": "गहाण ठेवणे किंवा बोजा निर्माण करण्याचा अधिकार?",
        "required": true,
        "default": false
      },
      "powers.can_appear_court": {
        "name": "powers.can_appear_court",
        "type": "boolean",
        "label_en": "Power to Represent in Courts / Tribunals?",
        "label_mr": "न्यायालयीन व महसूल कामांसाठी हजर राहण्याचा अधिकार?",
        "required": true,
        "default": true
      },
      "powers.can_sign_portal": {
        "name": "powers.can_sign_portal",
        "type": "boolean",
        "label_en": "Power to Sign Government / Portal Submissions?",
        "label_mr": "शासकीय कार्यालये व नोंदणी पोर्टलवर स्वाक्षरी करण्याचा अधिकार?",
        "required": true,
        "default": true
      },
      "execution_date": {
        "name": "execution_date",
        "type": "date",
        "label_en": "Execution Date",
        "label_mr": "दस्त निष्पादनाची तारीख",
        "required": true
      }
    },
    "derived_fields": {},
    "validations": []
  },
  "gift_deed_en": {
    "manifest_schema": 1,
    "template_id": "gift_deed_en",
    "name_en": "Gift Deed (Immoveable Property)",
    "name_mr": "दानपत्र (बक्षीसपत्र)",
    "version": 1,
    "status": "draft",
    "document_type": "gift_deed",
    "property_type": "plot",
    "language": "en",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "donors": {
        "role": "donor",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Donor(s)",
        "label_mr": "दान देणारे (दाता)"
      },
      "donees": {
        "role": "donee",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Donee(s)",
        "label_mr": "दान घेणारे (ग्रहिता)"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "title_warranty",
      "witness_attestation"
    ]
  },
  "gift_deed_mr": {
    "manifest_schema": 1,
    "template_id": "gift_deed_mr",
    "name_en": "Gift Deed (Immoveable Property)",
    "name_mr": "दानपत्र (बक्षीसपत्र)",
    "version": 1,
    "status": "draft",
    "document_type": "gift_deed",
    "property_type": "plot",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "donors": {
        "role": "donor",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Donor(s)",
        "label_mr": "दान देणारे (दाता)"
      },
      "donees": {
        "role": "donee",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Donee(s)",
        "label_mr": "दान घेणारे (ग्रहिता)"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "title_warranty",
      "witness_attestation"
    ]
  },
  "house_sale_deed_en": {
    "manifest_schema": 1,
    "template_id": "house_sale_deed_en",
    "name_en": "Deed of Absolute Sale (Residential House / Bungalow)",
    "name_mr": "घर / इमारत खरेदीखत",
    "version": 1,
    "status": "draft",
    "document_type": "sale_deed",
    "property_type": "residential",
    "language": "en",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "sellers": {
        "role": "seller",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Seller(s) / Vendor(s)",
        "label_mr": "विक्रेता"
      },
      "purchasers": {
        "role": "purchaser",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Purchaser(s)",
        "label_mr": "खरेदीदार"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "title_warranty",
      "witness_attestation"
    ]
  },
  "house_sale_deed_mr": {
    "manifest_schema": 1,
    "template_id": "house_sale_deed_mr",
    "name_en": "Deed of Absolute Sale (Residential House / Bungalow)",
    "name_mr": "घर / इमारत खरेदीखत",
    "version": 1,
    "status": "draft",
    "document_type": "sale_deed",
    "property_type": "residential",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "sellers": {
        "role": "seller",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Seller(s) / Vendor(s)",
        "label_mr": "विक्रेता"
      },
      "purchasers": {
        "role": "purchaser",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Purchaser(s)",
        "label_mr": "खरेदीदार"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "title_warranty",
      "witness_attestation"
    ]
  },
  "irrevocable_poa_en": {
    "manifest_schema": 1,
    "template_id": "irrevocable_poa_en",
    "name_en": "Irrevocable Power of Attorney (Coupled with Interest)",
    "name_mr": "अपरिवर्तनीय कुलमुखत्यारपत्र (हितसंबंधयुक्त कुलमुखत्यार)",
    "version": 1,
    "status": "draft",
    "document_type": "special_poa",
    "property_type": "plot",
    "language": "en",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "principals": {
        "role": "principal",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Principal(s)",
        "label_mr": "अधिकार देणारे (मुख्य मालक)"
      },
      "attorneys": {
        "role": "attorney",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Irrevocable Attorney(s)",
        "label_mr": "अधिकार घेणारे (कुलमुखत्यार)"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "title_warranty",
      "witness_attestation"
    ]
  },
  "irrevocable_poa_mr": {
    "manifest_schema": 1,
    "template_id": "irrevocable_poa_mr",
    "name_en": "Irrevocable Power of Attorney (Coupled with Interest)",
    "name_mr": "अपरिवर्तनीय कुलमुखत्यारपत्र (हितसंबंधयुक्त कुलमुखत्यार)",
    "version": 1,
    "status": "draft",
    "document_type": "special_poa",
    "property_type": "plot",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "principals": {
        "role": "principal",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Principal(s)",
        "label_mr": "अधिकार देणारे (मुख्य मालक)"
      },
      "attorneys": {
        "role": "attorney",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Irrevocable Attorney(s)",
        "label_mr": "अधिकार घेणारे (कुलमुखत्यार)"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "title_warranty",
      "witness_attestation"
    ]
  },
  "leave_and_licence_en": {
    "manifest_schema": 1,
    "template_id": "leave_and_licence_en",
    "name_en": "Leave and Licence Agreement (Residential)",
    "name_mr": "लिव्ह अँड लायसन्स करार (भाडेतत्वावर वापर परवाना)",
    "version": 1,
    "status": "draft",
    "document_type": "leave_and_licence",
    "property_type": "residential",
    "language": "en",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "licensors": {
        "role": "licensor",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Licensor(s)",
        "label_mr": "परवाना देणारे (लायसन्सर)"
      },
      "licensees": {
        "role": "licensee",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Licensee(s)",
        "label_mr": "परवाना घेणारे (लायसन्सदार)"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "leave_and_licence_mr": {
    "manifest_schema": 1,
    "template_id": "leave_and_licence_mr",
    "name_en": "Leave and Licence Agreement (Residential)",
    "name_mr": "लिव्ह अँड लायसन्स करार (भाडेतत्वावर वापर परवाना)",
    "version": 1,
    "status": "draft",
    "document_type": "leave_and_licence",
    "property_type": "residential",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "licensors": {
        "role": "licensor",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Licensor(s)",
        "label_mr": "परवाना देणारे (लायसन्सर)"
      },
      "licensees": {
        "role": "licensee",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Licensee(s)",
        "label_mr": "परवाना घेणारे (लायसन्सदार)"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "loan_security_document_en": {
    "manifest_schema": 1,
    "template_id": "loan_security_document_en",
    "name_en": "Loan Security and Personal Guarantee Document",
    "name_mr": "कर्ज सुरक्षा व हमी दस्तऐवज",
    "version": 1,
    "status": "draft",
    "document_type": "loan_security_document",
    "property_type": "general",
    "language": "en",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "borrowers": {
        "role": "borrower",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Borrower(s)",
        "label_mr": "मुख्य कर्जदार"
      },
      "guarantors": {
        "role": "guarantor",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Guarantor(s)",
        "label_mr": "जामीनदार (हमीदार)"
      },
      "lenders": {
        "role": "lender",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Lender(s)",
        "label_mr": "कर्जदाते / वित्तीय संस्था"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "agreement_terms",
        "title_en": "Agreement Terms",
        "title_mr": "कराराच्या अटी व तपशील",
        "field_names": [
          "execution_date"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "loan_security_document_mr": {
    "manifest_schema": 1,
    "template_id": "loan_security_document_mr",
    "name_en": "Loan Security and Personal Guarantee Document",
    "name_mr": "कर्ज सुरक्षा व हमी दस्तऐवज",
    "version": 1,
    "status": "draft",
    "document_type": "loan_security_document",
    "property_type": "general",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "borrowers": {
        "role": "borrower",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Borrower(s)",
        "label_mr": "मुख्य कर्जदार"
      },
      "guarantors": {
        "role": "guarantor",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Guarantor(s)",
        "label_mr": "जामीनदार (हमीदार)"
      },
      "lenders": {
        "role": "lender",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Lender(s)",
        "label_mr": "कर्जदाते / वित्तीय संस्था"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "agreement_terms",
        "title_en": "Agreement Terms",
        "title_mr": "कराराच्या अटी व तपशील",
        "field_names": [
          "execution_date"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "memorandum_of_deposit_of_title_deeds_en": {
    "manifest_schema": 1,
    "template_id": "memorandum_of_deposit_of_title_deeds_en",
    "name_en": "Memorandum of Deposit of Title Deeds (Equitable Mortgage)",
    "name_mr": "दस्तऐवज ठेव स्मरणपत्र (समभावी गहाण / MODTD)",
    "version": 1,
    "status": "draft",
    "document_type": "mortgage_deed",
    "property_type": "plot",
    "language": "en",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "borrowers": {
        "role": "borrower",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Borrower(s) / Depositor(s)",
        "label_mr": "कर्जदार / दस्त ठेव देणारे"
      },
      "lenders": {
        "role": "lender",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Lender Bank / Financial Institution",
        "label_mr": "बँक / कर्ज संस्था (दस्त स्वीकारणारे)"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "title_warranty",
      "witness_attestation"
    ]
  },
  "memorandum_of_deposit_of_title_deeds_mr": {
    "manifest_schema": 1,
    "template_id": "memorandum_of_deposit_of_title_deeds_mr",
    "name_en": "Memorandum of Deposit of Title Deeds (Equitable Mortgage)",
    "name_mr": "दस्तऐवज ठेव स्मरणपत्र (समभावी गहाण / MODTD)",
    "version": 1,
    "status": "draft",
    "document_type": "mortgage_deed",
    "property_type": "plot",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "borrowers": {
        "role": "borrower",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Borrower(s) / Depositor(s)",
        "label_mr": "कर्जदार / दस्त ठेव देणारे"
      },
      "lenders": {
        "role": "lender",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Lender Bank / Financial Institution",
        "label_mr": "बँक / कर्ज संस्था (दस्त स्वीकारणारे)"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "title_warranty",
      "witness_attestation"
    ]
  },
  "mortgage_agreement_en": {
    "manifest_schema": 1,
    "template_id": "mortgage_agreement_en",
    "name_en": "Mortgage Agreement and Loan Covenant",
    "name_mr": "गहाण करारनामा (कर्ज व गहाण शर्ती करार)",
    "version": 1,
    "status": "draft",
    "document_type": "mortgage_deed",
    "property_type": "plot",
    "language": "en",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "mortgagors": {
        "role": "mortgagor",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Mortgagor(s)",
        "label_mr": "गहाण देणारे"
      },
      "mortgagees": {
        "role": "mortgagee",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Mortgagee(s)",
        "label_mr": "गहाण घेणारे"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "title_warranty",
      "witness_attestation"
    ]
  },
  "mortgage_agreement_mr": {
    "manifest_schema": 1,
    "template_id": "mortgage_agreement_mr",
    "name_en": "Mortgage Agreement and Loan Covenant",
    "name_mr": "गहाण करारनामा (कर्ज व गहाण शर्ती करार)",
    "version": 1,
    "status": "draft",
    "document_type": "mortgage_deed",
    "property_type": "plot",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "mortgagors": {
        "role": "mortgagor",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Mortgagor(s)",
        "label_mr": "गहाण देणारे"
      },
      "mortgagees": {
        "role": "mortgagee",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Mortgagee(s)",
        "label_mr": "गहाण घेणारे"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "title_warranty",
      "witness_attestation"
    ]
  },
  "mortgage_deed_en": {
    "manifest_schema": 1,
    "template_id": "mortgage_deed_en",
    "name_en": "Deed of Mortgage (Immoveable Property)",
    "name_mr": "गहाणखत (कर्ज सुरक्षिततेसाठी मिळकत गहाण)",
    "version": 1,
    "status": "draft",
    "document_type": "mortgage_deed",
    "property_type": "plot",
    "language": "en",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "mortgagors": {
        "role": "mortgagor",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Mortgagor(s) / Borrower(s)",
        "label_mr": "गहाण देणारे (कर्जदार)"
      },
      "mortgagees": {
        "role": "mortgagee",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Mortgagee(s) / Lender(s)",
        "label_mr": "गहाण घेणारे (सावकार / बँक)"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "title_warranty",
      "witness_attestation"
    ]
  },
  "mortgage_deed_mr": {
    "manifest_schema": 1,
    "template_id": "mortgage_deed_mr",
    "name_en": "Deed of Mortgage (Immoveable Property)",
    "name_mr": "गहाणखत (कर्ज सुरक्षिततेसाठी मिळकत गहाण)",
    "version": 1,
    "status": "draft",
    "document_type": "mortgage_deed",
    "property_type": "plot",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "mortgagors": {
        "role": "mortgagor",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Mortgagor(s) / Borrower(s)",
        "label_mr": "गहाण देणारे (कर्जदार)"
      },
      "mortgagees": {
        "role": "mortgagee",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Mortgagee(s) / Lender(s)",
        "label_mr": "गहाण घेणारे (सावकार / बँक)"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "title_warranty",
      "witness_attestation"
    ]
  },
  "possession_letter_en": {
    "manifest_schema": 1,
    "template_id": "possession_letter_en",
    "name_en": "Possession Letter (Physical Handover of Unit)",
    "name_mr": "ताबा पत्र (प्रत्यक्ष ताबा सुपूर्द पत्र)",
    "version": 1,
    "status": "draft",
    "document_type": "possession_letter",
    "property_type": "flat",
    "language": "en",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "deliverers": {
        "role": "deliverer",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Possession Deliverer(s)",
        "label_mr": "ताबा देणारे (हस्तांतरक)"
      },
      "recipients": {
        "role": "recipient",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Possession Recipient(s)",
        "label_mr": "ताबा घेणारे (स्वीकारणारे)"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "possession_letter_mr": {
    "manifest_schema": 1,
    "template_id": "possession_letter_mr",
    "name_en": "Possession Letter (Physical Handover of Unit)",
    "name_mr": "ताबा पत्र (प्रत्यक्ष ताबा सुपूर्द पत्र)",
    "version": 1,
    "status": "draft",
    "document_type": "possession_letter",
    "property_type": "flat",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "deliverers": {
        "role": "deliverer",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Possession Deliverer(s)",
        "label_mr": "ताबा देणारे (हस्तांतरक)"
      },
      "recipients": {
        "role": "recipient",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Possession Recipient(s)",
        "label_mr": "ताबा घेणारे (स्वीकारणारे)"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "possession_receipt_en": {
    "manifest_schema": 1,
    "template_id": "possession_receipt_en",
    "name_en": "Possession Receipt (Acknowledgment of Delivery)",
    "name_mr": "ताबा पावती (कब्जा पोचपावती)",
    "version": 1,
    "status": "draft",
    "document_type": "possession_receipt",
    "property_type": "flat",
    "language": "en",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "recipients": {
        "role": "recipient",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Possession Acknowledger(s)",
        "label_mr": "ताबा स्वीकारणारे"
      },
      "deliverers": {
        "role": "deliverer",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Possession Handover Party",
        "label_mr": "ताबा देणारे"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "possession_receipt_mr": {
    "manifest_schema": 1,
    "template_id": "possession_receipt_mr",
    "name_en": "Possession Receipt (Acknowledgment of Delivery)",
    "name_mr": "ताबा पावती (कब्जा पोचपावती)",
    "version": 1,
    "status": "draft",
    "document_type": "possession_receipt",
    "property_type": "flat",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "recipients": {
        "role": "recipient",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Possession Acknowledger(s)",
        "label_mr": "ताबा स्वीकारणारे"
      },
      "deliverers": {
        "role": "deliverer",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Possession Handover Party",
        "label_mr": "ताबा देणारे"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "property_distribution_agreement_en": {
    "manifest_schema": 1,
    "template_id": "property_distribution_agreement_en",
    "name_en": "Property Distribution Agreement (Co-owners)",
    "name_mr": "मिळकत वाटप करारनामा",
    "version": 1,
    "status": "draft",
    "document_type": "property_distribution_agreement",
    "property_type": "plot",
    "language": "en",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "first_sharers": {
        "role": "co_owner_1",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "First Co-owner",
        "label_mr": "प्रथम सहमालक"
      },
      "second_sharers": {
        "role": "co_owner_2",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Second Co-owner",
        "label_mr": "द्वितीय सहमालक"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "property_distribution_agreement_mr": {
    "manifest_schema": 1,
    "template_id": "property_distribution_agreement_mr",
    "name_en": "Property Distribution Agreement (Co-owners)",
    "name_mr": "मिळकत वाटप करारनामा",
    "version": 1,
    "status": "draft",
    "document_type": "property_distribution_agreement",
    "property_type": "plot",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "first_sharers": {
        "role": "co_owner_1",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "First Co-owner",
        "label_mr": "प्रथम सहमालक"
      },
      "second_sharers": {
        "role": "co_owner_2",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Second Co-owner",
        "label_mr": "द्वितीय सहमालक"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "property_handover_en": {
    "manifest_schema": 1,
    "template_id": "property_handover_en",
    "name_en": "Property Handover Memorandum",
    "name_mr": "मिळकत सुपूर्द पत्र (जागा हस्तांतरण व ताबा)",
    "version": 1,
    "status": "draft",
    "document_type": "property_handover",
    "property_type": "commercial_unit",
    "language": "en",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "handover_parties": {
        "role": "handover_party",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Handover Party",
        "label_mr": "सुपूर्द करणारे"
      },
      "takeover_parties": {
        "role": "takeover_party",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Takeover Party",
        "label_mr": "स्वीकारणारे"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "property_handover_mr": {
    "manifest_schema": 1,
    "template_id": "property_handover_mr",
    "name_en": "Property Handover Memorandum",
    "name_mr": "मिळकत सुपूर्द पत्र (जागा हस्तांतरण व ताबा)",
    "version": 1,
    "status": "draft",
    "document_type": "property_handover",
    "property_type": "commercial_unit",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "handover_parties": {
        "role": "handover_party",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Handover Party",
        "label_mr": "सुपूर्द करणारे"
      },
      "takeover_parties": {
        "role": "takeover_party",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Takeover Party",
        "label_mr": "स्वीकारणारे"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "property_rights_declaration_en": {
    "manifest_schema": 1,
    "template_id": "property_rights_declaration_en",
    "name_en": "Declaration of Property Rights and Title",
    "name_mr": "मिळकत हक्क घोषणापत्र (प्रतिज्ञापत्र / जाहीरनामा)",
    "version": 1,
    "status": "draft",
    "document_type": "property_rights_declaration",
    "property_type": "plot",
    "language": "en",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "declarants": {
        "role": "declarant",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Declarant(s)",
        "label_mr": "घोषणा करणारे (प्रतिज्ञाकर्ते)"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "property_rights_declaration_mr": {
    "manifest_schema": 1,
    "template_id": "property_rights_declaration_mr",
    "name_en": "Declaration of Property Rights and Title",
    "name_mr": "मिळकत हक्क घोषणापत्र (प्रतिज्ञापत्र / जाहीरनामा)",
    "version": 1,
    "status": "draft",
    "document_type": "property_rights_declaration",
    "property_type": "plot",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "declarants": {
        "role": "declarant",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Declarant(s)",
        "label_mr": "घोषणा करणारे (प्रतिज्ञाकर्ते)"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "release_deed_hi": {
    "manifest_schema": 1,
    "template_id": "release_deed_hi",
    "name_en": "Deed of Release / Relinquishment of Undivided Share",
    "name_mr": "हक त्याग विलेख (रिलीज़ डीड)",
    "version": 1,
    "status": "draft",
    "document_type": "release_deed",
    "property_type": "plot",
    "language": "hi",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "releasors": {
        "role": "releasor",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Releasor(s)",
        "label_mr": "हक त्यागकर्ता"
      },
      "releasees": {
        "role": "releasee",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Releasee(s)",
        "label_mr": "हक ग्राहिता"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन व सोडलेला हिस्सा",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.plot_no",
          "property.area_sqm",
          "property.relinquished_share"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      },
      {
        "id": "financial_terms",
        "title_en": "Terms of Relinquishment",
        "title_mr": "हक्कसोड अटी व मोबदला",
        "field_names": [
          "financial.is_without_consideration",
          "financial.consideration_amount"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.plot_no": {
        "name": "property.plot_no",
        "type": "string",
        "label_en": "Plot No.",
        "label_mr": "प्लॉट क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Total Area (sq.m.)",
        "label_mr": "एकूण क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "property.relinquished_share": {
        "name": "property.relinquished_share",
        "type": "string",
        "label_en": "Relinquished Share Fraction",
        "label_mr": "सोडण्यात येणारा अविभाज्य हिस्सा",
        "required": true
      },
      "financial.is_without_consideration": {
        "name": "financial.is_without_consideration",
        "type": "boolean",
        "label_en": "Relinquished Without Consideration (Natural Love/Affection)",
        "label_mr": "विना मोबदला (खाजगी प्रेमाखातर / रक्ताच्या नात्यापोटी)",
        "required": true,
        "default": true
      },
      "financial.consideration_amount": {
        "name": "financial.consideration_amount",
        "type": "decimal",
        "label_en": "Consideration Amount (if any)",
        "label_mr": "मोबदला रक्कम (असल्यास)",
        "required": false,
        "default": 0
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      },
      "witness_1": {
        "name": "witness_1",
        "type": "string",
        "label_en": "First Attesting Witness",
        "label_mr": "पहिला साक्षीदार",
        "required": true
      },
      "witness_2": {
        "name": "witness_2",
        "type": "string",
        "label_en": "Second Attesting Witness",
        "label_mr": "दुसरा साक्षीदार",
        "required": true
      }
    }
  },
  "release_deed_mr": {
    "manifest_schema": 1,
    "template_id": "release_deed_mr",
    "name_en": "Release Deed / Relinquishment Deed (Marathi)",
    "name_mr": "हक्कसोड पत्र (सहहिस्सा / वारसाहक्क)",
    "version": 1,
    "status": "draft",
    "document_type": "release_deed",
    "property_type": "plot",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "releasors": {
        "role": "releasor",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Releasor(s) / Person Relinquishing Share",
        "label_mr": "हक्क सोडणारे (सहहिस्सेदार)"
      },
      "releasees": {
        "role": "releasee",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Releasee(s) / Person Accepting Relinquished Share",
        "label_mr": "हक्क घेणारे (सहहिस्सेदार)"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन व सोडलेला हिस्सा",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.plot_no",
          "property.area_sqm",
          "property.relinquished_share"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      },
      {
        "id": "financial_terms",
        "title_en": "Terms of Relinquishment",
        "title_mr": "हक्कसोड अटी व मोबदला",
        "field_names": [
          "financial.is_without_consideration",
          "financial.consideration_amount"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.plot_no": {
        "name": "property.plot_no",
        "type": "string",
        "label_en": "Plot No.",
        "label_mr": "प्लॉट क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Total Area (sq.m.)",
        "label_mr": "एकूण क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "property.relinquished_share": {
        "name": "property.relinquished_share",
        "type": "string",
        "label_en": "Relinquished Share Fraction",
        "label_mr": "सोडण्यात येणारा अविभाज्य हिस्सा",
        "required": true
      },
      "financial.is_without_consideration": {
        "name": "financial.is_without_consideration",
        "type": "boolean",
        "label_en": "Relinquished Without Consideration (Natural Love/Affection)",
        "label_mr": "विना मोबदला (खाजगी प्रेमाखातर / रक्ताच्या नात्यापोटी)",
        "required": true,
        "default": true
      },
      "financial.consideration_amount": {
        "name": "financial.consideration_amount",
        "type": "decimal",
        "label_en": "Consideration Amount (if any)",
        "label_mr": "मोबदला रक्कम (असल्यास)",
        "required": false,
        "default": 0
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      },
      "witness_1": {
        "name": "witness_1",
        "type": "string",
        "label_en": "First Attesting Witness",
        "label_mr": "पहिला साक्षीदार",
        "required": true
      },
      "witness_2": {
        "name": "witness_2",
        "type": "string",
        "label_en": "Second Attesting Witness",
        "label_mr": "दुसरा साक्षीदार",
        "required": true
      }
    }
  },
  "rent_commercial_en": {
    "manifest_schema": 1,
    "template_id": "rent_commercial_en",
    "name_en": "Commercial Premises Lease Agreement",
    "name_mr": "व्यावसायिक जागा भाडेपट्टा करार",
    "version": 1,
    "status": "draft",
    "document_type": "rent_commercial",
    "property_type": "commercial_unit",
    "language": "en",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "lessors": {
        "role": "lessor",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Lessor(s)",
        "label_mr": "भाडेपट्टा देणारे (जागा मालक)"
      },
      "lessees": {
        "role": "lessee",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Lessee(s)",
        "label_mr": "भाडेपट्टा घेणारे (कंपनी / संस्था)"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "rent_commercial_mr": {
    "manifest_schema": 1,
    "template_id": "rent_commercial_mr",
    "name_en": "Commercial Premises Lease Agreement",
    "name_mr": "व्यावसायिक जागा भाडेपट्टा करार",
    "version": 1,
    "status": "draft",
    "document_type": "rent_commercial",
    "property_type": "commercial_unit",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "lessors": {
        "role": "lessor",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Lessor(s)",
        "label_mr": "भाडेपट्टा देणारे (जागा मालक)"
      },
      "lessees": {
        "role": "lessee",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Lessee(s)",
        "label_mr": "भाडेपट्टा घेणारे (कंपनी / संस्था)"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "rent_residential_en": {
    "manifest_schema": 1,
    "template_id": "rent_residential_en",
    "name_en": "Residential Tenancy Agreement",
    "name_mr": "निवासी भाडेकरारनामा",
    "version": 1,
    "status": "draft",
    "document_type": "rent_residential",
    "property_type": "residential",
    "language": "en",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "landlords": {
        "role": "landlord",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Landlord(s)",
        "label_mr": "घरमालक"
      },
      "tenants": {
        "role": "tenant",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Tenant(s)",
        "label_mr": "भाडेकरू"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "rent_residential_mr": {
    "manifest_schema": 1,
    "template_id": "rent_residential_mr",
    "name_en": "Residential Tenancy Agreement",
    "name_mr": "निवासी भाडेकरारनामा",
    "version": 1,
    "status": "draft",
    "document_type": "rent_residential",
    "property_type": "residential",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "landlords": {
        "role": "landlord",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Landlord(s)",
        "label_mr": "घरमालक"
      },
      "tenants": {
        "role": "tenant",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Tenant(s)",
        "label_mr": "भाडेकरू"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "rent_shop_en": {
    "manifest_schema": 1,
    "template_id": "rent_shop_en",
    "name_en": "Commercial Shop Tenancy Agreement",
    "name_mr": "दुकान भाडेकरारनामा (व्यावसायिक गाळा भाडेकरार)",
    "version": 1,
    "status": "draft",
    "document_type": "rent_shop",
    "property_type": "shop",
    "language": "en",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "landlords": {
        "role": "landlord",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Landlord(s) / Shop Owner(s)",
        "label_mr": "दुकान मालक"
      },
      "tenants": {
        "role": "tenant",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Tenant(s) / Shopkeeper",
        "label_mr": "भाडेकरू (दुकानदार)"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "rent_shop_mr": {
    "manifest_schema": 1,
    "template_id": "rent_shop_mr",
    "name_en": "Commercial Shop Tenancy Agreement",
    "name_mr": "दुकान भाडेकरारनामा (व्यावसायिक गाळा भाडेकरार)",
    "version": 1,
    "status": "draft",
    "document_type": "rent_shop",
    "property_type": "shop",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "landlords": {
        "role": "landlord",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Landlord(s) / Shop Owner(s)",
        "label_mr": "दुकान मालक"
      },
      "tenants": {
        "role": "tenant",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Tenant(s) / Shopkeeper",
        "label_mr": "भाडेकरू (दुकानदार)"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "rights_transfer_en": {
    "manifest_schema": 1,
    "template_id": "rights_transfer_en",
    "name_en": "Assignment and Transfer of Rights Deed",
    "name_mr": "हक्क हस्तांतरण पत्र (करार व वाटप हक्क अभिहस्तांतरण)",
    "version": 1,
    "status": "draft",
    "document_type": "rights_transfer",
    "property_type": "flat",
    "language": "en",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "assignors": {
        "role": "assignor",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Assignor(s)",
        "label_mr": "हक्क अभिहस्तांतरक"
      },
      "assignees": {
        "role": "assignee",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Assignee(s)",
        "label_mr": "हक्क अभिहस्तांतरिती"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "title_warranty",
      "witness_attestation"
    ]
  },
  "rights_transfer_mr": {
    "manifest_schema": 1,
    "template_id": "rights_transfer_mr",
    "name_en": "Assignment and Transfer of Rights Deed",
    "name_mr": "हक्क हस्तांतरण पत्र (करार व वाटप हक्क अभिहस्तांतरण)",
    "version": 1,
    "status": "draft",
    "document_type": "rights_transfer",
    "property_type": "flat",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "assignors": {
        "role": "assignor",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Assignor(s)",
        "label_mr": "हक्क अभिहस्तांतरक"
      },
      "assignees": {
        "role": "assignee",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Assignee(s)",
        "label_mr": "हक्क अभिहस्तांतरिती"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "title_warranty",
      "witness_attestation"
    ]
  },
  "sale_deed_agricultural_hi": {
    "manifest_schema": 1,
    "template_id": "sale_deed_agricultural_hi",
    "name_en": "Sale Deed (Agricultural Land)",
    "name_mr": "विक्रय विलेख (कृषि भूमि / शेतजमीन)",
    "version": 1,
    "status": "draft",
    "document_type": "sale_deed",
    "property_type": "agricultural",
    "language": "hi",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "sellers": {
        "role": "seller",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Seller(s)",
        "label_mr": "विक्रेता (कृषक)"
      },
      "purchasers": {
        "role": "purchaser",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Purchaser(s)",
        "label_mr": "क्रेता (कृषक)"
      }
    },
    "repeaters": {
      "instalments": {
        "name": "instalments",
        "min": 1,
        "max": 6,
        "label_en": "Payment Details",
        "label_mr": "धनादेश / आरटीजीएस तपशील"
      },
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "agricultural_schedule",
        "title_en": "Agricultural Land Schedule",
        "title_mr": "शेतजमिनीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.gat_khasra_no",
          "property.area_hectare_r",
          "property.potkharab_area",
          "property.assessment_tax",
          "property.irrigation_type"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      },
      {
        "id": "financial_details",
        "title_en": "Financial Consideration",
        "title_mr": "मोबदला व देय रक्कम",
        "field_names": [
          "financial.total_consideration",
          "financial.earnest_advance"
        ]
      }
    ],
    "fields": {
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza",
        "label_mr": "मौजे",
        "required": true
      },
      "property.gat_khasra_no": {
        "name": "property.gat_khasra_no",
        "type": "string",
        "label_en": "Gat / Khasra No.",
        "label_mr": "गट क्र. / खसरा क्र.",
        "required": true
      },
      "property.area_hectare_r": {
        "name": "property.area_hectare_r",
        "type": "string",
        "label_en": "Total Area (Hectare - R)",
        "label_mr": "एकूण क्षेत्र (हेक्टर-आर)",
        "required": true
      },
      "property.potkharab_area": {
        "name": "property.potkharab_area",
        "type": "string",
        "label_en": "Potkharab Area",
        "label_mr": "पोटखराब क्षेत्र",
        "required": false,
        "default": "निरंक"
      },
      "property.assessment_tax": {
        "name": "property.assessment_tax",
        "type": "string",
        "label_en": "Land Revenue / Akar",
        "label_mr": "आकारणी (रुपये)",
        "required": false
      },
      "property.irrigation_type": {
        "name": "property.irrigation_type",
        "type": "string",
        "label_en": "Irrigation Type (Jirayat / Bagayat)",
        "label_mr": "जमिनीचा प्रकार (जिरायत / बागायत)",
        "required": true,
        "default": "जिरायत (कोरडवाहू)"
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South",
        "label_mr": "दक्षिण",
        "required": true
      },
      "financial.total_consideration": {
        "name": "financial.total_consideration",
        "type": "decimal",
        "label_en": "Total Consideration (Rs.)",
        "label_mr": "एकूण ठरलेला मोबदला (रु.)",
        "required": true
      },
      "financial.earnest_advance": {
        "name": "financial.earnest_advance",
        "type": "decimal",
        "label_en": "Earnest / Advance Amount (Rs.)",
        "label_mr": "इसार / आगाऊ रक्कम (रु.)",
        "required": true
      },
      "execution_date": {
        "name": "execution_date",
        "type": "date",
        "label_en": "Execution Date",
        "label_mr": "दस्त निष्पादनाची तारीख",
        "required": true
      }
    },
    "derived_fields": {
      "financial.balance_amount": {
        "name": "financial.balance_amount",
        "type": "decimal",
        "expression": "financial.total_consideration - financial.earnest_advance",
        "label_en": "Balance Amount",
        "label_mr": "शिल्लक मोबदला रक्कम"
      }
    },
    "validations": [
      {
        "id": "earnest_le_total",
        "condition": "financial.earnest_advance <= financial.total_consideration",
        "message_en": "Earnest money cannot exceed total consideration",
        "message_mr": "इसार रक्कम एकूण मोबदल्यापेक्षा जास्त असू शकत नाही",
        "severity": "error"
      },
      {
        "id": "total_gt_zero",
        "condition": "financial.total_consideration > 0",
        "message_en": "Total consideration must be greater than zero",
        "message_mr": "एकूण मोबदला शून्यापेक्षा जास्त असणे आवश्यक आहे",
        "severity": "error"
      }
    ]
  },
  "sale_deed_agricultural_mr": {
    "manifest_schema": 1,
    "template_id": "sale_deed_agricultural_mr",
    "name_en": "Sale Deed (Agricultural Land in Marathi)",
    "name_mr": "खरेदीखत (शेती जमीन / शेतजमीन)",
    "version": 1,
    "status": "draft",
    "document_type": "sale_deed",
    "property_type": "agricultural",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "sellers": {
        "role": "seller",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Seller(s)",
        "label_mr": "विक्रेता / शेतकरी"
      },
      "purchasers": {
        "role": "purchaser",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Purchaser(s)",
        "label_mr": "खरेदीदार"
      }
    },
    "repeaters": {
      "instalments": {
        "name": "instalments",
        "min": 1,
        "max": 6,
        "label_en": "Payment Details",
        "label_mr": "धनादेश / आरटीजीएस तपशील"
      },
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "agricultural_schedule",
        "title_en": "Agricultural Land Schedule",
        "title_mr": "शेतजमिनीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.gat_khasra_no",
          "property.area_hectare_r",
          "property.potkharab_area",
          "property.assessment_tax",
          "property.irrigation_type"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      },
      {
        "id": "financial_details",
        "title_en": "Financial Consideration",
        "title_mr": "मोबदला व देय रक्कम",
        "field_names": [
          "financial.total_consideration",
          "financial.earnest_advance"
        ]
      }
    ],
    "fields": {
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza",
        "label_mr": "मौजे",
        "required": true
      },
      "property.gat_khasra_no": {
        "name": "property.gat_khasra_no",
        "type": "string",
        "label_en": "Gat / Khasra No.",
        "label_mr": "गट क्र. / खसरा क्र.",
        "required": true
      },
      "property.area_hectare_r": {
        "name": "property.area_hectare_r",
        "type": "string",
        "label_en": "Total Area (Hectare - R)",
        "label_mr": "एकूण क्षेत्र (हेक्टर-आर)",
        "required": true
      },
      "property.potkharab_area": {
        "name": "property.potkharab_area",
        "type": "string",
        "label_en": "Potkharab Area",
        "label_mr": "पोटखराब क्षेत्र",
        "required": false,
        "default": "निरंक"
      },
      "property.assessment_tax": {
        "name": "property.assessment_tax",
        "type": "string",
        "label_en": "Land Revenue / Akar",
        "label_mr": "आकारणी (रुपये)",
        "required": false
      },
      "property.irrigation_type": {
        "name": "property.irrigation_type",
        "type": "string",
        "label_en": "Irrigation Type (Jirayat / Bagayat)",
        "label_mr": "जमिनीचा प्रकार (जिरायत / बागायत)",
        "required": true,
        "default": "जिरायत (कोरडवाहू)"
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South",
        "label_mr": "दक्षिण",
        "required": true
      },
      "financial.total_consideration": {
        "name": "financial.total_consideration",
        "type": "decimal",
        "label_en": "Total Consideration (Rs.)",
        "label_mr": "एकूण ठरलेला मोबदला (रु.)",
        "required": true
      },
      "financial.earnest_advance": {
        "name": "financial.earnest_advance",
        "type": "decimal",
        "label_en": "Earnest / Advance Amount (Rs.)",
        "label_mr": "इसार / आगाऊ रक्कम (रु.)",
        "required": true
      },
      "execution_date": {
        "name": "execution_date",
        "type": "date",
        "label_en": "Execution Date",
        "label_mr": "दस्त निष्पादनाची तारीख",
        "required": true
      }
    },
    "derived_fields": {
      "financial.balance_amount": {
        "name": "financial.balance_amount",
        "type": "decimal",
        "expression": "financial.total_consideration - financial.earnest_advance",
        "label_en": "Balance Amount",
        "label_mr": "शिल्लक मोबदला रक्कम"
      }
    },
    "validations": [
      {
        "id": "earnest_le_total",
        "condition": "financial.earnest_advance <= financial.total_consideration",
        "message_en": "Earnest money cannot exceed total consideration",
        "message_mr": "इसार रक्कम एकूण मोबदल्यापेक्षा जास्त असू शकत नाही",
        "severity": "error"
      },
      {
        "id": "total_gt_zero",
        "condition": "financial.total_consideration > 0",
        "message_en": "Total consideration must be greater than zero",
        "message_mr": "एकूण मोबदला शून्यापेक्षा जास्त असणे आवश्यक आहे",
        "severity": "error"
      }
    ]
  },
  "sale_deed_flat_en": {
    "manifest_schema": 1,
    "template_id": "sale_deed_flat_en",
    "name_en": "Deed of Absolute Sale (Flat / Apartment)",
    "name_mr": "खरेदीखत - फ्लॅट / सदनिका (इंग्रजी)",
    "version": 1,
    "status": "draft",
    "document_type": "sale_deed",
    "property_type": "flat",
    "language": "en",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "vendors": {
        "role": "vendor",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Vendor / Seller(s)",
        "label_mr": "विक्रेता"
      },
      "purchasers": {
        "role": "purchaser",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Purchaser(s)",
        "label_mr": "खरेदीदार"
      }
    },
    "repeaters": {
      "instalments": {
        "name": "instalments",
        "min": 1,
        "max": 6,
        "label_en": "Payment Cheque / RTGS Details",
        "label_mr": "धनादेश / आरटीजीएस तपशील"
      },
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "apartment_schedule",
        "title_en": "Apartment / Flat Schedule",
        "title_mr": "फ्लॅटचा तपशील",
        "field_names": [
          "property.flat_no",
          "property.floor_no",
          "property.building_name",
          "property.locality",
          "property.city",
          "property.survey_no",
          "property.carpet_area_sqm",
          "property.parking_no"
        ]
      },
      {
        "id": "financial_terms",
        "title_en": "Sale Consideration & Payment",
        "title_mr": "मोबदला व देय रक्कम",
        "field_names": [
          "financial.total_price",
          "financial.advance_paid"
        ]
      }
    ],
    "fields": {
      "property.flat_no": {
        "name": "property.flat_no",
        "type": "string",
        "label_en": "Flat / Unit No.",
        "label_mr": "फ्लॅट क्र.",
        "required": true
      },
      "property.floor_no": {
        "name": "property.floor_no",
        "type": "string",
        "label_en": "Floor No.",
        "label_mr": "मजला",
        "required": true
      },
      "property.building_name": {
        "name": "property.building_name",
        "type": "string",
        "label_en": "Building / Apartment Name",
        "label_mr": "इमारतीचे नाव",
        "required": true
      },
      "property.locality": {
        "name": "property.locality",
        "type": "string",
        "label_en": "Locality / Mouza",
        "label_mr": "परिसर / मौजे",
        "required": true
      },
      "property.city": {
        "name": "property.city",
        "type": "string",
        "label_en": "City",
        "label_mr": "शहर",
        "required": true,
        "default": "Nagpur"
      },
      "property.survey_no": {
        "name": "property.survey_no",
        "type": "string",
        "label_en": "City Survey / Khasra No.",
        "label_mr": "सर्व्हे / खसरा क्र.",
        "required": true
      },
      "property.carpet_area_sqm": {
        "name": "property.carpet_area_sqm",
        "type": "decimal",
        "label_en": "Carpet Area (Sq. Metres)",
        "label_mr": "कार्पेट क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "property.parking_no": {
        "name": "property.parking_no",
        "type": "string",
        "label_en": "Covered / Open Parking Space No.",
        "label_mr": "पार्किंग क्र.",
        "required": false
      },
      "financial.total_price": {
        "name": "financial.total_price",
        "type": "decimal",
        "label_en": "Total Sale Consideration (Rs.)",
        "label_mr": "एकूण विक्री मोबदला (रु.)",
        "required": true
      },
      "financial.advance_paid": {
        "name": "financial.advance_paid",
        "type": "decimal",
        "label_en": "Earnest / Advance Amount Paid (Rs.)",
        "label_mr": "आगाऊ मिळालेली रक्कम (रु.)",
        "required": true
      },
      "execution_date": {
        "name": "execution_date",
        "type": "date",
        "label_en": "Date of Execution",
        "label_mr": "दस्त निष्पादनाची तारीख",
        "required": true
      }
    },
    "derived_fields": {
      "financial.balance_amount": {
        "name": "financial.balance_amount",
        "type": "decimal",
        "expression": "financial.total_price - financial.advance_paid",
        "label_en": "Balance Sale Consideration",
        "label_mr": "शिल्लक देय रक्कम"
      },
      "property.carpet_area_sqft": {
        "name": "property.carpet_area_sqft",
        "type": "decimal",
        "expression": "property.carpet_area_sqm * 10.7639104",
        "label_en": "Carpet Area (Sq. Feet)",
        "label_mr": "कार्पेट क्षेत्रफळ (चौ.फूट)"
      }
    },
    "validations": [
      {
        "id": "advance_le_total",
        "condition": "financial.advance_paid <= financial.total_price",
        "message_en": "Advance amount cannot exceed total sale consideration",
        "message_mr": "आगाऊ रक्कम एकूण मोबदल्यापेक्षा जास्त असू शकत नाही",
        "severity": "error"
      },
      {
        "id": "total_gt_zero",
        "condition": "financial.total_price > 0",
        "message_en": "Total sale consideration must be greater than zero",
        "message_mr": "एकूण मोबदला शून्यापेक्षा जास्त असणे आवश्यक आहे",
        "severity": "error"
      }
    ]
  },
  "sale_deed_flat_hi": {
    "manifest_schema": 1,
    "template_id": "sale_deed_flat_hi",
    "name_en": "Sale Deed (Residential Flat / Apartment)",
    "name_mr": "विक्रय विलेख (सदनिका / आवासीय फ्लैट)",
    "version": 1,
    "status": "draft",
    "document_type": "sale_deed",
    "property_type": "flat",
    "language": "hi",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "sellers": {
        "role": "seller",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Seller(s)",
        "label_mr": "विक्रेता"
      },
      "purchasers": {
        "role": "purchaser",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Purchaser(s)",
        "label_mr": "क्रेता"
      }
    },
    "repeaters": {
      "instalments": {
        "name": "instalments",
        "min": 1,
        "max": 6,
        "label_en": "Instalment Details",
        "label_mr": "हप्ता / धनादेश तपशील"
      },
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "apartment_schedule",
        "title_en": "Apartment / Flat Schedule",
        "title_mr": "सदनिकेचे वर्णन",
        "field_names": [
          "property.flat_no",
          "property.floor_no",
          "property.building_name",
          "property.mouza",
          "property.khasra_no",
          "property.sheet_no",
          "property.carpet_area_sqm",
          "property.parking_no"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Flat Boundaries",
        "title_mr": "सदनिकेची चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      },
      {
        "id": "financial_details",
        "title_en": "Financial Consideration",
        "title_mr": "मोबदला व देय रक्कम",
        "field_names": [
          "financial.total_consideration",
          "financial.earnest_advance"
        ]
      }
    ],
    "fields": {
      "property.flat_no": {
        "name": "property.flat_no",
        "type": "string",
        "label_en": "Flat No.",
        "label_mr": "सदनिका / फ्लॅट क्र.",
        "required": true
      },
      "property.floor_no": {
        "name": "property.floor_no",
        "type": "string",
        "label_en": "Floor No.",
        "label_mr": "मजला क्र.",
        "required": true
      },
      "property.building_name": {
        "name": "property.building_name",
        "type": "string",
        "label_en": "Building Name",
        "label_mr": "इमारतीचे नाव",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.sheet_no": {
        "name": "property.sheet_no",
        "type": "string",
        "label_en": "City Survey Sheet No.",
        "label_mr": "नगर भूमापन शीट क्र.",
        "required": false
      },
      "property.carpet_area_sqm": {
        "name": "property.carpet_area_sqm",
        "type": "decimal",
        "label_en": "Carpet Area (Sq. Metres)",
        "label_mr": "कार्पेट क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "property.parking_no": {
        "name": "property.parking_no",
        "type": "string",
        "label_en": "Parking Space No.",
        "label_mr": "पार्किंग क्र.",
        "required": false
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South",
        "label_mr": "दक्षिण",
        "required": true
      },
      "financial.total_consideration": {
        "name": "financial.total_consideration",
        "type": "decimal",
        "label_en": "Total Consideration (Rs.)",
        "label_mr": "एकूण मोबदला (रु.)",
        "required": true
      },
      "financial.earnest_advance": {
        "name": "financial.earnest_advance",
        "type": "decimal",
        "label_en": "Earnest / Advance Amount (Rs.)",
        "label_mr": "इसार / आगाऊ रक्कम (रु.)",
        "required": true
      },
      "execution_date": {
        "name": "execution_date",
        "type": "date",
        "label_en": "Execution Date",
        "label_mr": "दस्त निष्पादनाची तारीख",
        "required": true
      }
    },
    "derived_fields": {
      "financial.balance_amount": {
        "name": "financial.balance_amount",
        "type": "decimal",
        "expression": "financial.total_consideration - financial.earnest_advance",
        "label_en": "Balance Amount",
        "label_mr": "शिल्लक मोबदला रक्कम"
      },
      "property.carpet_area_sqft": {
        "name": "property.carpet_area_sqft",
        "type": "decimal",
        "expression": "property.carpet_area_sqm * 10.7639104",
        "label_en": "Carpet Area (Sq. Feet)",
        "label_mr": "कार्पेट क्षेत्रफळ (चौ.फूट)"
      }
    },
    "validations": [
      {
        "id": "earnest_le_total",
        "condition": "financial.earnest_advance <= financial.total_consideration",
        "message_en": "Earnest money cannot exceed total consideration",
        "message_mr": "इसार रक्कम एकूण मोबदल्यापेक्षा जास्त असू शकत नाही",
        "severity": "error"
      },
      {
        "id": "total_gt_zero",
        "condition": "financial.total_consideration > 0",
        "message_en": "Total consideration must be greater than zero",
        "message_mr": "एकूण मोबदला शून्यापेक्षा जास्त असणे आवश्यक आहे",
        "severity": "error"
      }
    ]
  },
  "sale_deed_flat_mr": {
    "manifest_schema": 1,
    "template_id": "sale_deed_flat_mr",
    "name_en": "Sale Deed (Apartment / Flat in Marathi)",
    "name_mr": "खरेदीखत (सदनिका / फ्लॅट)",
    "version": 1,
    "status": "draft",
    "document_type": "sale_deed",
    "property_type": "flat",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "sellers": {
        "role": "seller",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Seller(s)",
        "label_mr": "विक्रेता"
      },
      "purchasers": {
        "role": "purchaser",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Purchaser(s)",
        "label_mr": "खरेदीदार"
      }
    },
    "repeaters": {
      "instalments": {
        "name": "instalments",
        "min": 1,
        "max": 6,
        "label_en": "Instalment Details",
        "label_mr": "हप्ता / धनादेश तपशील"
      },
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "apartment_schedule",
        "title_en": "Apartment / Flat Schedule",
        "title_mr": "सदनिकेचे वर्णन",
        "field_names": [
          "property.flat_no",
          "property.floor_no",
          "property.building_name",
          "property.mouza",
          "property.khasra_no",
          "property.sheet_no",
          "property.carpet_area_sqm",
          "property.parking_no"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Flat Boundaries",
        "title_mr": "सदनिकेची चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      },
      {
        "id": "financial_details",
        "title_en": "Financial Consideration",
        "title_mr": "मोबदला व देय रक्कम",
        "field_names": [
          "financial.total_consideration",
          "financial.earnest_advance"
        ]
      }
    ],
    "fields": {
      "property.flat_no": {
        "name": "property.flat_no",
        "type": "string",
        "label_en": "Flat No.",
        "label_mr": "सदनिका / फ्लॅट क्र.",
        "required": true
      },
      "property.floor_no": {
        "name": "property.floor_no",
        "type": "string",
        "label_en": "Floor No.",
        "label_mr": "मजला क्र.",
        "required": true
      },
      "property.building_name": {
        "name": "property.building_name",
        "type": "string",
        "label_en": "Building Name",
        "label_mr": "इमारतीचे नाव",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.sheet_no": {
        "name": "property.sheet_no",
        "type": "string",
        "label_en": "City Survey Sheet No.",
        "label_mr": "नगर भूमापन शीट क्र.",
        "required": false
      },
      "property.carpet_area_sqm": {
        "name": "property.carpet_area_sqm",
        "type": "decimal",
        "label_en": "Carpet Area (Sq. Metres)",
        "label_mr": "कार्पेट क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "property.parking_no": {
        "name": "property.parking_no",
        "type": "string",
        "label_en": "Parking Space No.",
        "label_mr": "पार्किंग क्र.",
        "required": false
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South",
        "label_mr": "दक्षिण",
        "required": true
      },
      "financial.total_consideration": {
        "name": "financial.total_consideration",
        "type": "decimal",
        "label_en": "Total Consideration (Rs.)",
        "label_mr": "एकूण मोबदला (रु.)",
        "required": true
      },
      "financial.earnest_advance": {
        "name": "financial.earnest_advance",
        "type": "decimal",
        "label_en": "Earnest / Advance Amount (Rs.)",
        "label_mr": "इसार / आगाऊ रक्कम (रु.)",
        "required": true
      },
      "execution_date": {
        "name": "execution_date",
        "type": "date",
        "label_en": "Execution Date",
        "label_mr": "दस्त निष्पादनाची तारीख",
        "required": true
      }
    },
    "derived_fields": {
      "financial.balance_amount": {
        "name": "financial.balance_amount",
        "type": "decimal",
        "expression": "financial.total_consideration - financial.earnest_advance",
        "label_en": "Balance Amount",
        "label_mr": "शिल्लक मोबदला रक्कम"
      },
      "property.carpet_area_sqft": {
        "name": "property.carpet_area_sqft",
        "type": "decimal",
        "expression": "property.carpet_area_sqm * 10.7639104",
        "label_en": "Carpet Area (Sq. Feet)",
        "label_mr": "कार्पेट क्षेत्रफळ (चौ.फूट)"
      }
    },
    "validations": [
      {
        "id": "earnest_le_total",
        "condition": "financial.earnest_advance <= financial.total_consideration",
        "message_en": "Earnest money cannot exceed total consideration",
        "message_mr": "इसार रक्कम एकूण मोबदल्यापेक्षा जास्त असू शकत नाही",
        "severity": "error"
      },
      {
        "id": "total_gt_zero",
        "condition": "financial.total_consideration > 0",
        "message_en": "Total consideration must be greater than zero",
        "message_mr": "एकूण मोबदला शून्यापेक्षा जास्त असणे आवश्यक आहे",
        "severity": "error"
      }
    ]
  },
  "sale_deed_plot_hi": {
    "manifest_schema": 1,
    "template_id": "sale_deed_plot_hi",
    "name_en": "Sale Deed (Plot in NIT/NMC Layout)",
    "name_mr": "विक्रय विलेख (भूखंड / प्लॉट)",
    "version": 1,
    "status": "draft",
    "document_type": "sale_deed",
    "property_type": "plot",
    "language": "hi",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "sellers": {
        "role": "seller",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Seller(s)",
        "label_mr": "विक्रेता (प्रथम पक्षकार)"
      },
      "purchasers": {
        "role": "purchaser",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Purchaser(s)",
        "label_mr": "क्रेता (द्वितीय पक्षकार)"
      }
    },
    "repeaters": {
      "instalments": {
        "name": "instalments",
        "min": 1,
        "max": 6,
        "label_en": "Instalment Details",
        "label_mr": "हप्ता / धनादेश तपशील"
      },
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_details",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.plot_no",
          "property.layout_name",
          "property.sheet_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      },
      {
        "id": "financial_details",
        "title_en": "Financial Consideration",
        "title_mr": "मोबदला व देय रक्कम",
        "field_names": [
          "financial.total_consideration",
          "financial.earnest_advance"
        ]
      }
    ],
    "fields": {
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.plot_no": {
        "name": "property.plot_no",
        "type": "string",
        "label_en": "Plot No.",
        "label_mr": "प्लॉट क्र.",
        "required": true
      },
      "property.layout_name": {
        "name": "property.layout_name",
        "type": "string",
        "label_en": "Layout / Colony Name",
        "label_mr": "लेआउटचे नाव",
        "required": false
      },
      "property.sheet_no": {
        "name": "property.sheet_no",
        "type": "string",
        "label_en": "City Survey Sheet No.",
        "label_mr": "नगर भूमापन शीट क्र.",
        "required": false
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South",
        "label_mr": "दक्षिण",
        "required": true
      },
      "financial.total_consideration": {
        "name": "financial.total_consideration",
        "type": "decimal",
        "label_en": "Total Consideration (Rs.)",
        "label_mr": "एकूण मोबदला (रु.)",
        "required": true
      },
      "financial.earnest_advance": {
        "name": "financial.earnest_advance",
        "type": "decimal",
        "label_en": "Earnest / Advance Amount (Rs.)",
        "label_mr": "इसार / आगाऊ रक्कम (रु.)",
        "required": true
      },
      "execution_date": {
        "name": "execution_date",
        "type": "date",
        "label_en": "Execution Date",
        "label_mr": "दस्त निष्पादनाची तारीख",
        "required": true
      }
    },
    "derived_fields": {
      "financial.balance_amount": {
        "name": "financial.balance_amount",
        "type": "decimal",
        "expression": "financial.total_consideration - financial.earnest_advance",
        "label_en": "Balance Consideration Amount",
        "label_mr": "शिल्लक मोबदला रक्कम"
      },
      "property.area_sqft": {
        "name": "property.area_sqft",
        "type": "decimal",
        "expression": "property.area_sqm * 10.7639104",
        "label_en": "Area (Sq. Feet)",
        "label_mr": "क्षेत्रफळ (चौ.फूट)"
      }
    },
    "validations": [
      {
        "id": "earnest_le_total",
        "condition": "financial.earnest_advance <= financial.total_consideration",
        "message_en": "Earnest amount cannot exceed total consideration",
        "message_mr": "इसार रक्कम एकूण मोबदल्यापेक्षा जास्त असू शकत नाही",
        "severity": "error"
      },
      {
        "id": "total_gt_zero",
        "condition": "financial.total_consideration > 0",
        "message_en": "Total consideration must be greater than zero",
        "message_mr": "एकूण मोबदला शून्यापेक्षा जास्त असणे आवश्यक आहे",
        "severity": "error"
      }
    ]
  },
  "sale_deed_plot_mr": {
    "manifest_schema": 1,
    "template_id": "sale_deed_plot_mr",
    "name_en": "Sale Deed (Plot in NIT/NMC Layout)",
    "name_mr": "खरेदीखत (भूखंड - ना.सु.प्र./ना.म.पा. लेआउट)",
    "version": 1,
    "status": "approved",
    "document_type": "sale_deed",
    "property_type": "plot",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "sellers": {
        "role": "seller",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Seller(s)",
        "label_mr": "विक्रेता"
      },
      "purchasers": {
        "role": "purchaser",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Purchaser(s)",
        "label_mr": "खरेदीदार"
      }
    },
    "repeaters": {
      "instalments": {
        "name": "instalments",
        "min": 1,
        "max": 6,
        "label_en": "Instalment Details",
        "label_mr": "हप्ता / धनादेश तपशील"
      },
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_details",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.plot_no",
          "property.layout_name",
          "property.sheet_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      },
      {
        "id": "financial_details",
        "title_en": "Financial Consideration",
        "title_mr": "मोबदला व देय रक्कम",
        "field_names": [
          "financial.total_consideration",
          "financial.earnest_advance"
        ]
      }
    ],
    "fields": {
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.plot_no": {
        "name": "property.plot_no",
        "type": "string",
        "label_en": "Plot No.",
        "label_mr": "प्लॉट क्र.",
        "required": true
      },
      "property.layout_name": {
        "name": "property.layout_name",
        "type": "string",
        "label_en": "Layout / Colony Name",
        "label_mr": "लेआउटचे नाव",
        "required": false
      },
      "property.sheet_no": {
        "name": "property.sheet_no",
        "type": "string",
        "label_en": "City Survey Sheet No.",
        "label_mr": "नगर भूमापन शीट क्र.",
        "required": false
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South",
        "label_mr": "दक्षिण",
        "required": true
      },
      "financial.total_consideration": {
        "name": "financial.total_consideration",
        "type": "decimal",
        "label_en": "Total Consideration (Rs.)",
        "label_mr": "एकूण मोबदला (रु.)",
        "required": true
      },
      "financial.earnest_advance": {
        "name": "financial.earnest_advance",
        "type": "decimal",
        "label_en": "Earnest / Advance Amount (Rs.)",
        "label_mr": "इसार / आगाऊ रक्कम (रु.)",
        "required": true
      },
      "execution_date": {
        "name": "execution_date",
        "type": "date",
        "label_en": "Execution Date",
        "label_mr": "दस्त निष्पादनाची तारीख",
        "required": true
      }
    },
    "derived_fields": {
      "financial.balance_amount": {
        "name": "financial.balance_amount",
        "type": "decimal",
        "expression": "financial.total_consideration - financial.earnest_advance",
        "label_en": "Balance Consideration Amount",
        "label_mr": "शिल्लक मोबदला रक्कम"
      },
      "property.area_sqft": {
        "name": "property.area_sqft",
        "type": "decimal",
        "expression": "property.area_sqm * 10.7639104",
        "label_en": "Area (Sq. Feet)",
        "label_mr": "क्षेत्रफळ (चौ.फूट)"
      }
    },
    "validations": [
      {
        "id": "earnest_le_total",
        "condition": "financial.earnest_advance <= financial.total_consideration",
        "message_en": "Earnest amount cannot exceed total consideration",
        "message_mr": "इसार रक्कम एकूण मोबदल्यापेक्षा जास्त असू शकत नाही",
        "severity": "error"
      },
      {
        "id": "total_gt_zero",
        "condition": "financial.total_consideration > 0",
        "message_en": "Total consideration must be greater than zero",
        "message_mr": "एकूण मोबदला शून्यापेक्षा जास्त असणे आवश्यक आहे",
        "severity": "error"
      }
    ]
  },
  "sale_deed_shop_hi": {
    "manifest_schema": 1,
    "template_id": "sale_deed_shop_hi",
    "name_en": "Sale Deed (Commercial Shop / Unit)",
    "name_mr": "विक्रय विलेख (व्यावसायिक दुकान / यूनिट)",
    "version": 1,
    "status": "draft",
    "document_type": "sale_deed",
    "property_type": "shop",
    "language": "hi",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "sellers": {
        "role": "seller",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Seller(s)",
        "label_mr": "विक्रेता"
      },
      "purchasers": {
        "role": "purchaser",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Purchaser(s)",
        "label_mr": "क्रेता"
      }
    },
    "repeaters": {
      "instalments": {
        "name": "instalments",
        "min": 1,
        "max": 6,
        "label_en": "Instalment Details",
        "label_mr": "हप्ता / धनादेश तपशील"
      },
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "shop_schedule",
        "title_en": "Commercial Shop Schedule",
        "title_mr": "दुकानाचे वर्णन",
        "field_names": [
          "property.shop_no",
          "property.floor_no",
          "property.complex_name",
          "property.mouza",
          "property.sheet_no",
          "property.khasra_no",
          "property.builtup_area_sqm",
          "property.frontage_ft"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Shop Boundaries",
        "title_mr": "दुकानाची चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      },
      {
        "id": "financial_details",
        "title_en": "Financial Consideration",
        "title_mr": "मोबदला व देय रक्कम",
        "field_names": [
          "financial.total_consideration",
          "financial.earnest_advance"
        ]
      }
    ],
    "fields": {
      "property.shop_no": {
        "name": "property.shop_no",
        "type": "string",
        "label_en": "Shop / Unit No.",
        "label_mr": "दुकान / गाळा क्र.",
        "required": true
      },
      "property.floor_no": {
        "name": "property.floor_no",
        "type": "string",
        "label_en": "Floor",
        "label_mr": "मजला",
        "required": true,
        "default": "तळमजला (Ground Floor)"
      },
      "property.complex_name": {
        "name": "property.complex_name",
        "type": "string",
        "label_en": "Commercial Complex / Market Name",
        "label_mr": "व्यावसायिक संकुलाचे नाव",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza",
        "label_mr": "मौजे",
        "required": true
      },
      "property.sheet_no": {
        "name": "property.sheet_no",
        "type": "string",
        "label_en": "City Survey Sheet No.",
        "label_mr": "नगर भूमापन शीट क्र.",
        "required": false
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.builtup_area_sqm": {
        "name": "property.builtup_area_sqm",
        "type": "decimal",
        "label_en": "Built-up Area (Sq. Metres)",
        "label_mr": "बांधकाम क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "property.frontage_ft": {
        "name": "property.frontage_ft",
        "type": "decimal",
        "label_en": "Road Frontage (Feet)",
        "label_mr": "रस्त्याकडील दर्शनी बाजू (फूट)",
        "required": false
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South",
        "label_mr": "दक्षिण",
        "required": true
      },
      "financial.total_consideration": {
        "name": "financial.total_consideration",
        "type": "decimal",
        "label_en": "Total Consideration (Rs.)",
        "label_mr": "एकूण मोबदला (रु.)",
        "required": true
      },
      "financial.earnest_advance": {
        "name": "financial.earnest_advance",
        "type": "decimal",
        "label_en": "Earnest / Advance Amount (Rs.)",
        "label_mr": "इसार / आगाऊ रक्कम (रु.)",
        "required": true
      },
      "execution_date": {
        "name": "execution_date",
        "type": "date",
        "label_en": "Execution Date",
        "label_mr": "दस्त निष्पादनाची तारीख",
        "required": true
      }
    },
    "derived_fields": {
      "financial.balance_amount": {
        "name": "financial.balance_amount",
        "type": "decimal",
        "expression": "financial.total_consideration - financial.earnest_advance",
        "label_en": "Balance Amount",
        "label_mr": "शिल्लक मोबदला रक्कम"
      },
      "property.builtup_area_sqft": {
        "name": "property.builtup_area_sqft",
        "type": "decimal",
        "expression": "property.builtup_area_sqm * 10.7639104",
        "label_en": "Built-up Area (Sq. Feet)",
        "label_mr": "बांधकाम क्षेत्रफळ (चौ.फूट)"
      }
    },
    "validations": [
      {
        "id": "earnest_le_total",
        "condition": "financial.earnest_advance <= financial.total_consideration",
        "message_en": "Earnest money cannot exceed total consideration",
        "message_mr": "इसार रक्कम एकूण मोबदल्यापेक्षा जास्त असू शकत नाही",
        "severity": "error"
      },
      {
        "id": "total_gt_zero",
        "condition": "financial.total_consideration > 0",
        "message_en": "Total consideration must be greater than zero",
        "message_mr": "एकूण मोबदला शून्यापेक्षा जास्त असणे आवश्यक आहे",
        "severity": "error"
      }
    ]
  },
  "sale_deed_shop_mr": {
    "manifest_schema": 1,
    "template_id": "sale_deed_shop_mr",
    "name_en": "Sale Deed (Commercial Shop / Unit in Marathi)",
    "name_mr": "खरेदीखत (व्यावसायिक दुकान / गाळा)",
    "version": 1,
    "status": "draft",
    "document_type": "sale_deed",
    "property_type": "shop",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "sellers": {
        "role": "seller",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Seller(s)",
        "label_mr": "विक्रेता"
      },
      "purchasers": {
        "role": "purchaser",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Purchaser(s)",
        "label_mr": "खरेदीदार"
      }
    },
    "repeaters": {
      "instalments": {
        "name": "instalments",
        "min": 1,
        "max": 6,
        "label_en": "Instalment Details",
        "label_mr": "हप्ता / धनादेश तपशील"
      },
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "shop_schedule",
        "title_en": "Commercial Shop Schedule",
        "title_mr": "दुकानाचे वर्णन",
        "field_names": [
          "property.shop_no",
          "property.floor_no",
          "property.complex_name",
          "property.mouza",
          "property.sheet_no",
          "property.khasra_no",
          "property.builtup_area_sqm",
          "property.frontage_ft"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Shop Boundaries",
        "title_mr": "दुकानाची चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      },
      {
        "id": "financial_details",
        "title_en": "Financial Consideration",
        "title_mr": "मोबदला व देय रक्कम",
        "field_names": [
          "financial.total_consideration",
          "financial.earnest_advance"
        ]
      }
    ],
    "fields": {
      "property.shop_no": {
        "name": "property.shop_no",
        "type": "string",
        "label_en": "Shop / Unit No.",
        "label_mr": "दुकान / गाळा क्र.",
        "required": true
      },
      "property.floor_no": {
        "name": "property.floor_no",
        "type": "string",
        "label_en": "Floor",
        "label_mr": "मजला",
        "required": true,
        "default": "तळमजला (Ground Floor)"
      },
      "property.complex_name": {
        "name": "property.complex_name",
        "type": "string",
        "label_en": "Commercial Complex / Market Name",
        "label_mr": "व्यावसायिक संकुलाचे नाव",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza",
        "label_mr": "मौजे",
        "required": true
      },
      "property.sheet_no": {
        "name": "property.sheet_no",
        "type": "string",
        "label_en": "City Survey Sheet No.",
        "label_mr": "नगर भूमापन शीट क्र.",
        "required": false
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.builtup_area_sqm": {
        "name": "property.builtup_area_sqm",
        "type": "decimal",
        "label_en": "Built-up Area (Sq. Metres)",
        "label_mr": "बांधकाम क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "property.frontage_ft": {
        "name": "property.frontage_ft",
        "type": "decimal",
        "label_en": "Road Frontage (Feet)",
        "label_mr": "रस्त्याकडील दर्शनी बाजू (फूट)",
        "required": false
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South",
        "label_mr": "दक्षिण",
        "required": true
      },
      "financial.total_consideration": {
        "name": "financial.total_consideration",
        "type": "decimal",
        "label_en": "Total Consideration (Rs.)",
        "label_mr": "एकूण मोबदला (रु.)",
        "required": true
      },
      "financial.earnest_advance": {
        "name": "financial.earnest_advance",
        "type": "decimal",
        "label_en": "Earnest / Advance Amount (Rs.)",
        "label_mr": "इसार / आगाऊ रक्कम (रु.)",
        "required": true
      },
      "execution_date": {
        "name": "execution_date",
        "type": "date",
        "label_en": "Execution Date",
        "label_mr": "दस्त निष्पादनाची तारीख",
        "required": true
      }
    },
    "derived_fields": {
      "financial.balance_amount": {
        "name": "financial.balance_amount",
        "type": "decimal",
        "expression": "financial.total_consideration - financial.earnest_advance",
        "label_en": "Balance Amount",
        "label_mr": "शिल्लक मोबदला रक्कम"
      },
      "property.builtup_area_sqft": {
        "name": "property.builtup_area_sqft",
        "type": "decimal",
        "expression": "property.builtup_area_sqm * 10.7639104",
        "label_en": "Built-up Area (Sq. Feet)",
        "label_mr": "बांधकाम क्षेत्रफळ (चौ.फूट)"
      }
    },
    "validations": [
      {
        "id": "earnest_le_total",
        "condition": "financial.earnest_advance <= financial.total_consideration",
        "message_en": "Earnest money cannot exceed total consideration",
        "message_mr": "इसार रक्कम एकूण मोबदल्यापेक्षा जास्त असू शकत नाही",
        "severity": "error"
      },
      {
        "id": "total_gt_zero",
        "condition": "financial.total_consideration > 0",
        "message_en": "Total consideration must be greater than zero",
        "message_mr": "एकूण मोबदला शून्यापेक्षा जास्त असणे आवश्यक आहे",
        "severity": "error"
      }
    ]
  },
  "simple_mortgage_en": {
    "manifest_schema": 1,
    "template_id": "simple_mortgage_en",
    "name_en": "Deed of Simple Mortgage (Without Possession)",
    "name_mr": "साधे गहाणखत (विना ताबा गहाण)",
    "version": 1,
    "status": "draft",
    "document_type": "mortgage_deed",
    "property_type": "plot",
    "language": "en",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "mortgagors": {
        "role": "mortgagor",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Mortgagor(s)",
        "label_mr": "साधे गहाण देणारे"
      },
      "mortgagees": {
        "role": "mortgagee",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Mortgagee(s)",
        "label_mr": "साधे गहाण घेणारे"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "title_warranty",
      "witness_attestation"
    ]
  },
  "simple_mortgage_mr": {
    "manifest_schema": 1,
    "template_id": "simple_mortgage_mr",
    "name_en": "Deed of Simple Mortgage (Without Possession)",
    "name_mr": "साधे गहाणखत (विना ताबा गहाण)",
    "version": 1,
    "status": "draft",
    "document_type": "mortgage_deed",
    "property_type": "plot",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "mortgagors": {
        "role": "mortgagor",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Mortgagor(s)",
        "label_mr": "साधे गहाण देणारे"
      },
      "mortgagees": {
        "role": "mortgagee",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Mortgagee(s)",
        "label_mr": "साधे गहाण घेणारे"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "title_warranty",
      "witness_attestation"
    ]
  },
  "special_poa_en": {
    "manifest_schema": 1,
    "template_id": "special_poa_en",
    "name_en": "Special Power of Attorney (Designated Registration & Acts)",
    "name_mr": "विशेष कुलमुखत्यारपत्र (विशिष्ट कामासाठी मुखत्यार)",
    "version": 1,
    "status": "draft",
    "document_type": "special_poa",
    "property_type": "plot",
    "language": "en",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "principals": {
        "role": "principal",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Principal(s)",
        "label_mr": "मुखत्यार देणारे (मुख्य मालक)"
      },
      "attorneys": {
        "role": "attorney",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Special Attorney(s)",
        "label_mr": "विशेष मुखत्यार"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "special_poa_mr": {
    "manifest_schema": 1,
    "template_id": "special_poa_mr",
    "name_en": "Special Power of Attorney (Designated Registration & Acts)",
    "name_mr": "विशेष कुलमुखत्यारपत्र (विशिष्ट कामासाठी मुखत्यार)",
    "version": 1,
    "status": "draft",
    "document_type": "special_poa",
    "property_type": "plot",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "principals": {
        "role": "principal",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Principal(s)",
        "label_mr": "मुखत्यार देणारे (मुख्य मालक)"
      },
      "attorneys": {
        "role": "attorney",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Special Attorney(s)",
        "label_mr": "विशेष मुखत्यार"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "transfer_deed_en": {
    "manifest_schema": 1,
    "template_id": "transfer_deed_en",
    "name_en": "Deed of Transfer (Ownership and Rights Conveyance)",
    "name_mr": "हस्तांतरण पत्र (मालकी हक्क व ताबा हस्तांतरण)",
    "version": 1,
    "status": "draft",
    "document_type": "transfer_deed",
    "property_type": "plot",
    "language": "en",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "transferors": {
        "role": "transferor",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Transferor(s)",
        "label_mr": "हस्तांतरक"
      },
      "transferees": {
        "role": "transferee",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Transferee(s)",
        "label_mr": "हस्तांतरिती"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "title_warranty",
      "witness_attestation"
    ]
  },
  "transfer_deed_mr": {
    "manifest_schema": 1,
    "template_id": "transfer_deed_mr",
    "name_en": "Deed of Transfer (Ownership and Rights Conveyance)",
    "name_mr": "हस्तांतरण पत्र (मालकी हक्क व ताबा हस्तांतरण)",
    "version": 1,
    "status": "draft",
    "document_type": "transfer_deed",
    "property_type": "plot",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "transferors": {
        "role": "transferor",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Transferor(s)",
        "label_mr": "हस्तांतरक"
      },
      "transferees": {
        "role": "transferee",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Transferee(s)",
        "label_mr": "हस्तांतरिती"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "title_warranty",
      "witness_attestation"
    ]
  },
  "usufructuary_mortgage_en": {
    "manifest_schema": 1,
    "template_id": "usufructuary_mortgage_en",
    "name_en": "Deed of Usufructuary Mortgage (With Possession)",
    "name_mr": "भोगगहाणखत (ताबा व उत्पन्नासह गहाण)",
    "version": 1,
    "status": "draft",
    "document_type": "mortgage_deed",
    "property_type": "agricultural",
    "language": "en",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "mortgagors": {
        "role": "mortgagor",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Mortgagor(s)",
        "label_mr": "भोगगहाण देणारे"
      },
      "mortgagees": {
        "role": "mortgagee",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Mortgagee(s)",
        "label_mr": "भोगगहाण घेणारे"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "usufructuary_mortgage_mr": {
    "manifest_schema": 1,
    "template_id": "usufructuary_mortgage_mr",
    "name_en": "Deed of Usufructuary Mortgage (With Possession)",
    "name_mr": "भोगगहाणखत (ताबा व उत्पन्नासह गहाण)",
    "version": 1,
    "status": "draft",
    "document_type": "mortgage_deed",
    "property_type": "agricultural",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "mortgagors": {
        "role": "mortgagor",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Mortgagor(s)",
        "label_mr": "भोगगहाण देणारे"
      },
      "mortgagees": {
        "role": "mortgagee",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Mortgagee(s)",
        "label_mr": "भोगगहाण घेणारे"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      },
      {
        "id": "boundaries",
        "title_en": "Boundaries",
        "title_mr": "चतुःसीमा",
        "field_names": [
          "boundaries.east",
          "boundaries.west",
          "boundaries.north",
          "boundaries.south"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      },
      "boundaries.east": {
        "name": "boundaries.east",
        "type": "string",
        "label_en": "East Boundary",
        "label_mr": "पूर्व",
        "required": true
      },
      "boundaries.west": {
        "name": "boundaries.west",
        "type": "string",
        "label_en": "West Boundary",
        "label_mr": "पश्चिम",
        "required": true
      },
      "boundaries.north": {
        "name": "boundaries.north",
        "type": "string",
        "label_en": "North Boundary",
        "label_mr": "उत्तर",
        "required": true
      },
      "boundaries.south": {
        "name": "boundaries.south",
        "type": "string",
        "label_en": "South Boundary",
        "label_mr": "दक्षिण",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "will_en": {
    "manifest_schema": 1,
    "template_id": "will_en",
    "name_en": "Last Will and Testament",
    "name_mr": "मृत्युपत्र (इच्छापत्र)",
    "version": 1,
    "status": "draft",
    "document_type": "will",
    "property_type": "residential",
    "language": "en",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "testators": {
        "role": "testator",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Testator(s)",
        "label_mr": "इच्छापत्र / मृत्युपत्र करणारे (चाचणीकार)"
      },
      "beneficiaries": {
        "role": "beneficiary",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Beneficiary(ies)",
        "label_mr": "वारसदार / लाभार्थी"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  },
  "will_mr": {
    "manifest_schema": 1,
    "template_id": "will_mr",
    "name_en": "Last Will and Testament",
    "name_mr": "मृत्युपत्र (इच्छापत्र)",
    "version": 1,
    "status": "draft",
    "document_type": "will",
    "property_type": "residential",
    "language": "mr",
    "page_size": "legal",
    "digits_setting": "western",
    "retention_class": "matter_lifecycle",
    "parties": {
      "testators": {
        "role": "testator",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Testator(s)",
        "label_mr": "इच्छापत्र / मृत्युपत्र करणारे (चाचणीकार)"
      },
      "beneficiaries": {
        "role": "beneficiary",
        "min_parties": 1,
        "max_parties": 4,
        "label_en": "Beneficiary(ies)",
        "label_mr": "वारसदार / लाभार्थी"
      }
    },
    "repeaters": {
      "witnesses": {
        "name": "witnesses",
        "min": 2,
        "max": 2,
        "label_en": "Attesting Witnesses",
        "label_mr": "साक्षीदार"
      }
    },
    "sections": [
      {
        "id": "property_schedule",
        "title_en": "Property Schedule",
        "title_mr": "मिळकतीचे वर्णन",
        "field_names": [
          "property.mouza",
          "property.khasra_no",
          "property.area_sqm"
        ]
      }
    ],
    "fields": {
      "execution_date": {
        "name": "execution_date",
        "type": "string",
        "label_en": "Execution Date",
        "label_mr": "दस्त नोंदणी दिनांक",
        "required": true
      },
      "property.mouza": {
        "name": "property.mouza",
        "type": "string",
        "label_en": "Mouza / Village",
        "label_mr": "मौजे",
        "required": true
      },
      "property.khasra_no": {
        "name": "property.khasra_no",
        "type": "string",
        "label_en": "Khasra / Survey No.",
        "label_mr": "खसरा / सर्व्हे क्र.",
        "required": true
      },
      "property.area_sqm": {
        "name": "property.area_sqm",
        "type": "decimal",
        "label_en": "Area (Sq. Metres)",
        "label_mr": "क्षेत्रफळ (चौ.मी.)",
        "required": true
      }
    },
    "clauses": [
      "witness_attestation"
    ]
  }
};
