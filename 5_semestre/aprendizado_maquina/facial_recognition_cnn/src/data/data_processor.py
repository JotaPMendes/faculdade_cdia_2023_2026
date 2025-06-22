import os
import cv2
import numpy as np
import torch
from torch.utils.data import Dataset 
from sklearn.model_selection import train_test_split
import random
from torch.utils.data import Dataset, DataLoader


class FaceDataset(Dataset):
    def __init__(self, images, labels, transform = None):
        self.images = images
        self.labels = labels
        self.transform = transform

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        image = self.images[idx]
        label = self.labels[idx]
        if self.transform:
            image = self.transform(image)
        return image, label

class DataProcessor:
    def __init__(self, image_size = (128, 128)):
        self.image_size = image_size

    def load_data(self, data_dir):
        images = []
        labels = []
        label_mapping = {}
        person_names = {}

        image_files = [f for f in os.listdir(data_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

        if not image_files:
            print(f"Aviso: Nenhuma imagem encontrada em {data_dir}.")
            return images, labels, label_mapping

        print(f"Encontradas {len(image_files)} imagens em {data_dir}.")

        for image_file in sorted(image_files):
            try:
                name_parts = image_file.rsplit('_', 1)
                if len(name_parts) == 2 and name_parts[1].split('.')[0].isdigit():
                    person_name = name_parts[0]
                else:
                    print(f"Aviso: Nome inválido no arquivo {image_file}. Ignorando.")
                    continue

                if person_name not in person_names:
                    person_idx = len(person_names)
                    person_names[person_name] = person_idx
                    label_mapping[person_idx] = person_name

                image_path = os.path.join(data_dir, image_file)
                image = cv2.imread(image_path)
                if image is None:
                    print(f"Aviso: Não foi possível ler a imagem {image_path}.")
                    continue

                image = cv2.resize(image, self.image_size)
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                images.append(image)
                labels.append(person_names[person_name])

            except Exception as e:
                print(f"Erro ao processar {image_file}: {str(e)}")

        print(f"Carregadas {len(images)} imagens de {len(person_names)} pessoas.")

        images = np.array(images)
        labels = np.array(labels)

        return images, labels, label_mapping

    def preprocess_data(self, images, labels, test_size = 0.2, random_state = 42):
        num_classes = len(np.unique(labels))
        labels = labels.astype(np.int64)
        min_samples_per_class = np.min(np.bincount(labels))
        if test_size * len(labels) < num_classes:
            test_size = max(num_classes / len(labels), 0.1)
            print(f"Aviso: O valor de test_size foi ajustado para {test_size}.")

        X_train, X_test, y_train, y_test = train_test_split(
            images, labels, test_size=test_size, random_state=random_state, stratify=labels
        )

        X_train = torch.tensor(X_train.transpose(0, 3, 1, 2) / 255.0, dtype = torch.float32)
        X_test = torch.tensor(X_test.transpose(0, 3, 1, 2) / 255.0, dtype = torch.float32)
        y_train = torch.tensor(y_train, dtype = torch.long)
        y_test = torch.tensor(y_test, dtype = torch.long)

        train_dataset = FaceDataset(X_train, y_train)
        test_dataset = FaceDataset(X_test, y_test)

        train_loader = DataLoader(train_dataset, batch_size = 32, shuffle = True)
        test_loader = DataLoader(test_dataset, batch_size = 32, shuffle = False)

        return train_loader, test_loader, num_classes

    def apply_data_augmentation(self, images, labels, augmentation_factor = 2):
        augmented_images = []
        augmented_labels = []

        augmented_images.extend(images)
        augmented_labels.extend(labels)

        for i in range(len(images)):
            image = images[i]
            label = labels[i]

            for _ in range(augmentation_factor):
                augmented_image = image.copy()
                if random.random() > 0.5:
                    augmented_image = cv2.flip(augmented_image, 1)
                angle = random.uniform(-15, 15)
                rows, cols, _ = augmented_image.shape
                M = cv2.getRotationMatrix2D((cols / 2, rows / 2), angle, 1)
                augmented_image = cv2.warpAffine(augmented_image, M, (cols, rows))

                alpha = random.uniform(0.8, 1.2)
                beta = random.randint(-30, 30)
                augmented_image = cv2.convertScaleAbs(augmented_image, alpha=alpha, beta=beta)

                augmented_images.append(augmented_image)
                augmented_labels.append(label)

        augmented_images = np.array(augmented_images)
        augmented_labels = np.array(augmented_labels)

        print(f"Imagens geradas após aumento de dados: {len(augmented_images)}")

        return augmented_images, augmented_labels