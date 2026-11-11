/**
 * Input formatting and masking utilities (F-015).
 * - Indian currency grouping (e.g. 25,00,000)
 * - PAN formatting (uppercase AAAAA9999A)
 * - Pincode formatting (6 digits)
 * - Date formatting (DD/MM/YYYY)
 */

export function formatIndianCurrency(val: string | number): string {
  if (val === undefined || val === null || val === "") return "";
  const clean = typeof val === "number" ? Math.floor(val).toString() : val.toString().replace(/[^0-9]/g, "");
  if (!clean) return "";

  if (clean.length <= 3) return clean;

  const last3 = clean.substring(clean.length - 3);
  const otherDigits = clean.substring(0, clean.length - 3);
  const formattedOther = otherDigits.replace(/\B(?=(\d{2})+(?!\d))/g, ",");

  return `${formattedOther},${last3}`;
}

export function formatPAN(val: string): string {
  if (!val) return "";
  return val
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, "")
    .slice(0, 10);
}

export function formatPincode(val: string): string {
  if (!val) return "";
  return val.replace(/[^0-9]/g, "").slice(0, 6);
}

export function formatDate(val: string): string {
  if (!val) return "";
  const digits = val.replace(/[^0-9]/g, "").slice(0, 8);
  if (digits.length <= 2) return digits;
  if (digits.length <= 4) return `${digits.slice(0, 2)}/${digits.slice(2)}`;
  return `${digits.slice(0, 2)}/${digits.slice(2, 4)}/${digits.slice(4, 8)}`;
}
