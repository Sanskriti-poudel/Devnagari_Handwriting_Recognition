/*
 * Preeti <-> Unicode (Nepali) conversion — pure, offline, no dependencies.
 *
 * "Preeti" is the legacy TTF font that encodes Devanagari as Latin-1 keystrokes
 * (the writing you see in old Nepali documents, government forms, newspapers).
 * It is a FONT, not an encoding standard, so the same bytes render as Devanagari
 * only while the Preeti font is installed. This module turns that legacy text
 * into real Unicode (searchable, copyable, future-proof) and back.
 *
 *   preetiToUnicode("g]kfn")  -> "नेपाल"
 *   unicodeToPreeti("नेपाल")  -> "g]kfn"
 *
 * Ported verbatim from webapp/static/preeti.js (the Flask document digitizer).
 */

// --------------------------------------------------------------- forward map
// Preeti keystroke (Latin-1 char) -> Devanagari Unicode fragment.
// ASCII core covers essentially all real Preeti text; the high-ASCII entries
// are font ligatures that occasionally appear. 'm' is intentionally absent —
// it is a transform sentinel consumed by the post-rules (पm->फ, भm->झ, ...).
const CHAR_MAP = {
  a: "ब", A: "ब्", b: "द", B: "द्य", c: "अ", C: "ऋ", d: "म", D: "म्",
  e: "भ", E: "भ्", f: "ा", F: "ँ", g: "न", G: "न्", h: "ज", H: "ज्",
  i: "ष्", I: "क्ष्", j: "व", J: "व्", k: "प", K: "प्", l: "ि", L: "ी",
  n: "ल", N: "ल्", o: "य", O: "इ", p: "उ", P: "ए", q: "त्र", Q: "त्त",
  r: "च", R: "च्", s: "क", S: "क्", t: "त", T: "त्", u: "ग", U: "ग्",
  v: "ख", V: "ख्", w: "ध", W: "ध्", x: "ह", X: "ह्", y: "थ", Y: "थ्",
  z: "श", Z: "श्",
  // unshifted number row -> conjuncts / consonants (Preeti layout)
  "0": "ण्", "1": "ज्ञ", "2": "द्द", "3": "घ", "4": "द्ध",
  "5": "छ", "6": "ट", "7": "ठ", "8": "ड", "9": "ढ",
  // shifted number row -> Devanagari digits
  "!": "१", "@": "२", "#": "३", "$": "४", "%": "५",
  "^": "६", "&": "७", "*": "८", "(": "९", ")": "०",
  // punctuation / signs
  "`": "ञ", "~": "ञ्", "-": "(", "_": ")", "=": ".", "+": "ं",
  "[": "ृ", "]": "े", "}": "ै", "\\": "्", "|": "्र",
  ";": "स", ":": "स्", "'": "ु", '"': "ू",
  ",": ",", ".": "।", "/": "र", "<": "?", ">": "श्र", "?": "रु",
  // high-ASCII ligatures (the unambiguous ones)
  "«": "्र", "„": "ध्र", "¿": "रू", "£": "घ्", "¢": "द्घ", "¥": "र्‍",
  "ª": "ङ", "÷": "/", "‰": "झ्", "˜": "ऽ", "›": "द्र", "±": "+",
  "§": "ट्ट", "¶": "ठ्ठ", "•": "ड्ड", "©": "र", "¤": "झ्", "¡": "ज्ञ्",
  "Ë": "ङ्ग", "Î": "ङ्ख", "Í": "ङ्क", "Ì": "न्न", "Ø": "्य",
  "°": "ङ्ढ", "‹": "ङ्घ", "ß": "द्म", "å": "द्व", "Å": "हृ", "ç": "ॐ",
};

// Character classes used by the reordering rules.
const H = "्"; // halant / virama
const M_ALL = "ािीुूृेैोौंःँ"; // every dependent sign
const M_V = "ािीुूृेैोौः"; // dependent signs minus anusvara/chandrabindu

// Ordered post-processing rules (string pattern, replacement), applied with
// the global flag in sequence — order matters. Faithful to the canonical set.
const POST_RULES = [
  [H + "ा", ""], // stray halant+aa cleanup
  ["(त्र|त्त)([^उभप]+?)m", "$1m$2"], // protect त्र/त्त before sentinel hop
  ["त्रm", "क्र"],
  ["त्तm", "क्त"],
  ["([^उभप]+?)m", "m$1"], // hop the 'm' sentinel left
  ["उm", "ऊ"],
  ["भm", "झ"],
  ["पm", "फ"],
  ["इ{", "ई"],
  ["ि((." + H + ")*[^" + H + "])", "$1ि"], // short-i: move after its cluster
  ["(.[" + M_ALL + "]*?){", "{$1"], // walk reph marker left over a syllable
  ["((." + H + ")*){", "{$1"], // walk reph marker left over half-letters
  ["{", "र्"], // reph marker -> र्
  ["([" + M_ALL + "]+?)(" + H + "(." + H + ")*[^" + H + "])", "$2$1"],
  [H + "([" + M_ALL + "]+?)((." + H + ")*[^" + H + "])", H + "$2$1"],
  ["([ंँ])([" + M_V + "]*)", "$2$1"], // anusvara/chandrabindu after other signs
  ["ँँ", "ँ"], ["ंं", "ं"], ["ेे", "े"], ["ैै", "ै"], ["ुु", "ु"], ["ूू", "ू"],
  ["^ः", ":"],
  ["टृ", "ट्ट"],
  ["ेा", "ाे"], ["ैा", "ाै"], // normalise split-vowel order...
  ["अाे", "ओ"], ["अाै", "औ"], ["अा", "आ"], // ...then coalesce
  ["एे", "ऐ"], ["ाे", "ो"], ["ाै", "ौ"],
];

