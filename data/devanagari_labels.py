"""
Mapping from DHCD class-folder names to real Devanagari glyphs.

The CRNN baseline treats labels as opaque class names (e.g. "character_1_ka")
because CTC just needs distinct symbol ids. TrOCR, however, is a text model: its
decoder emits Unicode characters, so the training targets must be the actual
Devanagari glyphs. This module is the single source of truth for that mapping,
shared by the TrOCR dataset, evaluation, and prediction code.

Classes follow the standard Devanagari Handwritten Character Dataset (DHCD):
36 consonant classes (3 of them conjuncts) + 10 digits = 46 classes.
"""

# class-folder name -> (Devanagari glyph, latin transliteration)
CLASS_TO_DEVANAGARI = {
    "character_1_ka": ("क", "ka"),
    "character_2_kha": ("ख", "kha"),
    "character_3_ga": ("ग", "ga"),
    "character_4_gha": ("घ", "gha"),
    "character_5_kna": ("ङ", "nga"),
    "character_6_cha": ("च", "cha"),
    "character_7_chha": ("छ", "chha"),
    "character_8_ja": ("ज", "ja"),
    "character_9_jha": ("झ", "jha"),
    "character_10_yna": ("ञ", "nya"),
    "character_11_taamatar": ("ट", "ta"),
    "character_12_thaa": ("ठ", "tha"),
    "character_13_daa": ("ड", "da"),
    "character_14_dhaa": ("ढ", "dha"),
    "character_15_adna": ("ण", "ana"),
    "character_16_tabala": ("त", "ta"),
    "character_17_tha": ("थ", "tha"),
    "character_18_da": ("द", "da"),
    "character_19_dha": ("ध", "dha"),
    "character_20_na": ("न", "na"),
    "character_21_pa": ("प", "pa"),
    "character_22_pha": ("फ", "pha"),
    "character_23_ba": ("ब", "ba"),
    "character_24_bha": ("भ", "bha"),
    "character_25_ma": ("म", "ma"),
    "character_26_yaw": ("य", "ya"),
    "character_27_ra": ("र", "ra"),
    "character_28_la": ("ल", "la"),
    "character_29_waw": ("व", "wa"),
    "character_30_motosaw": ("श", "sha"),
    "character_31_petchiryakha": ("ष", "shha"),
    "character_32_patalosaw": ("स", "sa"),
    "character_33_ha": ("ह", "ha"),
    "character_34_chhya": ("क्ष", "kshya"),
    "character_35_tra": ("त्र", "tra"),
    "character_36_gya": ("ज्ञ", "gya"),
    "digit_0": ("०", "0"),
    "digit_1": ("१", "1"),
    "digit_2": ("२", "2"),
    "digit_3": ("३", "3"),
    "digit_4": ("४", "4"),
    "digit_5": ("५", "5"),
    "digit_6": ("६", "6"),
    "digit_7": ("७", "7"),
    "digit_8": ("८", "8"),
    "digit_9": ("९", "9"),
}


def class_to_glyph(class_name: str) -> str:
    """Return the Devanagari glyph for a class-folder name."""
    return CLASS_TO_DEVANAGARI[class_name][0]


def class_to_translit(class_name: str) -> str:
    """Return the latin transliteration for a class-folder name."""
    return CLASS_TO_DEVANAGARI[class_name][1]


# reverse map (glyph -> class name); glyphs are unique in DHCD
GLYPH_TO_CLASS = {g: c for c, (g, _) in CLASS_TO_DEVANAGARI.items()}
