# -*- coding: utf-8 -*-
"""fine tunel model

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1wCaXxX6Kr0iMUeRr5SKYRp_YZhp8vYyi
"""

import os
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import load_model
from tensorflow.keras.optimizers import Adam

def fine_tune_model(model_path, data_dir, image_size=(128,128), batch_size=32, learning_rate=1e-4, epochs=10):
    print(f"Carregando modelo de {model_path}...")
    model = load_model(model_path)

    datagen = ImageDataGenerator(rescale=1./255,
                                 validation_split=0.2,
                                 horizontal_flip=True,
                                 rotation_range=20)

    train_gen = datagen.flow_from_directory(
        data_dir,
        target_size=image_size,
        batch_size=batch_size,
        subset='training',
        class_mode='categorical',
        shuffle=True
    )

    val_gen = datagen.flow_from_directory(
        data_dir,
        target_size=image_size,
        batch_size=batch_size,
        subset='validation',
        class_mode='categorical',
        shuffle=True
    )

    model.compile(optimizer=Adam(learning_rate=learning_rate),
                  loss='categorical_crossentropy',
                  metrics=['accuracy'])

    model.fit(train_gen,
              epochs=epochs,
              validation_data=val_gen)

    model.save(model_path)
    print(f"Modelo atualizado salvo em {model_path}")