export function preetiToUnicode(text) {
  if (!text) return text;
  let out = "";
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    out += Object.prototype.hasOwnProperty.call(CHAR_MAP, ch) ? CHAR_MAP[ch] : ch;
  }
  for (let r = 0; r < POST_RULES.length; r++) {
    out = out.replace(new RegExp(POST_RULES[r][0], "g"), POST_RULES[r][1]);
  }
  return out;
}

// --------------------------------------------------------------- reverse map
// Devanagari Unicode -> Preeti keystrokes. Verified single-codepoint table;
// clusters/conjuncts are assembled per-character (halant -> "\\").
const UTOP = {
  "अ": "c", "आ": "cf", "इ": "O", "ई": "O{", "उ": "p", "ऊ": "pm",
  "ए": "P", "ऐ": "P]", "ओ": "cf]", "औ": "cf}", "ऋ": "C",
  "ा": "f", "ि": "l", "ी": "L", "ु": "'", "ू": '"', "ृ": "[",
  "े": "]", "ै": "}", "ो": "f]", "ौ": "f}",
  "ं": "+", "ँ": "F", "ः": "M", "्": "\\", "ऽ": "˜",
  "क": "s", "ख": "v", "ग": "u", "घ": "3", "ङ": "ª",
  "च": "r", "छ": "5", "ज": "h", "झ": "´", "ञ": "`",
  "ट": "6", "ठ": "7", "ड": "8", "ढ": "9", "ण": "0f",
  "त": "t", "थ": "y", "द": "b", "ध": "w", "न": "g",
  "प": "k", "फ": "km", "ब": "a", "भ": "e", "म": "d",
  "य": "o", "र": "/", "ल": "n", "व": "j",
  "श": "z", "ष": "if", "स": ";", "ह": "x",
  "ज्ञ": "1", "त्र": "q", "रू": "?",
  "१": "!", "२": "@", "३": "#", "४": "$", "५": "%",
  "६": "^", "७": "&", "८": "*", "९": "(", "०": ")",
  "।": ".",
};

const CONS = "कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह";
const SIGNS = "ािीुूृेैोौ"; // dependent vowel signs
const MODS = "ंँः"; // anusvara / chandrabindu / visarga

function mapCluster(uni) {
  let out = "";
  for (let i = 0; i < uni.length; i++) out += UTOP[uni[i]] || uni[i];
  return out;
}

export function unicodeToPreeti(text) {
  if (!text) return text;
  let out = "";
  let i = 0;
  const n = text.length;
  while (i < n) {
    let ch = text[i];

    // reph: र् riding on a following consonant -> cluster (+signs) then '{'
    let reph = false;
    if (ch === "र" && text[i + 1] === H && CONS.indexOf(text[i + 2]) !== -1) {
      reph = true;
      i += 2;
      ch = text[i];
    }

    if (CONS.indexOf(ch) !== -1) {
      // consonant cluster: C (्C)*
      let cluster = ch;
      i++;
      while (text[i] === H && CONS.indexOf(text[i + 1]) !== -1) {
        cluster += H + text[i + 1];
        i += 2;
      }
      let trailingHalant = false;
      if (text[i] === H) { trailingHalant = true; i++; } // word-final half-letter

      // gather the matras / mods that belong to this syllable
      let sgns = "";
      while (i < n && (SIGNS.indexOf(text[i]) !== -1 || MODS.indexOf(text[i]) !== -1)) {
        sgns += text[i];
        i++;
      }

      const hasShortI = sgns.indexOf("ि") !== -1;
      let pk = mapCluster(cluster);
      if (trailingHalant) pk += "\\";
      let sk = "";
      for (let s = 0; s < sgns.length; s++) {
        if (sgns[s] === "ि") continue; // becomes the 'l' prefix
        sk += UTOP[sgns[s]] || sgns[s];
      }
      out += (hasShortI ? "l" : "") + pk + sk + (reph ? "{" : "");
      continue;
    }

    if (reph) { // र् not followed by a consonant — emit literally
      out += UTOP["र"] + "\\";
    }

    // independent vowels / digits / punctuation; try 2-char keys first (रू)
    const two = text.substr(i, 2);
    if (Object.prototype.hasOwnProperty.call(UTOP, two)) { out += UTOP[two]; i += 2; continue; }
    out += Object.prototype.hasOwnProperty.call(UTOP, ch) ? UTOP[ch] : ch;
    i++;
  }
  return out;
}
