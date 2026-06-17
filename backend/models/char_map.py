"""
Devanagari character vocabulary for CTC-based OCR.
Index 0 is the CTC blank token; all other indices map to Unicode characters.
"""

DEVANAGARI_CHARS = [
    # Vowels
    'अ', 'आ', 'इ', 'ई', 'उ', 'ऊ', 'ऋ', 'ए', 'ऐ', 'ओ', 'औ',
    # Consonants
    'क', 'ख', 'ग', 'घ', 'ङ',
    'च', 'छ', 'ज', 'झ', 'ञ',
    'ट', 'ठ', 'ड', 'ढ', 'ण',
    'त', 'थ', 'द', 'ध', 'न',
    'प', 'फ', 'ब', 'भ', 'म',
    'य', 'र', 'ल', 'व',
    'श', 'ष', 'स', 'ह',
    # Vowel diacritics (matras)
    'ा', 'ि', 'ी', 'ु', 'ू', 'ृ', 'े', 'ै', 'ो', 'ौ', '्',
    # Anusvara, Visarga, Chandrabindu
    'ं', 'ः', 'ँ',
    # Devanagari digits
    '०', '१', '२', '३', '४', '५', '६', '७', '८', '९',
    # Space
    ' ',
]

BLANK_INDEX = 0
VOCAB = ['<BLANK>'] + DEVANAGARI_CHARS
NUM_CLASSES = len(VOCAB)

char_to_idx: dict[str, int] = {c: i for i, c in enumerate(VOCAB)}
idx_to_char: dict[int, str] = {i: c for i, c in enumerate(VOCAB)}


def encode(text: str) -> list[int]:
    return [char_to_idx[c] for c in text if c in char_to_idx]


def decode(indices: list[int]) -> str:
    return ''.join(idx_to_char.get(i, '') for i in indices if i != BLANK_INDEX)
