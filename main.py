import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk ,filedialog
import cv2
import face_recognition
from datetime import datetime
import os
import mysql.connector
import csv
from threading import Thread
import pandas as pd

ADMIN_USER = ""
ADMIN_PASS = ""

def connect_database():
    return mysql.connector.connect(
        host="localhost",
        username="root",
        password="Delldell123",
        database="insta_vision"
    )


def save_to_database(name, date_time):
    conn = connect_database()
    cursor = conn.cursor()
    query = "INSERT INTO attendance_records (name, time) VALUES (%s, %s)"
    cursor.execute(query, (name, date_time))
    conn.commit()
    conn.close()

def on_enter(e):
    e.widget['background'] = '#16a085'

def on_leave(e):
    e.widget['background'] = '#1abc9c'


class AttendanceSystemApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Facial Recognition Attendance System")
        self.root.geometry("800x700")
        self.root.configure(bg="#1a1a1a")

        # Paths and attendance record storage
        self.photo_directory = r"D:\Projects ALL\Face reco\images"
        self.attendance_records = []
        self.known_face_encodings = {}
        self.running = False
        self.thread = None

        # Load known faces
        self.load_known_faces()

        # GUI setup
        self.create_gui()

    def create_gui(self):
        # Header with date/time
        self.header_label = tk.Label(self.root, text="Facial Recognition Attendance System", font=("Arial", 16, "bold"),
                                     bg="#1a1a1a", fg="#00ffcc")
        self.header_label.pack(pady=10)

        self.date_label = tk.Label(self.root, text=f"Date: {datetime.now().strftime('%Y-%m-%d')}",
                                   font=("Arial", 10), bg="#1a1a1a", fg="#00ffcc")
        self.date_label.pack()

        # Start/Stop buttons
        self.start_button = tk.Button(self.root, text="Start Attendance", command=self.start_attendance, width=20,
                                      font=("Arial", 12, "bold"), bg="#1abc9c", fg="white")
        self.start_button.pack(pady=10)
        self.start_button.bind("<Enter>", on_enter)
        self.start_button.bind("<Leave>", on_leave)

        self.stop_button = tk.Button(self.root, text="Stop Attendance", command=self.stop_attendance, width=20,
                                     font=("Arial", 12, "bold"), bg="#1abc9c", fg="white", state=tk.DISABLED)
        self.stop_button.pack(pady=10)
        self.stop_button.bind("<Enter>", on_enter)
        self.stop_button.bind("<Leave>", on_leave)

        # Attendance records display
        self.records_text = scrolledtext.ScrolledText(self.root, width=70, height=15, bg="#262626", fg="#00ffcc",
                                                      font=("Consolas", 10))
        self.records_text.pack(pady=10)

        # Filter attendance by date
        self.date_filter_label = tk.Label(self.root, text="Filter by Date:", bg="#1a1a1a", fg="#00ffcc")
        self.date_filter_label.pack()
        self.date_entry = tk.Entry(self.root, width=20, font=("Arial", 10))
        self.date_entry.pack(pady=5)

        # Export CSV Button
        self.export_button = tk.Button(self.root, text="Export to CSV", command=self.export_to_csv, width=20,
                                       font=("Arial", 12, "bold"), bg="#1abc9c", fg="white")
        self.export_button.pack(pady=10)
        self.export_button.bind("<Enter>", on_enter)
        self.export_button.bind("<Leave>", on_leave)

        self.export_all_button = tk.Button(self.root, text="Export All Data",command=self.export_all_data ,width=20,
                                       font=("Arial", 12, "bold"), bg="#1abc9c", fg="white")
        self.export_all_button.pack(pady=10)
        self.export_all_button.bind("<Enter>", on_enter)
        self.export_all_button.bind("<Leave>", on_leave)

        # Quit button
        self.quit_button = tk.Button(self.root, text="Quit", command=self.quit_app, width=20, font=("Arial", 12, "bold"),
                                     bg="#1abc9c", fg="white")
        self.quit_button.pack(pady=10)
        self.quit_button.bind("<Enter>", on_enter)
        self.quit_button.bind("<Leave>", on_leave)

    def load_known_faces(self):
        for filename in os.listdir(self.photo_directory):
            name, extension = os.path.splitext(filename)
            if extension.lower() in (".jpg", ".jpeg", ".png"):
                image_path = os.path.join(self.photo_directory, filename)
                image = face_recognition.load_image_file(image_path)
                encoding = face_recognition.face_encodings(image)[0]
                self.known_face_encodings[name] = encoding

    def start_attendance(self):
        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.records_text.delete(1.0, tk.END)
        self.thread = Thread(target=self.run_attendance)
        self.thread.start()

    def stop_attendance(self):
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        if self.thread is not None:
            self.thread.join()

    def run_attendance(self):
        video_capture = cv2.VideoCapture(0)
        while self.running:
            ret, frame = video_capture.read()
            face_locations = face_recognition.face_locations(frame)
            face_encodings = face_recognition.face_encodings(frame, face_locations)

            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                name = "Unknown"
                for known_name, known_encoding in self.known_face_encodings.items():
                    if face_recognition.compare_faces([known_encoding], face_encoding)[0]:
                        name = known_name
                        if name not in [record['name'] for record in self.attendance_records]:
                            date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            self.attendance_records.append({"name": name, "time": date_time})
                            self.update_records_text(f"{name} is marked present at {date_time}.")
                            save_to_database(name, date_time)

                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)

            cv2.imshow("Video", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        video_capture.release()
        cv2.destroyAllWindows()

    def update_records_text(self, text):
        self.records_text.insert(tk.END, text + "\n")
        self.records_text.yview(tk.END)

    def export_to_csv(self):
        with open("attendance_records.csv", "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Name", "Time"])
            for record in self.attendance_records:
                writer.writerow([record["name"], record["time"]])
        messagebox.showinfo("Export", "Attendance records exported to attendance_records.csv")

    def export_all_data(self):
        db = mysql.connector.connect(user='root', password='Delldell123', host='localhost',
                                     database='insta_vision')
        sql = "SELECT * FROM insta_vision.attendance_records;"
        df = pd.read_sql(sql, db)

        folder_path = filedialog.askdirectory(parent=self.root)

        if not folder_path:
            messagebox.showinfo("Info", "Export canceled by admin", parent=self.root)
            db.close()
            return

        excel_file_path = f"{folder_path}/Attendance_All_data.xlsx"
        df.to_excel(excel_file_path, index=False)
        messagebox.showinfo("Success", "Data Exported Successfully", parent=self.root)
        db.close()


    def quit_app(self):
        if self.running:
            self.stop_attendance()
        self.root.destroy()

