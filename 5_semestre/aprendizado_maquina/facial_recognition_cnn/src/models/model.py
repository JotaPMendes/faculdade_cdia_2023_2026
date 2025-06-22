import torch
import torch.nn as nn
import numpy as np

class FaceRecognitionCNN(nn.Module):
    def __init__(self, num_classes, dropout_rate=0.5):
        super(FaceRecognitionCNN, self).__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),  # (B, 32, 128, 128)
            nn.ReLU(),
            nn.BatchNorm2d(32),
            nn.MaxPool2d(2),  # (B, 32, 64, 64)

            nn.Conv2d(32, 64, kernel_size=3, padding=1),  # (B, 64, 64, 64)
            nn.ReLU(),
            nn.BatchNorm2d(64),
            nn.MaxPool2d(2),  # (B, 64, 32, 32)

            nn.Conv2d(64, 128, kernel_size=3, padding=1),  # (B, 128, 32, 32)
            nn.ReLU(),
            nn.BatchNorm2d(128),
            nn.MaxPool2d(2),  # (B, 128, 16, 16)
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * 16 * 16, 512),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(512, num_classes)
        )

    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x

def create_cnn_model(input_shape, num_classes):
    # input_shape esperado: (C, H, W), por exemplo (3, 128, 128)
    model = FaceRecognitionCNN(num_classes)
    return model