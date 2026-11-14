import { FieldDefinition, RepeaterDefinition, TemplateManifest } from "./types";

const PARTY_FIELDS: Record<string, FieldDefinition> = {
  full_name: { name: "full_name", type: "string", label_en: "Full Legal Name", label_mr: "संपूर्ण नाव", required: true },
  gender: { name: "gender", type: "enum", label_en: "Gender", label_mr: "लिंग", enum_values: ["male", "female", "other"], default: "male", required: true },
  age: { name: "age", type: "integer", label_en: "Age (Years)", label_mr: "वय (वर्षे)", required: true },
  occupation: { name: "occupation", type: "string", label_en: "Occupation", label_mr: "व्यवसाय", required: true },
  address: { name: "address", type: "string", label_en: "Residential Address", label_mr: "राहण्याचा पत्ता", required: true },
  pan: { name: "pan", type: "string", label_en: "PAN Number", label_mr: "पॅन क्रमांक", required: false },
};

const KNOWN_REPEATER_FIELDS: Record<string, Record<string, FieldDefinition>> = {
  instalments: {
    amount: { name: "amount", type: "decimal", label_en: "Amount (Rs.)", label_mr: "रक्कम (रु.)", required: true },
    mode: { name: "mode", type: "enum", label_en: "Payment Mode", label_mr: "पेमेंट प्रकार", enum_values: ["cheque", "rtgs", "neft", "dd", "upi"], default: "cheque", required: true },
    ref_no: { name: "ref_no", type: "string", label_en: "Cheque / UTR No.", label_mr: "धनादेश / यूटीआर क्र.", required: true },
    bank_name: { name: "bank_name", type: "string", label_en: "Bank Name", label_mr: "बँकेचे नाव", required: true },
    date: { name: "date", type: "date", label_en: "Payment Date", label_mr: "दिनांक", required: true },
  },
  witnesses: {
    name: { name: "name", type: "string", label_en: "Witness Full Name", label_mr: "साक्षीदाराचे संपूर्ण नाव", required: true },
    address: { name: "address", type: "string", label_en: "Witness Address", label_mr: "साक्षीदाराचा पत्ता", required: true },
  },
};

export function normalizeManifest(raw: Partial<TemplateManifest> & { template_id: string }): TemplateManifest {
  const repeaters: Record<string, RepeaterDefinition> = {};

  for (const [key, partyDef] of Object.entries(raw.parties ?? {})) {
    repeaters[key] = {
      name: key,
      min: partyDef.min_parties ?? 1,
      max: partyDef.max_parties ?? 4,
      label_en: partyDef.label_en,
      label_mr: partyDef.label_mr,
      fields: PARTY_FIELDS,
    };
  }

  for (const [key, repDef] of Object.entries(raw.repeaters ?? {})) {
    const existingFields = repDef.fields && Object.keys(repDef.fields).length > 0 ? repDef.fields : undefined;
    repeaters[key] = {
      ...repDef,
      name: repDef.name || key,
      min: repDef.min ?? 1,
      max: repDef.max ?? 10,
      fields: existingFields ?? KNOWN_REPEATER_FIELDS[key] ?? {
        value: { name: "value", type: "string", label_en: "Details", label_mr: "तपशील", required: true },
      },
    };
  }

  return {
    manifest_schema: raw.manifest_schema ?? 1,
    template_id: raw.template_id,
    name_en: raw.name_en ?? raw.template_id,
    name_mr: raw.name_mr ?? raw.name_en ?? raw.template_id,
    version: raw.version ?? 1,
    document_type: raw.document_type ?? "deed",
    property_type: raw.property_type ?? "general",
    language: raw.language ?? "mr",
    page_size: raw.page_size ?? "legal",
    parties: raw.parties ?? {},
    repeaters,
    sections: raw.sections ?? [],
    fields: raw.fields ?? {},
    derived_fields: raw.derived_fields ?? {},
    validations: raw.validations ?? [],
  };
}

export function buildInitialFormData(manifest: TemplateManifest): Record<string, unknown> {
  const initial: Record<string, unknown> = {};
  for (const [key, field] of Object.entries(manifest.fields)) {
    initial[key] = field.default ?? (field.type === "boolean" ? false : "");
  }
  return initial;
}

export function buildInitialRepeatersData(manifest: TemplateManifest): Record<string, Record<string, unknown>[]> {
  const init: Record<string, Record<string, unknown>[]> = {};
  for (const [key, rep] of Object.entries(manifest.repeaters)) {
    const count = Math.max(1, rep.min);
    init[key] = Array.from({ length: count }, () => {
      const item: Record<string, unknown> = {};
      for (const [fKey, fDef] of Object.entries(rep.fields ?? {})) {
        item[fKey] = fDef.default ?? "";
      }
      return item;
    });
  }
  return init;
}

export function unflattenFormData(flat: Record<string, unknown>): Record<string, unknown> {
  const nested: Record<string, unknown> = {};
  for (const [key, val] of Object.entries(flat)) {
    const parts = key.split(".");
    let cursor = nested as Record<string, unknown>;
    for (let i = 0; i < parts.length - 1; i++) {
      const part = parts[i];
      if (!cursor[part] || typeof cursor[part] !== "object") {
        cursor[part] = {};
      }
      cursor = cursor[part] as Record<string, unknown>;
    }
    cursor[parts[parts.length - 1]] = val;
  }
  return nested;
}

