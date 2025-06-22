import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PATHS = {
    'data_dir': os.path.join(PROJECT_ROOT, 'data'),
    'captured_faces': os.path.join(PROJECT_ROOT, 'data', 'captured_faces'),
    'processed': os.path.join(PROJECT_ROOT, 'data', 'data_processed'),
    'augmented': os.path.join(PROJECT_ROOT, 'data', 'data_augmented'),
    'models': os.path.join(PROJECT_ROOT, 'src', 'models'),
    'results': os.path.join(PROJECT_ROOT, 'src', 'results')
}

MODEL_CONFIG = {
    'expected_classes': ['leonardo', 'ana_clara', 'joao_paulo', 'matheus', 'joao_gabriel'],
    'image_size': (128, 128),
    'batch_size': 32,
    'learning_rate': 0.001,
    'num_epochs': 100
}