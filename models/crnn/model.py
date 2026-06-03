import torch
import torch.nn as nn
import torch.nn.functional as F


class CRNN(nn.Module):
    """
    CNN-RNN-CTC for character recognition.
    Input: (B, 1, 64, W) where W varies (padded to max in batch)
    Output: (T, B, num_chars) logits for CTC loss
    """

    def __init__(self, num_classes, hidden_size=256):
        super(CRNN, self).__init__()
        self.num_classes = num_classes
        self.hidden_size = hidden_size

        # CNN backbone: extract features from 64-height images
        # Keep height = 1 after pooling (H dimension), vary width
        self.cnn = nn.Sequential(
            # Conv1: 1 -> 32 channels
            nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # H: 64->32, W: W->W/2

            # Conv2: 32 -> 64 channels
            nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # H: 32->16, W: W/2->W/4

            # Conv3: 64 -> 128 channels
            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(2, 1), stride=(2, 1)),  # H: 16->8, W: W/4

            # Conv4: 128 -> 256 channels
            nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
        )

        # After CNN: features have shape (B, 256, 8, W/4)
        # Reshape to (B, 256*8, W/4) = (B, 2048, W/4) for RNN

        # RNN: BiLSTM for sequence modeling
        self.rnn = nn.LSTM(
            input_size=256 * 8,
            hidden_size=hidden_size,
            num_layers=2,
            bidirectional=True,
            batch_first=False
        )

        # Output layer: (2*hidden_size) -> num_classes
        self.fc = nn.Linear(2 * hidden_size, num_classes)

    def forward(self, images):
        """
        Args:
            images: (B, 1, 64, W) tensor

        Returns:
            logits: (T, B, num_classes) for CTC loss
        """
        # CNN
        features = self.cnn(images)  # (B, 256, 8, W')

        # Reshape for RNN: (B, 256, 8, W') -> (B, 256*8, W') -> (W', B, 256*8)
        b, c, h, w = features.shape
        features = features.view(b, c * h, w)  # (B, 2048, W')
        features = features.permute(2, 0, 1)  # (W', B, 2048)

        # RNN
        rnn_out, _ = self.rnn(features)  # (T, B, 2*hidden_size)

        # FC + log_softmax (CTCLoss expects log-probabilities, not raw logits)
        logits = self.fc(rnn_out)  # (T, B, num_classes)
        log_probs = F.log_softmax(logits, dim=2)

        return log_probs


def decode_ctc_greedy(logits, charset, blank_idx=None):
    """
    Greedy CTC decoding: argmax per timestep, collapse blanks/repeats.

    Args:
        logits: (T, B, num_classes) or (B, T, num_classes)
        charset: list of characters/class names
        blank_idx: CTC blank token index (default: last index)

    Returns:
        list of decoded strings
    """
    if logits.dim() == 3 and logits.shape[0] != len(charset):
        # Assume (B, T, num_classes), convert to (T, B, num_classes)
        logits = logits.permute(1, 0, 2)

    if blank_idx is None:
        blank_idx = len(charset)

    pred_ids = torch.argmax(logits, dim=2)  # (T, B)

    batch_size = pred_ids.shape[1]
    decoded = []

    for b in range(batch_size):
        seq = pred_ids[:, b].cpu().numpy()
        result = []
        prev = None
        for idx in seq:
            if idx != blank_idx and idx != prev:
                result.append(charset[int(idx)])
            prev = idx
        decoded.append("_".join(result))

    return decoded
