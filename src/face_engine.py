import face_recognition
import cv2
import numpy as np
import pickle

class FaceEngine:
    DEFAULT_TOLERANCE = 0.45

    def __init__(self):
        pass

    def load_image(self, image_path):
        """Loads an image file."""
        return face_recognition.load_image_file(image_path)

    def preprocess_image(self, image):
        """Applies CLAHE to normalize lighting and enhance details."""
        if not isinstance(image, np.ndarray):
            return image
            
        # Convert to LAB to normalize L (lightness) channel
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        cl = clahe.apply(l)
        
        limg = cv2.merge((cl,a,b))
        final = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        return final

    def get_face_encodings(self, image, face_locations=None, num_jitters=1):
        """
        Returns a list of face encodings found in the image.
        """
        return face_recognition.face_encodings(image, face_locations, num_jitters=num_jitters)

    def encode_to_bytes(self, encoding):
        """Converts numpy array encoding to bytes for storage."""
        return pickle.dumps(encoding)

    def get_face_landmarks(self, image, face_locations=None):
        """Returns facial landmarks for the first face found."""
        return face_recognition.face_landmarks(image, face_locations)

    def detect_emotion(self, image, face_location):
        """
        Detects basic emotion (Happy, Neutral, Surprised) based on normalized landmarks.
        Much more robust against face distance/scale changes.
        """
        landmarks_list = face_recognition.face_landmarks(image, [face_location])
        if not landmarks_list:
            return "Neutral"
            
        landmarks = landmarks_list[0]
        
        # 1. Get Reference Dimension: Eye-to-Eye distance (Face Width baseline)
        left_eye = np.array(landmarks.get('left_eye', []))
        right_eye = np.array(landmarks.get('right_eye', []))
        
        if len(left_eye) == 0 or len(right_eye) == 0:
            return "Neutral"
            
        # Center of each eye
        left_eye_center = np.mean(left_eye, axis=0)
        right_eye_center = np.mean(right_eye, axis=0)
        face_width = np.linalg.norm(left_eye_center - right_eye_center)
        
        if face_width < 1: face_width = 1 # Avoid division by zero
        
        # 2. Analyze Mouth
        top_lip = landmarks.get('top_lip', [])
        bottom_lip = landmarks.get('bottom_lip', [])
        if not top_lip or not bottom_lip: return "Neutral"
            
        # Normalized Mouth Width
        mouth_width = np.linalg.norm(np.array(top_lip[0]) - np.array(top_lip[6]))
        mouth_width_ratio = mouth_width / face_width
        
        # Normalized Mouth Height (Openness)
        mouth_height = np.linalg.norm(np.array(top_lip[9]) - np.array(bottom_lip[9]))
        mouth_open_ratio = mouth_height / mouth_width if mouth_width > 0 else 0
        
        # 3. Analyze Eyebrows (Surprise indicator)
        left_eyebrow = landmarks.get('left_eyebrow', [])
        if left_eyebrow:
            # Distance from eye to eyebrow center normalized
            eb_center = np.mean(np.array(left_eyebrow), axis=0)
            eb_elevation = np.linalg.norm(eb_center - left_eye_center) / face_width
        else:
            eb_elevation = 0

        # --- HEURISTIC LOGIC ---
        
        # A. Surprised: Mouth open wide OR high eyebrow elevation
        if mouth_open_ratio > 0.45 or eb_elevation > 0.65:
            return "Surprised"
            
        # B. Happy: Wider mouth (ratio > 0.9) AND lifted corners
        # Note: Standard mouth_width_ratio is around 0.7-0.8
        corners_y = (top_lip[0][1] + top_lip[6][1]) / 2
        center_y = top_lip[3][1]
        corners_lifted = corners_y < center_y - (face_width * 0.02) # Lifted relative to face scale
        
        if mouth_width_ratio > 0.95 or (mouth_width_ratio > 0.85 and corners_lifted):
            return "Happy"
            
        return "Neutral"

    def decode_from_bytes(self, enc_bytes):
        """Converts bytes back to numpy array."""
        return pickle.loads(enc_bytes)

    def compare_faces(self, known_encodings, face_encoding_to_check, tolerance=None):
        if tolerance is None:
            tolerance = self.DEFAULT_TOLERANCE
        return face_recognition.compare_faces(known_encodings, face_encoding_to_check, tolerance=tolerance)

    def face_distance(self, known_encodings, face_encoding_to_check):
        """
        Returns the euclidean distance for each face.
        """
        return face_recognition.face_distance(known_encodings, face_encoding_to_check)

    def get_eye_landmarks(self, face_landmarks_list):
        """
        Extracts left and right eye points from face_landmarks_list.
        """
        if not face_landmarks_list:
            return None, None
        
        landmarks = face_landmarks_list[0] # Assume one face for EAR processing
        if 'left_eye' in landmarks and 'right_eye' in landmarks:
            return landmarks['left_eye'], landmarks['right_eye']
        return None, None

    def calculate_ear(self, eye_points):
        """
        Calculates Eye Aspect Ratio (EAR).
        Formula: (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
        """
        if len(eye_points) < 6:
            return 1.0 # Default to open if points are missing
            
        # Distances between vertical points
        A = np.linalg.norm(np.array(eye_points[1]) - np.array(eye_points[5]))
        B = np.linalg.norm(np.array(eye_points[2]) - np.array(eye_points[4]))
        
        # Distance between horizontal points
        C = np.linalg.norm(np.array(eye_points[0]) - np.array(eye_points[3]))
        
        ear = (A + B) / (2.0 * C)
        return ear

    def check_liveness(self, rgb_image, face_location):
        """
        Helper to get EAR for a face.
        Note: face_recognition.face_landmarks can be slow in real-time.
        """
        face_landmarks_list = face_recognition.face_landmarks(rgb_image, [face_location])
        left_eye, right_eye = self.get_eye_landmarks(face_landmarks_list)
        
        if left_eye and right_eye:
            left_ear = self.calculate_ear(left_eye)
            right_ear = self.calculate_ear(right_eye)
            return (left_ear + right_ear) / 2.0
        return 1.0 # Default to "open" if eyes not found
