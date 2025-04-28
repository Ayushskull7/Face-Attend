import face_recognition
import numpy as np
import cv2
import os
import sqlite3
import datetime
import sendmail

video_capture = cv2.VideoCapture(0)

def enroll():
    conn = sqlite3.connect("identifier.sqlite")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Enrolled_Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            regno TEXT UNIQUE NOT NULL,
            pno INTEGER NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE 
        )
    ''')
    conn.commit()
    print("Database connected and table checked.")

    cam_port = 0
    cam = cv2.VideoCapture(cam_port)

    folder_name = "Enrolled"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    print("Press 'c' to capture an image, or 'q' to quit.")
    while True:
        ret, frame = cam.read()
        if not ret:
            print("Failed to grab frame")
            break

        cv2.imshow("Camera Feed", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('c'):
            name = input("Enter the person's name: ")
            print("1.) Administrator\n2.) Faculty\n3.)Student")
            ip = input("Select the person's role: ")
            role = ""
            while ip not in ("1", "2", "3"):
                print("Invalid input. Please try again.")
                ip = input("Select the person's role: ")
            ip = int(ip)
            if ip == 1:
                role = "Administrator"
            elif ip == 2:
                role = "Faculty"
            elif ip == 3:
                role = "Student"

            regno = input("Enter the person's registration number: ")
            pno = int(input("Enter the person's pno: "))
            email = input("Enter the person's email: ")
            filename = os.path.join(folder_name, f"{regno}.jpg")
            cv2.imwrite(filename, frame)
            print(f"Image saved as {filename}")

            # Insert the new user's data into the database
            cursor.execute("INSERT INTO Enrolled_Users (name, role, regno, pno, email) VALUES (?, ?, ?, ?, ?)", (name, role, regno, pno, email))
            conn.commit()
            print(f"User '{name}' with role '{role}' and Registration No. '{regno}' added to the database.")
            sendmail.send_enrollment_email(name, email, regno)

        elif key == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()
    conn.close()

def detect():
    # Initialize empty lists for face encodings and names
    known_face_encodings = []
    known_face_names = []
    known_face_regnos = []

    # Connect to the SQLite database
    conn = sqlite3.connect("identifier.sqlite")
    cursor = conn.cursor()

    # Query the database to get all enrolled users
    cursor.execute("SELECT regno,name FROM Enrolled_Users")
    users = cursor.fetchall()

    # Loop through each user, load the image, and compute the face encoding
    for (regno,name,) in users:
        image_path = os.path.join("Enrolled", f"{regno}.jpg")
        if os.path.exists(image_path):
            image = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image)
            if encodings:
                known_face_encodings.append(encodings[0])
                known_face_names.append(name)
                known_face_regnos.append(regno)
            else:
                print(f"Warning: No face found in image for user '{name}'.")
        else:
            print(f"Warning: Image file '{image_path}' not found for user '{name}'.")

    conn.close()

    face_locations = []
    face_names = []
    process_this_frame = True

    currently_detected = set()
    while True:
        # Grab a single frame of video
        ret, frame = video_capture.read()

        # Only process every other frame of video to save time
        if process_this_frame:
            detected_this_frame = set()
            # Resize frame of video to 1/4 size for faster face recognition processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

            # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            # Find all the faces and face encodings in the current frame of video
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            # Set to store registration numbers detected in this frame

            face_names = []
            for face_encoding in face_encodings:
                # See if the face is a match for the known face(s)
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                #name = "Unknown"
                label = "Unknown"

                # # If a match was found in known_face_encodings, just use the first one.
                # if True in matches:
                #     first_match_index = matches.index(True)
                #     name = known_face_names[first_match_index]

                # Or instead, use the known face with the smallest distance to the new face
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]
                    regno = known_face_regnos[best_match_index]

                    label = f"{known_face_names[best_match_index]} ({known_face_regnos[best_match_index]})"

                    detected_this_frame.add(regno)

                    if regno not in currently_detected:
                        mark_attendance(name, regno)
                        currently_detected.add(regno)

                face_names.append(label)

            currently_detected.intersection_update(detected_this_frame)

        process_this_frame = not process_this_frame

        # Display the results
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            # Scale back up face locations since the frame we detected in was scaled to 1/4 size
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            # Draw a box around the face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

            # Draw a label with a name below the face
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

        # Display the resulting image
        cv2.imshow('Video', frame)

        # Hit 'q' on the keyboard to quit!
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release handle to the webcam
    video_capture.release()
    cv2.destroyAllWindows()

def mark_attendance(name, regno):
    conn = sqlite3.connect("identifier.sqlite")
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS Attendance ( 
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT,
        regno INTEGER NOT NULL,
        date DATE NOT NULL,
        time_in TIME,
        time_out TIME,
        status TEXT CHECK(status IN ('Present', 'Absent', 'Late', 'Excused')) NOT NULL,
        remarks TEXT,
        device_id TEXT,
        email TEXT NOT NULL,
        email_sent INTEGER DEFAULT 0,
        exit_email_sent INTEGER DEFAULT 0
    )''')
    conn.commit()

    now = datetime.datetime.now()
    current_date = now.date()
    current_time = now.time()
    current_time_str = now.strftime("%H:%M:%S")

    work_start_time = datetime.time(11, 13, 0)
    work_end_time = datetime.time(11, 15, 0)

    shift_crosses_midnight = work_start_time > work_end_time
    if shift_crosses_midnight:
        shift_date = current_date if current_time >= work_start_time else current_date - datetime.timedelta(days=1)
    else:
        shift_date = current_date
    shift_date_str = shift_date.isoformat()

    cursor.execute("SELECT role, email FROM Enrolled_Users WHERE regno = ?", (regno,))
    role_data = cursor.fetchone()
    role = role_data[0] if role_data else "Employee"
    email = role_data[1] if role_data else "<EMAIL>"

    device_id = "Device001"

    cursor.execute("SELECT time_in, time_out, remarks, status, email_sent, exit_email_sent FROM Attendance WHERE regno = ? AND date = ?",
                   (regno, shift_date_str))
    record = cursor.fetchone()

    if not record:
        if work_start_time <= current_time <= work_end_time:
            print(f"ℹ️ No record found. Marking {name} ({regno}) as 'Present' with time_in = {current_time_str}")
            cursor.execute('''INSERT INTO Attendance (name, role, regno, date, time_in, status, remarks, device_id, email, email_sent)
                              VALUES (?, ?, ?, ?, ?, 'Present', '', ?, ?, 0)''',
                           (name, role, regno, shift_date_str, current_time_str, device_id, email))
            conn.commit()
            print(f"✅ Check-in recorded for {name} ({regno}) at {current_time_str}.")

            try:
                success = sendmail.send_attendance_email(name, email, regno, "Checked In", f"Checked in at {current_time_str}")
            except Exception as e:
                success = False
                print(f"❌ Exception during check-in email send: {e}")
            if success:
                cursor.execute("UPDATE Attendance SET email_sent = 1 WHERE regno = ? AND date = ?", (regno, shift_date_str))
                conn.commit()
                print(f"📧 Check-in email sent successfully for {name} ({regno}).")
            else:
                print(f"⚠️ Check-in email failed for {name} ({regno}). Will retry later.")
        else:
            print(f"⏳ It's too early for check-in. Shift starts at {work_start_time}.")
    else:
        time_in, time_out, existing_remarks, stored_status, email_sent, exit_email_sent = record

        if current_time >= work_end_time:
            if time_out is None or current_time_str > time_out:
                extra_minutes = int((datetime.datetime.combine(shift_date, current_time) -
                                       datetime.datetime.combine(shift_date, work_end_time)).total_seconds() // 60)
                new_remarks = existing_remarks if existing_remarks else ""
                if extra_minutes > 0 and "Extra work" not in new_remarks:
                    new_remarks += f" | Extra work: {extra_minutes} minutes" if new_remarks else f"Extra work: {extra_minutes} minutes"
                elif extra_minutes <= 0 and "Left on time" not in new_remarks:
                    new_remarks += " | Left on time" if new_remarks else "Left on time"

                cursor.execute("UPDATE Attendance SET time_out = ?, remarks = ? WHERE regno = ? AND date = ?",
                               (current_time_str, new_remarks, regno, shift_date_str))
                conn.commit()
                print(f"✅ {name} ({regno}) time_out updated to {current_time_str}. {new_remarks}")

                if exit_email_sent == 0:
                    try:
                        success = sendmail.send_attendance_email(name, email, regno, "Checked Out", new_remarks+f" | Checked out at {current_time_str}")
                    except Exception as e:
                        success = False
                        print(f"❌ Exception during exit email send: {e}")

                    if success:
                        cursor.execute("UPDATE Attendance SET exit_email_sent = 1 WHERE regno = ? AND date = ?",
                                       (regno, shift_date_str))
                        conn.commit()
                        print(f"📧 Exit email sent successfully for {name} ({regno}).")
                    else:
                        print(f"⚠️ Exit email failed for {name} ({regno}). Will retry later.")
            else:
                print(f"⚠️ {name} ({regno}) already has a later time_out recorded.")
        else:
            print(f"⏳ Work shift still in progress. Cannot mark time_out before {work_end_time}.")

    conn.close()

if __name__ == '__main__':
    enroll()
    detect()
