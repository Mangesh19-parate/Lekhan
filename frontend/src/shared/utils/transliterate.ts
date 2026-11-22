/**
 * Phonetic transliteration suggestion helper (F-013).
 *
 * CRITICAL RULE (AGENTS.md Rule 6 / PRD FR-04):
 * Names and addresses are stored per language and are NEVER auto-transliterated
 * without explicit user review and confirmation. Suggestions are advisory only.
 */

const LATIN_TO_DEV_MAP: Record<string, string> = {
  a: "अ", aa: "आ", i: "इ", ee: "ई", u: "उ", oo: "ऊ", e: "ए", ai: "ऐ", o: "ओ", au: "औ",
  k: "क", kh: "ख", g: "ग", gh: "घ",
  ch: "च", chh: "छ", j: "ज", jh: "झ",
  t: "त", th: "थ", d: "द", dh: "ध", n: "न",
  p: "प", ph: "फ", f: "फ", b: "ब", bh: "भ", m: "म",
  y: "य", r: "र", l: "ल", v: "व", w: "व",
  sh: "श", s: "स", h: "ह",
  joshi: "जोशी", patil: "पाटील", deshmukh: "देशमुख", shinde: "शिंदे", pawar: "पवार",
  kulkarni: "कुलकर्णी", bapat: "बापट", vyas: "व्यास", sharma: "शर्मा", jain: "जैन",
  nagpur: "नागपूर", pune: "पुणे", mumbai: "मुंबई", dharampeth: "धरमपेठ", sonegaon: "सोनेगाव"
};

const DEV_TO_LATIN_MAP: Record<string, string> = {
  "जोशी": "Joshi", "पाटील": "Patil", "देशमुख": "Deshmukh", "शिंदे": "Shinde", "पवार": "Pawar",
  "कुलकर्णी": "Kulkarni", "नागपूर": "Nagpur", "पुणे": "Pune", "मुंबई": "Mumbai",
  "आनंद": "Anand", "सुरेश": "Suresh", "रमेश": "Ramesh", "सचिन": "Sachin", "विजय": "Vijay",
  "सोनेगाव": "Sonegaon", "धरमपेठ": "Dharampeth"
};

/** Suggests Devanagari representation for English legal party name/address. */
export function suggestDevanagari(input: string): string {
  if (!input) return "";
  const words = input.trim().split(/\s+/);
  return words
    .map((word) => {
      const lower = word.toLowerCase().replace(/[^a-z]/g, "");
      if (LATIN_TO_DEV_MAP[lower]) return LATIN_TO_DEV_MAP[lower];
      return word; // Pass-through if not in basic phonetic map
    })
    .join(" ");
}

/** Suggests English Latin representation for Devanagari legal party name/address. */
export function suggestLatin(input: string): string {
  if (!input) return "";
  const words = input.trim().split(/\s+/);
  return words
    .map((word) => {
      const clean = word.replace(/[,.]/g, "");
      if (DEV_TO_LATIN_MAP[clean]) return DEV_TO_LATIN_MAP[clean];
      return word;
    })
    .join(" ");
}
