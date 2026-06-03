import os
import json
import cv2
import torch
import numpy as np
from torch.utils.data import Dataset, DataLoader
from torch.nn.utils.rnn import pad_sequence
import sys

# Project root = two levels up from this file (models/crnn/dataset.py -> repo root)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, PROJECT_ROOT)
from Preprocessing.preprocess import preprocess_image

DEFAULT_CHARSET = os.path.join(PROJECT_ROOT, "data", "charset.json")
DEFAULT_SPLIT = os.path.join(PROJECT_ROOT, "data", "split_index.json")

# Root that split_index.json's relative paths are resolved against.
# Local default = <repo>/Datasets. On Colab/Kaggle, point it at the mounted
# data folder (which contains train/ and test/) via the env var, e.g.
#   export DEVNAGARI_DATA_ROOT=/content/drive/MyDrive/Devnagari/Preprocessed
DATA_ROOT = os.environ.get("DEVNAGARI_DATA_ROOT", os.path.join(PROJECT_ROOT, "Datasets"))


class CRNNDataset(Dataset):
    """
    Loads preprocessed character images and returns (image, label_indices).
    Handles variable-width images by padding in collate_fn.
    """

    def __init__(self, split="train", charset_path=DEFAULT_CHARSET, split_index_path=DEFAULT_SPLIT):
        """
        Args:
            split: "train", "val", or "test"
            charset_path: path to charset.json
            split_index_path: path to split_index.json
        """
        self.split = split

        # Load charset (chars are class names like "character_1_ka")
        with open(charset_path, "r", encoding="utf-8") as f:
            charset_data = json.load(f)
        self.charset = charset_data["chars"]
        self.char_to_idx = {ch: i for i, ch in enumerate(self.charset)}
        self.blank_idx = charset_data.get("blank_idx", len(self.charset))
        self.num_classes = charset_data.get("num_classes", len(self.charset) + 1)

        # Load split index
        with open(split_index_path, "r") as f:
            split_data = json.load(f)
        self.image_paths = split_data[split]

        print(f"[CRNNDataset] Loaded {len(self.image_paths)} images for split '{split}'")

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        rel_path = self.image_paths[idx]
        img_path = os.path.join(DATA_ROOT, rel_path)

        # Preprocess image (returns float32, [0, 1])
        img_array = preprocess_image(img_path)

        # Extract label from path: .../label/image.png -> label
        label = os.path.basename(os.path.dirname(rel_path))

        # Convert label (class name) to index
        if label in self.char_to_idx:
            label_indices = [self.char_to_idx[label]]
        else:
            label_indices = [0]  # Default to first class if unknown

        # Convert to tensors
        img_tensor = torch.from_numpy(img_array).unsqueeze(0)  # (1, 64, 64)
        label_tensor = torch.tensor(label_indices, dtype=torch.long)

        return img_tensor, label_tensor

    def get_charset(self):
        return self.charset

    def get_blank_idx(self):
        return self.blank_idx


def collate_crnn(batch):
    """
    Collate function for DataLoader: pad images to same width.
    Returns:
        images: (B, 1, 64, max_width)
        labels: concatenated label tensor
        label_lengths: (B,) lengths of each label
    """
    images, labels = zip(*batch)

    # Pad images to max width in batch
    images = pad_sequence(images, batch_first=True, padding_value=0)  # (B, 1, 64, W_max)

    # Flatten batch dimension back
    label_lengths = torch.tensor([len(l) for l in labels], dtype=torch.long)
    labels_flat = torch.cat(labels)

    return images, labels_flat, label_lengths


def get_crnn_dataloaders(batch_size=32, num_workers=0):
    """
    Create train/val/test dataloaders.

    Args:
        batch_size: batch size
        num_workers: number of workers for DataLoader

    Returns:
        dict: {"train": DataLoader, "val": DataLoader, "test": DataLoader}
    """
    loaders = {}
    for split in ["train", "val", "test"]:
        dataset = CRNNDataset(split=split)
        loader = DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=(split == "train"),
            collate_fn=collate_crnn,
            num_workers=num_workers
        )
        loaders[split] = loader

    return loaders
