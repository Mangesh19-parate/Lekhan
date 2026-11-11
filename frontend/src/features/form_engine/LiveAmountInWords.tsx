import React, { useMemo } from "react";
import { IndianRupee } from "lucide-react";

interface Props {
  amount: number | string | undefined;
  language?: "mr" | "en";
}

const MR_NUMS: Record<number, string> = {
  0: "शून्य", 1: "एक", 2: "दोन", 3: "तीन", 4: "चार", 5: "पाच", 6: "सहा", 7: "सात", 8: "आठ", 9: "नऊ",
  10: "दहा", 11: "अकरा", 12: "बारा", 13: "तेरा", 14: "चौदा", 15: "पंधरा", 16: "सोळा", 17: "सतरा",
  18: "अठरा", 19: "एकोणीस", 20: "वीस", 25: "पंचवीस", 30: "तीस", 40: "चाळीस", 50: "पन्नास",
  60: "साठ", 70: "सत्तर", 80: "ऐंशी", 90: "नव्वद"
};

const EN_ONES: Record<number, string> = {
  0: "Zero", 1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven", 8: "Eight", 9: "Nine",
  10: "Ten", 11: "Eleven", 12: "Twelve", 13: "Thirteen", 14: "Fourteen", 15: "Fifteen", 16: "Sixteen",
  17: "Seventeen", 18: "Eighteen", 19: "Nineteen"
};

const EN_TENS: Record<number, string> = {
  20: "Twenty", 30: "Thirty", 40: "Forty", 50: "Fifty", 60: "Sixty", 70: "Seventy", 80: "Eighty", 90: "Ninety"
};

function numberToIndianWordsEn(num: number): string {
  if (num === 0) return "Rupees Zero Only";
  let n = Math.floor(num);
  const parts: string[] = [];

  const crores = Math.floor(n / 10000000);
  n %= 10000000;
  if (crores > 0) parts.push(`${numberToIndianWordsEn(crores).replace(/Rupees | Only/g, "")} Crore`);

  const lakhs = Math.floor(n / 100000);
  n %= 100000;
  if (lakhs > 0) parts.push(`${twoDigitsEn(lakhs)} Lakh`);

  const thousands = Math.floor(n / 1000);
  n %= 1000;
  if (thousands > 0) parts.push(`${twoDigitsEn(thousands)} Thousand`);

  const hundreds = Math.floor(n / 100);
  n %= 100;
  if (hundreds > 0) parts.push(`${EN_ONES[hundreds]} Hundred`);

  if (n > 0) parts.push(twoDigitsEn(n));

  return `Rupees ${parts.join(" ")} Only`;
}

function twoDigitsEn(n: number): string {
  if (n < 20) return EN_ONES[n] || String(n);
  const t = Math.floor(n / 10) * 10;
  const rem = n % 10;
  return rem === 0 ? EN_TENS[t] : `${EN_TENS[t]} ${EN_ONES[rem]}`;
}

function numberToWordsMr(num: number): string {
  if (num === 0) return "शून्य रुपये फक्त";
  let n = Math.floor(num);
  const parts: string[] = [];

  const crores = Math.floor(n / 10000000);
  n %= 10000000;
  if (crores > 0) parts.push(`${twoDigitsMr(crores)} कोटी`);

  const lakhs = Math.floor(n / 100000);
  n %= 100000;
  if (lakhs > 0) parts.push(`${twoDigitsMr(lakhs)} लाख`);

  const thousands = Math.floor(n / 1000);
  n %= 1000;
  if (thousands > 0) parts.push(`${twoDigitsMr(thousands)} हजार`);

  const hundreds = Math.floor(n / 100);
  n %= 100;
  if (hundreds > 0) parts.push(`${twoDigitsMr(hundreds)}शे`);

  if (n > 0) parts.push(twoDigitsMr(n));

  return `${parts.join(" ")} रुपये फक्त`;
}

function twoDigitsMr(n: number): string {
  return MR_NUMS[n] || String(n);
}

export const LiveAmountInWords: React.FC<Props> = ({ amount, language = "mr" }) => {
  const words = useMemo(() => {
    const val = typeof amount === "string" ? parseFloat(amount.replace(/,/g, "")) : amount;
    if (val === undefined || isNaN(val) || val <= 0) return null;
    return language === "mr" ? numberToWordsMr(val) : numberToIndianWordsEn(val);
  }, [amount, language]);

  if (!words) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      style={{
        marginTop: "6px",
        fontSize: "0.8125rem",
        backgroundColor: "var(--brand-50)",
        color: "var(--brand-700)",
        border: "1px solid var(--brand-100)",
        borderRadius: "var(--radius-input)",
        padding: "6px 10px",
        display: "flex",
        alignItems: "center",
        gap: "6px",
        lineHeight: 1.4,
      }}
    >
      <IndianRupee size={14} className="shrink-0 text-[var(--brand-500)]" />
      <span style={{ fontWeight: 600, color: "var(--text-secondary)", fontSize: "0.75rem" }}>
        {language === "mr" ? "अक्षरी:" : "In words:"}
      </span>
      <span style={{ fontWeight: 600, color: "var(--brand-600)" }}>{words}</span>
    </div>
  );
};
