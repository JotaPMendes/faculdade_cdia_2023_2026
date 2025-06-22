import os
import cv2
import numpy as np
from rembg import remove
import cvlib as cv

class RemoveBackgroundAndSetWhite:
    def __init__(self):
        pass

    def process(self, image):
        output = remove(image)
        if output.shape[2] == 4:
            alpha = output[:, :, 3] / 255.0
            white_bg = np.ones_like(output[:, :, :3], dtype=np.uint8) * 255
            result = output[:, :, :3] * alpha[..., None] + white_bg * (1 - alpha[..., None])
            result = result.astype(np.uint8)
        else:
            result = output
        return result

class FaceDetector:
    def __init__(self):
        self.bg_remover = RemoveBackgroundAndSetWhite()

    def detect_face(self, image):
        faces, confidences = cv.detect_face(image)
        return faces

    def crop_face(self, image, face_box):
        x1, y1, x2, y2 = face_box
        cropped_face = image[y1:y2, x1:x2]
        return cropped_face

    def preprocess_image(self, image_path, target_size=(128, 128)):
        try:
            image = cv2.imread(image_path)
            if image is None:
                print(f"Aviso: não foi possivel carregar a imagem {image_path}")
                return None, None

            image_white_bg = self.bg_remover.process(image)

            faces = self.detect_face(image_white_bg)
            if not faces:
                print(f"Aviso: nenhuma face foi detectada em {image_path}")
                return image_white_bg, None

            largest_face = max(faces, key=lambda box: (box[2] - box[0]) * (box[3] - box[1]))
            face_crop = self.crop_face(image_white_bg, largest_face)
            face_crop = cv2.resize(face_crop, target_size)
            return image_white_bg, face_crop

        except Exception as e:
            print(f"Erro ao processar a imagem {image_path}: {e}")
            return None, None

    def process_directory(self, input_dir, output_dir_whitebg, output_dir_cropped, target_size=(128, 128)):
        os.makedirs(output_dir_whitebg, exist_ok=True)
        os.makedirs(output_dir_cropped, exist_ok=True)
        image_extensions = ['.jpg', '.jpeg', '.png']
        image_files = []

        for root, _, files in os.walk(input_dir):
            for file in files:
                if any(file.lower().endswith(ext) for ext in image_extensions):
                    image_files.append(os.path.join(root, file))

        print(f"Encontradas {len(image_files)} imagens para processar.")
        processed_count = 0

        for image_path in image_files:
            filename = os.path.basename(image_path)
            output_path_whitebg = os.path.join(output_dir_whitebg, filename)
            output_path_cropped = os.path.join(output_dir_cropped, filename)
            os.makedirs(os.path.dirname(output_path_whitebg), exist_ok=True)
            os.makedirs(os.path.dirname(output_path_cropped), exist_ok=True)

            image_white_bg, face_img = self.preprocess_image(image_path, target_size)
            if image_white_bg is not None:
                cv2.imwrite(output_path_whitebg, image_white_bg)
            if face_img is not None:
                cv2.imwrite(output_path_cropped, face_img)
                processed_count += 1

        print(f"Processamento concluído. {processed_count} faces recortadas salvas.")