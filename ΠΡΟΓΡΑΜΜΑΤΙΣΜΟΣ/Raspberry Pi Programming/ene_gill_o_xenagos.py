import RPi.GPIO as GPIO
import time
import subprocess
import os
import serial
import threading

# Σύνδεση με Arduino μέσω Bluetooth-Serial (/dev/rfcomm0)
try:
    bluetooth = serial.Serial("/dev/rfcomm0", 9600)
    print("[INFO] Bluetooth συνδέθηκε επιτυχώς.")
except Exception as e:
    print(f"[ERROR] Bluetooth: {e}")
    bluetooth = None

# GPIO numbering: φυσική αρίθμηση pins (BOARD)
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

# Αντιστοίχιση αισθητήρων υπερήχων με τα βίντεο στάσης (TRIG, ECHO, VIDEO)
SENSORS = [
    (16, 18, "video1.mp4"),
    (29, 31, "video2.mp4"),
    (33, 37, "video3.mp4"),
    (22, 32, "video4.mp4"),
]

# Αρχικοποίηση αισθητήρων
for TRIG, ECHO, _ in SENSORS:
    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)
    GPIO.output(TRIG, False)

# Κουμπί χειροκίνητης παρέμβασης (pull-up, ενεργοποίηση με πτώση)
BUTTON_PIN = 40  # BOARD pin 40
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Κατάσταση αναπαραγωγής βίντεο (μονο-διεργασία VLC)
video_process = None
video_lock = threading.Lock()
video_playing = False  # True μόνο όταν παίζει το εισαγωγικό video0.mp4 (παγώνει τις μετρήσεις)


def stop_car():
    """Στέλνει εντολή stop στο Arduino."""
    if bluetooth and bluetooth.is_open:
        bluetooth.write(b'S')
        print("[ACTION] Στάση αυτοκινήτου")


def start_car():
    """Στέλνει εντολή go στο Arduino."""
    if bluetooth and bluetooth.is_open:
        bluetooth.write(b'G')
        print("[ACTION] Κίνηση αυτοκινήτου")


def stop_current_video():
    """Διακόπτει τυχόν τρέχουσα αναπαραγωγή VLC."""
    global video_process
    with video_lock:
        if video_process and video_process.poll() is None:
            print("[INFO] Διακοπή τρέχοντος video...")
            video_process.terminate()
            video_process.wait()
            video_process = None


def play_video(video_file, is_manual=False):
    """Αναπαράγει βίντεο full screen και συγχρονίζει την κίνηση του οχήματος."""
    global video_process, video_playing
    video_path = os.path.expanduser(f"~/Desktop/{video_file}")

    # Κατά την εισαγωγή (video0) δεν εκτελούνται μετρήσεις αισθητήρων
    if video_file == "video0.mp4":
        video_playing = True

    with video_lock:
        stop_car()
        print(f"[VIDEO] Παίζει {video_file}")
        try:
            video_process = subprocess.Popen(
                ["vlc", "--fullscreen", "--play-and-exit", video_path]
            )
        except Exception as e:
            print(f"[ERROR] Δεν μπόρεσε να ξεκινήσει το βίντεο: {e}")
            return

    video_process.wait()
    video_process = None

    if video_file == "video0.mp4":
        video_playing = False

    start_car()

    # Μικρή καθυστέρηση μετά από αυτόματη στάση ώστε να μην ξανα-πυροδοτηθεί άμεσα ο ίδιος αισθητήρας
    if not is_manual:
        print("[INFO] Καθυστέρηση 2 δευτερόλεπτα για απομάκρυνση...")
        time.sleep(2)


def measure_distance(TRIG, ECHO):
    """Μετρά απόσταση (cm) από HC-SR04. Επιστρέφει None σε timeout ή όταν είναι ενεργό το video0."""
    if video_playing:
        return None

    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    pulse_start = time.time()
    timeout = pulse_start + 0.1

    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
        if time.time() > timeout:
            return None

    pulse_end = time.time()
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
        if time.time() > timeout:
            return None

    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150
    return round(distance, 2)


def button_callback(channel):
    """Χειροκίνητη εκκίνηση εισαγωγικού βίντεο (διακόπτει τρέχον βίντεο αν υπάρχει)."""
    print("[BUTTON] Πατήθηκε κουμπί → Παίζει video0.mp4")
    stop_current_video()
    play_video("video0.mp4", is_manual=True)


GPIO.add_event_detect(
    BUTTON_PIN, GPIO.FALLING, callback=button_callback, bouncetime=300
)

try:
    while True:
        for TRIG, ECHO, video_file in SENSORS:
            distance = measure_distance(TRIG, ECHO)
            if distance is not None:
                print(
                    f"[DIST] Sensor {SENSORS.index((TRIG, ECHO, video_file)) + 1}: {distance} cm"
                )
                if distance <= 20:
                    print(f"[TRIGGER] Παίζει {video_file}")
                    stop_current_video()
                    play_video(video_file)

        # Ρυθμός polling αισθητήρων (1Hz)
        time.sleep(1)

except KeyboardInterrupt:
    print("\n[EXIT] Διακοπή από χρήστη")

finally:
    GPIO.cleanup()
    if bluetooth and bluetooth.is_open:
        bluetooth.close()
        print("[INFO] Τερματισμός Bluetooth")