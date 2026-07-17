# EDA Summary — Devanagari Character Dataset

- **Total images:** 92,000
- **Classes:** 46 (36 consonants + 10 digits)
- **Split:** train 73,609 / val 9,191 / test 9,200
- **Per-class total range:** 2000–2000 (imbalance ratio 1.00×)
- **Image size:** width 64–64 px, height 64–64 px (median 64×64)

## Class imbalance check
Near-balanced — every class has a similar count, so no resampling/weighting is required. (Ratio close to 1.0 means balanced.)

## Most / least represented classes
```
class
character_10_yna      2000
character_8_ja        2000
character_33_ha       2000
character_34_chhya    2000
character_35_tra      2000
...
class
character_10_yna      2000
character_33_ha       2000
character_34_chhya    2000
character_35_tra      2000
character_36_gya      2000
```

Artifacts: `class_counts.csv`, `class_distribution.png`, `image_size_distribution.png`, `sample_grid.png`.