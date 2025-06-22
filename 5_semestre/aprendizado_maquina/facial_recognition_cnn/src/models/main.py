import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
import matplotlib.pyplot as plt
from tqdm import tqdm
import numpy as np
import argparse
from torchvision import transforms
from PIL import Image
from torch.utils.data import Dataset
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model import create_cnn_model
from model_results import FaceRecognitionMetrics
from config import PATHS, MODEL_CONFIG

class FaceRecognitionDataset(Dataset):
    def __init__(self, data_dir, transform=None):
        self.data_dir = data_dir
        self.transform = transform or transforms.Compose([
            transforms.Resize(MODEL_CONFIG['image_size']),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        self.images = []
        self.labels = []
        self.class_map = {}
        
        expected_classes = MODEL_CONFIG['expected_classes']
        
        for idx, class_name in enumerate(expected_classes):
            self.class_map[class_name] = idx
        
        print(f"Initialized class mapping: {self.class_map}")
        
        for filename in os.listdir(data_dir):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                person_name = self.extract_person_name(filename)
                
                if person_name in self.class_map:
                    self.images.append(os.path.join(data_dir, filename))
                    self.labels.append(self.class_map[person_name])
                else:
                    print(f"Warning: Unknown person '{person_name}' in file {filename}")
        
        print(f"Loaded {len(self.images)} images from {len(set(self.labels))} classes")
    
    def extract_person_name(self, filename):
        name_without_ext = os.path.splitext(filename)[0]
        parts = name_without_ext.split('_')
        
        for i in range(len(parts) - 1, -1, -1):
            try:
                int(parts[i])
                return '_'.join(parts[:i])
            except ValueError:
                continue
        
        return name_without_ext
    
    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, idx):
        img_path = self.images[idx]
        label = self.labels[idx]
        
        image = Image.open(img_path).convert('RGB')
        if self.transform:
            image = self.transform(image)
        
        return image, label
    
    def get_num_classes(self):
        return len(self.class_map)
    
    def get_class_names(self):
        return [k for k, v in sorted(self.class_map.items(), key=lambda item: item[1])]

def debug_dataset_files(data_dir):
    print(f"\n🔍 DEBUG - Analyzing files in {data_dir}")
    
    files_by_person = {}
    
    for filename in os.listdir(data_dir):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            name_without_ext = os.path.splitext(filename)[0]
            parts = name_without_ext.split('_')
            
            person_name = name_without_ext
            for i in range(len(parts) - 1, -1, -1):
                try:
                    int(parts[i])
                    person_name = '_'.join(parts[:i])
                    break
                except ValueError:
                    continue
            
            if person_name not in files_by_person:
                files_by_person[person_name] = []
            files_by_person[person_name].append(filename)
    
    print("📊 Files found by person:")
    for person, files in files_by_person.items():
        print(f"   - {person}: {len(files)} files")
        if len(files) <= 3:
            for file in files[:3]:
                print(f"     * {file}")
    
    expected_classes = MODEL_CONFIG['expected_classes']
    found_classes = set(files_by_person.keys())
    
    print(f"\n✅ Expected classes: {expected_classes}")
    print(f"📋 Found classes: {sorted(found_classes)}")
    
    missing = set(expected_classes) - found_classes
    extra = found_classes - set(expected_classes)
    
    if missing:
        print(f"⚠️  Missing classes: {missing}")
    if extra:
        print(f"⚠️  Extra classes found: {extra}")
    
    return files_by_person

def train_model(model, train_loader, val_loader, num_epochs, device, learning_rate=0.001):
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    train_losses = []
    val_losses = []
    val_accuracies = []
    
    best_val_acc = 0.0
    best_model_state = None
    
    print(f"Training on {device}...")
    
    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0
        
        progress_bar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{num_epochs} [Train]")
        for inputs, labels in progress_bar:
            inputs, labels = inputs.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item() * inputs.size(0)
            progress_bar.set_postfix(loss=loss.item())
            
        epoch_loss = running_loss / len(train_loader.dataset)
        train_losses.append(epoch_loss)
        
        model.eval()
        val_loss = 0.0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for inputs, labels in tqdm(val_loader, desc=f"Epoch {epoch+1}/{num_epochs} [Val]"):
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                
                val_loss += loss.item() * inputs.size(0)
                
                _, predicted = torch.max(outputs, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
                
        val_loss = val_loss / len(val_loader.dataset)
        val_accuracy = correct / total
        
        val_losses.append(val_loss)
        val_accuracies.append(val_accuracy)
        
        print(f"Epoch {epoch+1}/{num_epochs} - "
              f"Train Loss: {epoch_loss:.4f}, "
              f"Val Loss: {val_loss:.4f}, "
              f"Val Acc: {val_accuracy:.4f}")
        
        if val_accuracy > best_val_acc:
            best_val_acc = val_accuracy
            best_model_state = model.state_dict().copy()
    
    if best_model_state:
        model.load_state_dict(best_model_state)
        
    plt.figure(figsize=(12, 4))
    
    plt.subplot(1, 2, 1)
    plt.plot(train_losses, label='Train Loss')
    plt.plot(val_losses, label='Validation Loss')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()
    
    plt.subplot(1, 2, 2)
    plt.plot(val_accuracies, label='Validation Accuracy')
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.legend()
    
    plt.tight_layout()
    
    return model, train_losses, val_losses, val_accuracies

def main():
    parser = argparse.ArgumentParser(description="Facial Recognition CNN Training")
    parser.add_argument("--epochs", type=int, default=MODEL_CONFIG['num_epochs'], help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=MODEL_CONFIG['batch_size'], help="Batch size for training")
    parser.add_argument("--learning-rate", type=float, default=MODEL_CONFIG['learning_rate'], help="Learning rate")
    parser.add_argument("--no-cuda", action="store_true", help="Disable CUDA acceleration")
    args = parser.parse_args()
    
    augmented_data_dir = os.path.join(PATHS['data_dir'], 'data_augmented')
    original_data_dir = os.path.join(PATHS['data_dir'], 'data_processed')
    model_dir = PATHS['models']
    results_dir = PATHS['results']

    if not os.path.isdir(augmented_data_dir):
        raise FileNotFoundError(f"Augmented data directory not found: {augmented_data_dir}")
    if not os.path.isdir(original_data_dir):
        raise FileNotFoundError(f"Original data directory not found: {original_data_dir}")
    
    for directory in [model_dir, results_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    
    device = torch.device('cpu' if args.no_cuda or not torch.cuda.is_available() else 'cuda')
    
    print("=" * 60)
    debug_dataset_files(augmented_data_dir)
    debug_dataset_files(original_data_dir)
    print("=" * 60)
    
    print(f"Loading augmented dataset from {augmented_data_dir}...")
    train_dataset = FaceRecognitionDataset(augmented_data_dir)
    
    print(f"Loading original dataset from {original_data_dir}...")
    test_dataset = FaceRecognitionDataset(original_data_dir)
    
    num_classes = train_dataset.get_num_classes()
    class_names = train_dataset.get_class_names()
    
    print(f"Dataset loaded with {num_classes} classes: {', '.join(class_names)}")
    print(f"Training samples: {len(train_dataset)}, Test samples: {len(test_dataset)}")
    
    train_size = int(0.8 * len(train_dataset))
    val_size = len(train_dataset) - train_size
    train_subset, val_subset = random_split(train_dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_subset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_subset, batch_size=args.batch_size)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size)
    
    model = create_cnn_model(input_shape=(3, 128, 128), num_classes=num_classes)
    model = model.to(device)
    
    print(f"Model created with {num_classes} output classes.")
    
    model, train_losses, val_losses, val_accuracies = train_model(
        model, train_loader, val_loader, 
        num_epochs=args.epochs, 
        device=device, 
        learning_rate=args.learning_rate
    )
    
    model_path = os.path.join(model_dir, "face_recognition_model.pth")
    torch.save({
        'model_state_dict': model.state_dict(),
        'class_names': class_names,
        'num_classes': num_classes
    }, model_path)
    print(f"Model saved to {model_path}")
    
    plt.figure(figsize=(12, 4))
    
    plt.subplot(1, 2, 1)
    plt.plot(train_losses, label='Train Loss')
    plt.plot(val_losses, label='Validation Loss')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()
    
    plt.subplot(1, 2, 2)
    plt.plot(val_accuracies, label='Validation Accuracy')
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, "training_history.png"))
    
    print("\nEvaluating model on test data...")
    metrics = FaceRecognitionMetrics(device=device)
    metrics.load_model(model_path)
    
    results = metrics.evaluate_model(test_loader)
    print(f"\nTest Results:")
    print(f"Accuracy: {results['accuracy']:.4f}")
    print(f"Precision: {results['precision']:.4f}")
    print(f"Recall: {results['recall']:.4f}")
    print(f"F1 Score: {results['f1']:.4f}")
    
    metrics.print_classification_report()
    
    metrics.plot_confusion_matrix(save_path=os.path.join(results_dir, "confusion_matrix.png"))
    
    metrics.plot_sample_predictions(test_loader, num_samples=5, 
                               save_path=os.path.join(results_dir, "sample_predictions.png"))
    
    metrics.export_results(os.path.join(results_dir, "metrics"))
    
    print(f"\nTraining and evaluation complete. Results saved to {results_dir}")

if __name__ == "__main__":
    main()