# Admin Login for authentication
class AdminLoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Admin Login")
        self.root.geometry("500x400")
        self.root.configure(bg="#121212")

        title_label = tk.Label(self.root, text="Admin Login", font=("Arial", 20, "bold"), bg="#121212", fg="#00ffcc")
        title_label.pack(pady=30)

        self.username_label = tk.Label(self.root, text="Username:", font=("Arial", 12, "bold"), bg="#121212", fg="#00ffcc")
        self.username_label.pack(pady=10)
        self.username_entry = tk.Entry(self.root, font=("Arial", 12), bg="#262626", fg="#00ffcc")
        self.username_entry.pack(pady=5, ipadx=5, ipady=5)

        self.password_label = tk.Label(self.root, text="Password:", font=("Arial", 12, "bold"), bg="#121212", fg="#00ffcc")
        self.password_label.pack(pady=10)
        self.password_entry = tk.Entry(self.root, show="*", font=("Arial", 12), bg="#262626", fg="#00ffcc")
        self.password_entry.pack(pady=5, ipadx=5, ipady=5)

        self.login_button = tk.Button(self.root, text="Login", command=self.login, font=("Arial", 12, "bold"),
                                      bg="#1abc9c", fg="white", activebackground="#16a085")
        self.login_button.pack(pady=30, ipadx=10, ipady=5)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if username == ADMIN_USER and password == ADMIN_PASS:
            self.root.destroy()  # Close the login window
            main_root = tk.Tk()  # Create a new main window
            AttendanceSystemApp(main_root)  # Initialize the attendance system
            main_root.mainloop()  # Start the main loop
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")


if __name__ == "__main__":
    root = tk.Tk()
    AdminLoginApp(root)
    root.mainloop()
