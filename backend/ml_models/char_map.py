# DHCD dataset charset — 46 character classes, CTC blank at index 46
CHARS = [
    "character_10_yna", "character_11_taamatar", "character_12_thaa",
    "character_13_daa", "character_14_dhaa", "character_15_adna",
    "character_16_tabala", "character_17_tha", "character_18_da",
    "character_19_dha", "character_1_ka", "character_20_na",
    "character_21_pa", "character_22_pha", "character_23_ba",
    "character_24_bha", "character_25_ma", "character_26_yaw",
    "character_27_ra", "character_28_la", "character_29_waw",
    "character_2_kha", "character_30_motosaw", "character_31_petchiryakha",
    "character_32_patalosaw", "character_33_ha", "character_34_chhya",
    "character_35_tra", "character_36_gya", "character_3_ga",
    "character_4_gha", "character_5_kna", "character_6_cha",
    "character_7_chha", "character_8_ja", "character_9_jha",
    "digit_0", "digit_1", "digit_2", "digit_3", "digit_4",
    "digit_5", "digit_6", "digit_7", "digit_8", "digit_9",
]

BLANK_IDX = 46
NUM_CLASSES = 47  # 46 chars + 1 blank

char_to_idx = {c: i for i, c in enumerate(CHARS)}

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

idx_to_char = {i: _LABEL_TO_GLYPH[c] for i, c in enumerate(CHARS)}
