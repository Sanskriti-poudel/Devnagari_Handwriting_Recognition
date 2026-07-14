import torch
import torch.nn as nn
import torch.nn.functional as F


class CRNN(nn.Module):
    """
    Input:  (B, 1, 64, W) — greyscale, 64px height, variable width
    Output: (T, B, num_classes) — log-softmax for CTCLoss
    """

    def __init__(self, num_classes, hidden_size=256):
        super(CRNN, self).__init__()

        self.cnn = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),            # H: 64->32

            nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),            # H: 32->16

            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(2, 1), stride=(2, 1)), # H: 16->8

            nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
        )
        # After CNN: (B, 256, 8, W/4)

        self.rnn = nn.LSTM(
            input_size=256 * 8,
            hidden_size=hidden_size,
            num_layers=2,
            bidirectional=True,
            batch_first=False,
        )
        self.fc = nn.Linear(2 * hidden_size, num_classes)

    def forward(self, images):
        features = self.cnn(images)                              # (B, 256, 8, W')
        b, c, h, w = features.shape
        features = features.view(b, c * h, w).permute(2, 0, 1)  # (W', B, 2048)
        rnn_out, _ = self.rnn(features)                          # (T, B, 2*hidden)
        return F.log_softmax(self.fc(rnn_out), dim=2)            # (T, B, num_classes)
