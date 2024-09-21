import tkinter as tk
import pyttsx3
import threading
import speech_recognition as sr 
import datetime
import wikipedia 
import webbrowser
import os
import pywhatkit
import pyjokes
import subprocess
import time

engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)

# Flag to control whether voice assistant should listen for commands
listening_enabled = False

def speak(audio):
    engine.say(audio)
    engine.runAndWait()

def wishMe():
    hour = datetime.datetime.now().hour
    if 0 <= hour < 12:
        speak("Good Morning!")
    elif 12 <= hour < 18:
        speak("Good Afternoon!")
    else:
        speak("Good Evening!")

    speak("I am Thunder Sir. Please tell me how may I help you")

def takeCommand():
    global listening_enabled
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.pause_threshold = 0.5
        audio = r.listen(source)

    try:
        print("Recognizing...")
        query = r.recognize_google(audio, language='en-in')
        print(f"User said: {query}\n")
        return query

    except Exception as e:
        print(e)
        print("Say that again please...")
        return "None"

def start_listening():
    global listening_enabled
    listening_enabled = True
    listen_button.config(state=tk.DISABLED)
    listen_status_label.config(text="Listening...")
    thread = threading.Thread(target=voice_assistant_logic)
    thread.start()

def stop_listening():
    global listening_enabled
    listening_enabled = False
    listen_button.config(state=tk.NORMAL)
    listen_status_label.config(text="Not Listening")
    root.destroy()  # Close the Tkinter window

def voice_assistant_logic():
    global listening_enabled
    wishMe()
    while listening_enabled:
        query = takeCommand().lower()

        if 'wikipedia' in query or 'who is' in query:
            speak('Searching Wikipedia...')
            query = query.replace("wikipedia", "").strip()
            try:
                results = wikipedia.summary(query, sentences=2)
                speak("According to Wikipedia")
                print(results.encode('utf-8'))
                speak(results)
            except wikipedia.exceptions.DisambiguationError:
                speak("I'm sorry, I couldn't find specific information on that topic.")
            except wikipedia.exceptions.PageError:
                speak("I'm sorry, I couldn't find any information on that topic.")

        elif 'search on youtube' in query:
            song = query.replace('search on youtube', '')
            speak('searching' + song)
            webbrowser.open("https://www.youtube.com/results?search_query="+song)
            
        elif 'play' in query:
            song = query.replace('play', '')
            speak('playing ' + song)
            pywhatkit.playonyt(song)

        elif 'open google' in query:
            webbrowser.open("google.com")

        elif 'open stackoverflow' in query:
            webbrowser.open("stackoverflow.com")
        elif 'watch movies' in query:
            webbrowser.open("NETFLIX.com")
        
        elif 'the time' in query:
            strTime = datetime.datetime.now().strftime("%H:%M:%S")
            speak(f"Sir, the time is {strTime}")

        elif 'open code' in query:
            codePath = "D:/CODING/New folder/voice.py"
            os.startfile(codePath)

        elif 'joke' in query:
            speak(pyjokes.get_joke())
        
        elif 'open camera' in query:
            camera_thread = threading.Thread(target=open_camera)
            camera_thread.start()

        elif 'exit code' in query:
            speak("Thank You Sir!!")
            stop_listening()
            break
        elif 'scan money' in query:
            camera_thread = threading.Thread(target=scan_money)
            camera_thread.start()
           
            
def open_camera():
    subprocess.Popen(['python', 'object_detection.py'])
    time.sleep(5)  # Wait for 5 seconds for camera window to open
    speak("Camera window opened.")
def scan_money():
    subprocess.Popen(['python', 'money_detection.py'])
    time.sleep(5)  # Wait for 5 seconds for camera window to open
    speak("Camera window opened.")
    
    
        
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Voice Assistant")
    root.geometry("400x200")  # Set the size of the window

    listen_button = tk.Button(root, text="Start Listening", command=start_listening)
    listen_button.pack()

    stop_button = tk.Button(root, text="Stop Listening", command=stop_listening)
    stop_button.pack()

    listen_status_label = tk.Label(root, text="Not Listening")
    listen_status_label.pack()

    root.mainloop()
