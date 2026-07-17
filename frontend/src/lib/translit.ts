/*
 * Romanized -> Devanagari (Nepali) transliteration — pure client-side, offline.
 *
 * Lets someone who can't type Nepali correct the OCR text by typing phonetically:
 *   "namaste"  -> नमस्ते
 *   "nepal"    -> नेपाल
 *   "kathmandu"-> कथमन्दु
 *
 * It is a typing AID, not a spelling authority: a consonant with no following
 * vowel becomes a half-letter (with ्) mid-word, and keeps its inherent "a" at
 * the end of a word. Capital letters select retroflex/aspirated variants
 * (T,Th,D,Dh,N,S) the way most Nepali phonetic keyboards do.
 *
 * Ported from webapp/static/translit.js (the Flask document digitizer) /
 * frontend/src/lib/translit.js (the ml-branch document digitizer app).
 */

// consonants — LONGEST keys first so greedy matching works (chh before ch, etc.)
const CONS: Record<string, string> = {
  chh: "छ", Chh: "छ",
  ksh: "क्ष", gy: "ज्ञ", shr: "श्र",
  kh: "ख", gh: "घ", ng: "ङ", ch: "च", jh: "झ", ny: "ञ",
  Th: "ठ", Dh: "ढ", th: "थ", dh: "ध", ph: "फ", bh: "भ",
  sh: "श", Sh: "ष",
  k: "क", g: "ग", c: "च", j: "ज",
  T: "ट", D: "ड", N: "ण",
  t: "त", d: "द", n: "न",
  p: "प", f: "फ", b: "ब", m: "म",
  y: "य", r: "र", l: "ल", v: "व", w: "व",
  s: "स", S: "ष", h: "ह",
};

// vowels -> [independent form, matra (dependent sign)]. "a" has no matra.
const VOW: Record<string, [string, string]> = {
  aa: ["आ", "ा"], A: ["आ", "ा"], ai: ["ऐ", "ै"], au: ["औ", "ौ"],
  ee: ["ई", "ी"], ii: ["ई", "ी"], oo: ["ऊ", "ू"], uu: ["ऊ", "ू"], ri: ["ऋ", "ृ"],
  a: ["अ", ""], i: ["इ", "ि"], u: ["उ", "ु"], e: ["ए", "े"], o: ["ओ", "ो"],
};

const HALANT = "्";
const ANUSVARA = "ं"; // typed as "M"
const CHANDRA = "ँ"; // typed as "MM"

const consKeys = Object.keys(CONS).sort((a, b) => b.length - a.length);
const vowKeys = Object.keys(VOW).sort((a, b) => b.length - a.length);

function matchAt(str: string, i: number, keys: string[]): string | null {
  for (const k of keys) {
    if (str.startsWith(k, i)) return k;
  }
  return null;
}

export function romanToDevanagari(token: string): string {
  if (!token) return token;
  let out = "";
  let i = 0;
  let prevWasConsonant = false;

  while (i < token.length) {
    // anusvara / chandrabindu shortcuts
    if (token.startsWith("MM", i)) { out += CHANDRA; i += 2; prevWasConsonant = false; continue; }
    if (token[i] === "M") { out += ANUSVARA; i += 1; prevWasConsonant = false; continue; }

    const c = matchAt(token, i, consKeys);
    if (c) {
      // a consonant directly after another consonant: the previous one is a half-letter
      if (prevWasConsonant) out += HALANT;
      out += CONS[c];
      i += c.length;
      const v = matchAt(token, i, vowKeys);
      if (v) {
        out += VOW[v][1]; // attach the matra (empty for "a")
        i += v.length;
        prevWasConsonant = false;
      } else {
        // no vowel yet — decide half vs inherent-"a" when we see what's next
        prevWasConsonant = true;
      }
      continue;
    }

    const v = matchAt(token, i, vowKeys);
    if (v) {
      // a vowel after a bare consonant would have been consumed above, so this
      // is an independent vowel (word start or after another vowel)
      if (prevWasConsonant) out += HALANT; // consonant + standalone vowel cluster
      out += VOW[v][0];
      i += v.length;
      prevWasConsonant = false;
      continue;
    }

    // anything we don't recognise (already-Devanagari, punctuation, digits) passes through
    out += token[i];
    i += 1;
    prevWasConsonant = false;
  }
  return out;
}
