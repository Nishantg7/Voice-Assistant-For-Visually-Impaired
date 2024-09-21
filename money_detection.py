import cv2
import tkinter as tk
from PIL import Image, ImageTk
from ultralytics import YOLO
import pyttsx3

class YOLOWithWebcamUI:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)

        # Initialize YOLO model
        self.model = YOLO("rupee.pt")
        self.classNames = ['10', '100', '20', '200', '2000', '50', '500']
        self.engine = pyttsx3.init()

        # Create a label for displaying the video feed
        self.label = tk.Label(window)
        self.label.pack()

        # Button to capture image
        self.btn_capture = tk.Button(window, text="Capture Image", width=50, command=self.capture_image)
        self.btn_capture.pack()

        # Open the webcam
        self.cap = cv2.VideoCapture(0)
        self.update()

        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.mainloop()

    def update(self):
        # Read frame from webcam
        ret, frame = self.cap.read()
        if ret:
            # Convert frame from BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Convert frame to PIL format
            img = Image.fromarray(rgb_frame)
            img.thumbnail((640, 480))  # Resize image to fit window
            # Convert PIL image to Tkinter format
            img_tk = ImageTk.PhotoImage(image=img)
            # Update label with new image
            self.label.img_tk = img_tk
            self.label.config(image=img_tk)
            # Schedule the update to happen after 10 ms
            self.window.after(10, self.update)

    def capture_image(self):
        # Read frame from webcam
        ret, frame = self.cap.read()
        if ret:
            # Perform object detection and speech synthesis on the captured image
            self.object_detection_and_speech(frame)

    def object_detection_and_speech(self, img):
        results = self.model(img, stream=True)
        detected_objects = []

        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                # Convert Tensor confidence to Python float
                confidence = round(float(box.conf[0]), 2)
                cls = int(box.cls[0])
                if 0 <= cls < len(self.classNames):
                    detected_objects.append(self.classNames[cls])
                    org = [x1, y1]
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    fontScale = 1
                    color = (255, 0, 0)
                    thickness = 2
                    cv2.putText(img, self.classNames[cls], org, font, fontScale, color, thickness)

        objects_text = ", ".join(detected_objects)
        speech_text = f"I see {objects_text}."
        self.speak(speech_text)


    def speak(self, audio):
        self.engine.say(audio)
        self.engine.runAndWait()

    def on_closing(self):
        # Release the webcam
        self.cap.release()
        # Close the application window
        self.window.destroy()

# Create a window and pass it to the YOLOWithWebcamUI class
window = tk.Tk()
YOLOWithWebcamUI(window, "YOLO with Webcam UI")
