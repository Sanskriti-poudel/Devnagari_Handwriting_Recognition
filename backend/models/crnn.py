"""
CRNN (CNN + Bidirectional LSTM + CTC) for Devanagari handwriting recognition.

Input:  (batch, 1, IMG_HEIGHT, W) — greyscale, fixed height, variable width
Output: (T, batch, num_classes)   — log-softmax over vocab, fed into CTCLoss

Architecture follows Shi et al. "An End-to-End Trainable Neural Network for
Image-based Sequence Recognition" (2015), adapted for 32-px input height.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

IMG_HEIGHT = 32  # must match preprocessing


class _BidirectionalLSTM(nn.Module):
    def __init__(self, in_size: int, hidden: int, out_size: int):
        super().__init__()
        self.lstm = nn.LSTM(in_size, hidden, bidirectional=True, batch_first=False)
        self.linear = nn.Linear(hidden * 2, out_size)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.linear(out)


class CRNN(nn.Module):
    def __init__(self, num_classes: int, img_height: int = IMG_HEIGHT):
        super().__init__()

        # CNN backbone — collapses spatial height to 1 while preserving width sequence
        self.cnn = nn.Sequential(
            # (B, 1, H, W) → (B, 64, H/2, W/2)
            nn.Conv2d(1, 64, 3, padding=1), nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            # → (B, 128, H/4, W/4)
            nn.Conv2d(64, 128, 3, padding=1), nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            # → (B, 256, H/8, W/4)
            nn.Conv2d(128, 256, 3, padding=1), nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, 3, padding=1), nn.ReLU(inplace=True),
            nn.MaxPool2d((2, 1)),
            # → (B, 512, H/16, W/4)
            nn.Conv2d(256, 512, 3, padding=1), nn.BatchNorm2d(512), nn.ReLU(inplace=True),
            nn.Conv2d(512, 512, 3, padding=1), nn.BatchNorm2d(512), nn.ReLU(inplace=True),
            nn.MaxPool2d((2, 1)),
            # → (B, 512, 1, W/4) — final conv collapses remaining height
            nn.Conv2d(512, 512, (img_height // 16, 1)), nn.ReLU(inplace=True),
        )

        # Recurrent layers
        self.rnn = nn.Sequential(
            _BidirectionalLSTM(512, 256, 256),
            _BidirectionalLSTM(256, 256, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        features = self.cnn(x)           # (B, 512, 1, T)
        features = features.squeeze(2)   # (B, 512, T)
        features = features.permute(2, 0, 1)  # (T, B, 512)
        out = self.rnn(features)          # (T, B, num_classes)
        return F.log_softmax(out, dim=2)
