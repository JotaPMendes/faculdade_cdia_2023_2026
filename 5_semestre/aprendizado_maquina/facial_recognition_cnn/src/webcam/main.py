import os
import cv2
import torch
import numpy as np
from torchvision import transforms
from PIL import Image
import time
import sys
import datetime
import uuid

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models'))

from models.model import create_cnn_model
from models.model_results import FaceRecognitionMetrics


class FaceRecognitionWebcam:
    def __init__(self, model_path, confidence_threshold=0.7, capture_faces=True, capture_interval=2.0):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Using device: {self.device}")
        
        self.load_model(model_path)
        
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        self.transform = transforms.Compose([
            transforms.Resize((128, 128)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        self.confidence_threshold = confidence_threshold
        
        self.capture_faces = capture_faces
        self.capture_interval = capture_interval
        self.last_capture_time = {}
        
        if self.capture_faces:
            current_file_path = os.path.abspath(__file__)
            webcam_dir = os.path.dirname(current_file_path)
            src_dir = os.path.dirname(webcam_dir)
            project_root = os.path.dirname(src_dir)
            
            self.capture_dir = os.path.join(project_root, "data", "captured_faces")
            os.makedirs(self.capture_dir, exist_ok=True)
            
            print(f"Faces capturadas serão salvas em: {self.capture_dir}")
    
    def load_model(self, model_path):
        try:
            checkpoint = torch.load(model_path, map_location=self.device)
            num_classes = checkpoint['num_classes']
            self.class_names = checkpoint['class_names']
            
            self.model = create_cnn_model(input_shape=(3, 128, 128), num_classes=num_classes)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.model.to(self.device)
            self.model.eval()
            
            print(f"Modelo carregado com sucesso com {num_classes} classes")
            print(f"Classes: {', '.join(self.class_names)}")
        except Exception as e:
            print(f"Erro ao carregar o modelo: {str(e)}")
            sys.exit(1)
    
    def predict_face(self, face_img):
        pil_img = Image.fromarray(cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB))
        
        input_tensor = self.transform(pil_img)
        input_batch = input_tensor.unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(input_batch)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)[0]
            
        max_prob, pred_idx = torch.max(probabilities, 0)
        predicted_class = self.class_names[pred_idx.item()]
        confidence = max_prob.item()
        
        return predicted_class, confidence
    
    def save_face(self, face_img, person_name, confidence):
        if not self.capture_faces:
            return False
            
        current_time = time.time()
        
        if person_name in self.last_capture_time:
            if current_time - self.last_capture_time[person_name] < self.capture_interval:
                return False
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:6]
        
        confidence_tag = "high" if confidence > self.confidence_threshold else "low"
        filename = f"face_{timestamp}_{unique_id}_pred_{person_name}_{confidence:.2f}_{confidence_tag}.jpg"
        
        save_path = os.path.join(self.capture_dir, filename)
        cv2.imwrite(save_path, face_img)
        
        self.last_capture_time[person_name] = current_time
        
        return True
    
    def run(self, camera_id=0, window_name="Reconhecimento Facial"):
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            print("Erro ao abrir a webcam")
            return
        
        frame_times = []
        start_time = time.time()
        fps_update_interval = 1.0
        last_fps_update = start_time
        current_fps = 0
        
        total_faces_detected = 0
        total_faces_saved = 0
        
        print("Pressione 'q' para sair, 'c' para capturar face manualmente")
        
        while True:
            frame_start = time.time()
            
            ret, frame = cap.read()
            if not ret:
                print("Erro ao capturar o frame")
                break
            
            display_frame = frame.copy()
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 5)
            
            for (x, y, w, h) in faces:
                expansion = int(w * 0.1)
                x = max(0, x - expansion)
                y = max(0, y - expansion)
                w += 2 * expansion
                h += 2 * expansion
                
                face = frame[y:y+h, x:x+w]
                
                if face.size == 0:
                    continue
                
                total_faces_detected += 1
                
                try:
                    predicted_class, confidence = self.predict_face(face)
                    
                    face_saved = self.save_face(face, predicted_class, confidence)
                    if face_saved:
                        total_faces_saved += 1
                    
                    if confidence > self.confidence_threshold:
                        color = (0, 255, 0)
                        display_text = f"{predicted_class} ({confidence:.2f})"
                    else:
                        color = (0, 165, 255)
                        display_text = f"Desconhecido ({confidence:.2f})"
                    
                    if face_saved:
                        cv2.rectangle(display_frame, (x, y), (x+w, y+h), color, 3)
                        display_text += " [Salva]"
                    else:
                        cv2.rectangle(display_frame, (x, y), (x+w, y+h), color, 2)
                    
                    cv2.putText(display_frame, display_text, (x, y-10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                except Exception as e:
                    print(f"Erro ao processar face: {str(e)}")
            
            frame_end = time.time()
            frame_time = frame_end - frame_start
            frame_times.append(frame_time)
            
            if frame_end - last_fps_update > fps_update_interval:
                recent_times = frame_times[-10:]
                if recent_times:
                    current_fps = 1.0 / (sum(recent_times) / len(recent_times))
                last_fps_update = frame_end
            
            cv2.putText(display_frame, f"FPS: {current_fps:.1f}", (10, 30),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            if self.capture_faces:
                cv2.putText(display_frame, f"Faces salvas: {total_faces_saved}", (10, 60),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            cv2.imshow(window_name, display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('c') and len(faces) > 0:
                for (x, y, w, h) in faces:
                    expansion = int(w * 0.1)
                    x = max(0, x - expansion)
                    y = max(0, y - expansion)
                    w += 2 * expansion
                    h += 2 * expansion
                    face = frame[y:y+h, x:x+w]
                    if face.size > 0:
                        try:
                            predicted_class, confidence = self.predict_face(face)
                            self.last_capture_time[predicted_class] = 0
                            if self.save_face(face, predicted_class, confidence):
                                print(f"Face capturada manualmente: {predicted_class} ({confidence:.2f})")
                                total_faces_saved += 1
                        except Exception as e:
                            print(f"Erro ao processar captura manual: {str(e)}")
        
        cap.release()
        cv2.destroyAllWindows()
        
        print(f"\nResumo da sessão:")
        print(f"- Faces detectadas: {total_faces_detected}")
        print(f"- Faces salvas para treinamento: {total_faces_saved}")
        print(f"- Arquivos salvos em: {self.capture_dir}")

def main():
    print("Iniciando sistema de reconhecimento facial...")
    
    current_file_path = os.path.abspath(__file__)
    webcam_dir = os.path.dirname(current_file_path)
    src_dir = os.path.dirname(webcam_dir)
    project_root = os.path.dirname(src_dir)
    
    model_path = os.path.join(src_dir, "models", "face_recognition_model.pth")
    print(f"Procurando modelo em: {model_path}")
    
    if not os.path.exists(model_path):
        print(f"Modelo não encontrado em: {model_path}")
        print("Por favor, treine o modelo primeiro usando main.py")
        return
    
    print("Modelo encontrado. Inicializando...")
    
    try:
        face_recognition = FaceRecognitionWebcam(
            model_path=model_path,
            confidence_threshold=0.7,
            capture_faces=True,
            capture_interval=2.0
        )
        print("Iniciando detecção...")
        face_recognition.run()
    except Exception as e:
        print(f"Erro durante execução: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()