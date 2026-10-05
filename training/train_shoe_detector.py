#!/usr/bin/env python3
"""Train ResNet18 shoe detection model for assistive follower robot."""

import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import models, transforms
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import cv2
from pathlib import Path
from sklearn.model_selection import train_test_split


class ShoeDataset(Dataset):
    def __init__(self, csv_path, img_dir, transform=None):
        self.df = pd.read_csv(csv_path)
        self.img_dir = Path(img_dir)
        self.transform = transform

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img = cv2.imread(str(self.img_dir / row["filename"]))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        if self.transform:
            img = self.transform(img)
        target = torch.tensor(
            [
                row["x_offset_norm"],
                row["z_distance_norm"],
                row["sin_theta"],
                row["cos_theta"],
            ],
            dtype=torch.float32,
        )
        return img, target


def main():
    transform = transforms.Compose(
        [
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )

    # Check if data directory exists
    data_dir = Path("data")
    annotations_path = data_dir / "annotations.csv"
    images_dir = data_dir / "images"
    
    if not annotations_path.exists():
        raise FileNotFoundError(
            f"Annotations file not found: {annotations_path}\n"
            "Please prepare your dataset following docs/dataset_preparation.md"
        )
    if not images_dir.exists():
        raise FileNotFoundError(f"Images directory not found: {images_dir}")

    dataset = ShoeDataset(str(annotations_path), str(images_dir), transform)
    train_idx, val_idx = train_test_split(
        range(len(dataset)), test_size=0.2, random_state=42
    )
    train_loader = DataLoader(
        torch.utils.data.Subset(dataset, train_idx), batch_size=32, shuffle=True
    )
    val_loader = DataLoader(torch.utils.data.Subset(dataset, val_idx), batch_size=32)

    model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
    model.fc = nn.Linear(model.fc.in_features, 4)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    criterion = nn.MSELoss()
    optimizer = optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5)

    best_val = float("inf")
    for epoch in range(100):
        model.train()
        train_loss = 0
        for imgs, targets in train_loader:
            imgs, targets = imgs.to(device), targets.to(device)
            optimizer.zero_grad()
            loss = criterion(model(imgs), targets)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

        model.eval()
        val_loss = 0
        with torch.no_grad():
            for imgs, targets in val_loader:
                imgs, targets = imgs.to(device), targets.to(device)
                val_loss += criterion(model(imgs), targets).item()

        train_loss /= len(train_loader)
        val_loss /= len(val_loader)
        scheduler.step(val_loss)

        print(f"Epoch {epoch:3d} | Train: {train_loss:.6f} | Val: {val_loss:.6f}")

        if val_loss < best_val:
            best_val = val_loss
            torch.save(model.state_dict(), "shoe_model.pth")
            print(f"  Saved best model (val_loss={val_loss:.6f})")
            print(f"  Copy to ROS package with: cp shoe_model.pth ../my_nodes/models/")

    print(f"\nTraining complete. Best val loss: {best_val:.6f}")
    print("Deploy model: cp shoe_model.pth ../my_nodes/models/shoe_model.pth")


if __name__ == "__main__":
    main()
