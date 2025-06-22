import os
import torch
import numpy as np
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score, precision_score, recall_score, f1_score
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from tqdm import tqdm
from model import create_cnn_model
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MODEL_CONFIG
from model import create_cnn_model

class FaceRecognitionMetrics:
    def __init__(self, model=None, device=None):
        self.model = model
        self.device = device if device else torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.class_names = None
        self.predictions = None
        self.true_labels = None
        self.results = {}
        
    def load_model(self, model_path):
        checkpoint = torch.load(model_path, map_location=self.device)
        num_classes = checkpoint['num_classes']
        self.class_names = checkpoint['class_names']
        
        model = create_cnn_model(input_shape=(3, *MODEL_CONFIG['image_size']), num_classes=num_classes)
        model.load_state_dict(checkpoint['model_state_dict'])
        model.to(self.device)
        model.eval()
        
        self.model = model
        return model
    
    def evaluate_model(self, data_loader):
        if self.model is None:
            raise ValueError("Model is not loaded. Call load_model first.")
        
        self.model.eval()
        all_preds = []
        all_labels = []
        all_probs = []
        
        with torch.no_grad():
            for images, labels in tqdm(data_loader, desc="Evaluating"):
                images, labels = images.to(self.device), labels.to(self.device)
                outputs = self.model(images)
                probs = torch.softmax(outputs, dim=1)
                
                _, preds = torch.max(outputs, 1)
                
                all_probs.extend(probs.cpu().numpy())
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
        
        self.predictions = np.array(all_preds)
        self.true_labels = np.array(all_labels)
        self.probabilities = np.array(all_probs)
        
        # Calculate basic metrics
        self.results['accuracy'] = accuracy_score(self.true_labels, self.predictions)
        self.results['precision'] = precision_score(self.true_labels, self.predictions, average='weighted', zero_division=0)
        self.results['recall'] = recall_score(self.true_labels, self.predictions, average='weighted', zero_division=0)
        self.results['f1'] = f1_score(self.true_labels, self.predictions, average='weighted', zero_division=0)
        
        return self.results
    
    def print_classification_report(self):
        if self.predictions is None or self.true_labels is None:
            raise ValueError("No evaluation results available. Run evaluate_model first.")
            
        print("\nClassification Report:")
        print(classification_report(self.true_labels, self.predictions, 
                                   target_names=self.class_names if self.class_names else None))
        
    def plot_confusion_matrix(self, save_path=None):
        if self.predictions is None or self.true_labels is None:
            raise ValueError("No evaluation results available. Run evaluate_model first.")
            
        cm = confusion_matrix(self.true_labels, self.predictions)
        plt.figure(figsize=(10, 8))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                   xticklabels=self.class_names if self.class_names else "auto",
                   yticklabels=self.class_names if self.class_names else "auto")
        plt.xlabel('Predicted')
        plt.ylabel('True')
        plt.title('Confusion Matrix')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
            print(f"Confusion matrix saved to {save_path}")
        
        plt.show()
    
    def plot_sample_predictions(self, data_loader, num_samples=5, save_path=None):
        if self.model is None:
            raise ValueError("Model is not loaded. Call load_model first.")
            
        self.model.eval()
        
        samples_seen = 0
        plt.figure(figsize=(15, 10))
        
        for images, labels in data_loader:
            batch_size = images.size(0)
            
            images_cpu = images.numpy().transpose(0, 2, 3, 1)  
            images_cpu = np.clip((images_cpu * 0.225 + 0.45) * 255, 0, 255).astype(np.uint8)  
            
            images, labels = images.to(self.device), labels.to(self.device)
            outputs = self.model(images)
            _, preds = torch.max(outputs, 1)
            
            for i in range(batch_size):
                if samples_seen >= num_samples:
                    break
                    
                plt.subplot(1, num_samples, samples_seen + 1)
                plt.imshow(images_cpu[i])
                plt.axis('off')
                
                true_label = labels[i].item()
                pred_label = preds[i].item()
                true_name = self.class_names[true_label] if self.class_names else f"Class {true_label}"
                pred_name = self.class_names[pred_label] if self.class_names else f"Class {pred_label}"
                
                color = 'green' if true_label == pred_label else 'red'
                plt.title(f"True: {true_name}\nPred: {pred_name}", color=color)
                
                samples_seen += 1
                if samples_seen >= num_samples:
                    break
            
            if samples_seen >= num_samples:
                break
                
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
            print(f"Sample predictions saved to {save_path}")
            
        plt.show()
        
    def export_results(self, output_dir):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        metrics_df = pd.DataFrame([self.results])
        metrics_path = os.path.join(output_dir, 'model_metrics.csv')
        metrics_df.to_csv(metrics_path, index=False)
        
        cm_path = os.path.join(output_dir, 'confusion_matrix.png')
        self.plot_confusion_matrix(save_path=cm_path)
        
        report = classification_report(self.true_labels, self.predictions,
                                     target_names=self.class_names if self.class_names else None,
                                     output_dict=True)
        report_df = pd.DataFrame(report).transpose()
        report_path = os.path.join(output_dir, 'classification_report.csv')
        report_df.to_csv(report_path)
        
        print(f"Results exported to {output_dir}")
        return metrics_path, cm_path, report_path