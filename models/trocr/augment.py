"""
Train-only data augmentation (proposal section 3.2.3): rotation, scaling,
translation, and slight distortion (shear). Applied to the PIL image BEFORE the
TrOCR processor resizes/normalizes it. Validation and test images are never
augmented, so reported metrics reflect clean inputs.

Kept deliberately mild — Devanagari characters are sensitive to orientation and
the *shirorekha* (top bar), so heavy rotation/distortion would change identity.
"""

from torchvision import transforms


def build_train_augment():
    """Return a callable PIL.Image -> PIL.Image applying mild affine jitter."""
    return transforms.RandomAffine(
        degrees=5,                 # rotation: characters are orientation-sensitive
        translate=(0.05, 0.05),    # small shifts
        scale=(0.9, 1.1),          # zoom in/out
        shear=5,                   # slight distortion
        fill=0,                    # pad with background (black, foreground is white)
    )
