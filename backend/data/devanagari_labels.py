# Maps OCR class names (e.g. "character_1_ka") → Devanagari glyphs

_LABEL_TO_GLYPH = {
    "character_1_ka": "क", "character_2_kha": "ख", "character_3_ga": "ग",
    "character_4_gha": "घ", "character_5_kna": "ङ", "character_6_cha": "च",
    "character_7_chha": "छ", "character_8_ja": "ज", "character_9_jha": "झ",
    "character_10_yna": "ञ", "character_11_taamatar": "ट", "character_12_thaa": "ठ",
    "character_13_daa": "ड", "character_14_dhaa": "ढ", "character_15_adna": "ण",
    "character_16_tabala": "त", "character_17_tha": "थ", "character_18_da": "द",
    "character_19_dha": "ध", "character_20_na": "न", "character_21_pa": "प",
    "character_22_pha": "फ", "character_23_ba": "ब", "character_24_bha": "भ",
    "character_25_ma": "म", "character_26_yaw": "य", "character_27_ra": "र",
    "character_28_la": "ल", "character_29_waw": "व", "character_30_motosaw": "श",
    "character_31_petchiryakha": "ष", "character_32_patalosaw": "स",
    "character_33_ha": "ह", "character_34_chhya": "क्ष", "character_35_tra": "त्र",
    "character_36_gya": "ज्ञ",
    "digit_0": "०", "digit_1": "१", "digit_2": "२", "digit_3": "३", "digit_4": "४",
    "digit_5": "५", "digit_6": "६", "digit_7": "७", "digit_8": "८", "digit_9": "९",
}

# Primary interface — class name → glyph (returns '' for unknown classes)
def class_to_glyph(cls: str) -> str:
    return _LABEL_TO_GLYPH.get(cls, "")

# Also expose idx_to_char for direct index lookups
from ml_models.char_map import idx_to_char  # noqa: E402
