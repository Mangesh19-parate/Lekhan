export type FieldType = "string" | "decimal" | "integer" | "boolean" | "date" | "enum" | "text";

export interface FieldDefinition {
  name: string;
  type: FieldType;
  label_en: string;
  label_mr: string;
  required?: boolean;
  default?: any;
  enum_values?: string[];
  visible_when?: string;
  help_text_en?: string;
  help_text_mr?: string;
}

export interface RepeaterDefinition {
  name: string;
  min: number;
  max: number;
  label_en?: string;
  label_mr?: string;
  fields: Record<string, FieldDefinition>;
}

export interface SectionDefinition {
  id: string;
  title_en: string;
  title_mr: string;
  field_names: string[];
  visible_when?: string;
}

export interface DerivedFieldDefinition {
  name: string;
  type: FieldType;
  expression: string;
  label_en?: string;
  label_mr?: string;
}

export interface ValidationRule {
  id: string;
  condition: string;
  message_en: string;
  message_mr: string;
  severity: "error" | "warning";
}

export interface TemplateManifest {
  manifest_schema: number;
  template_id: string;
  name_en: string;
  name_mr: string;
  version: number;
  document_type: string;
  property_type: string;
  language: "mr" | "en" | "hi";
  page_size: "legal" | "a4";
  parties: Record<string, { role: string; min_parties: number; max_parties: number; label_en: string; label_mr: string }>;
  repeaters: Record<string, RepeaterDefinition>;
  sections: SectionDefinition[];
  fields: Record<string, FieldDefinition>;
  derived_fields: Record<string, DerivedFieldDefinition>;
  validations: ValidationRule[];
}

