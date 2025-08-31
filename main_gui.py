#!/usr/bin/env python3
import os
import sys
import subprocess
from PyQt5.QtCore import QProcess
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QMessageBox

APP_DIR = os.path.dirname(os.path.abspath(__file__))
STT_SCRIPT = os.path.join(APP_DIR, "stt.py")

# Adjust this LED path to one that exists on your DK2 image
# You can list with:  ls -1 /sys/class/leds
LED_BRIGHTNESS = "/sys/class/leds/led0/brightness"

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WSN Demo GUI")
        layout = QVBoxLayout(self)

        self.btn_stt = QPushButton("🎙️ Record & Transcribe")
        self.btn_led = QPushButton("💡 Toggle LED")
        self.log = QTextEdit()
        self.log.setReadOnly(True)

        layout.addWidget(self.btn_stt)
        layout.addWidget(self.btn_led)
        layout.addWidget(self.log)

        # Run STT as an external process so UI stays responsive
        self.proc = QProcess(self)
        self.proc.readyReadStandardOutput.connect(self.on_stdout)
        self.proc.readyReadStandardError.connect(self.on_stderr)
        self.proc.finished.connect(self.on_finished)

        self.btn_stt.clicked.connect(self.run_stt)
        self.btn_led.clicked.connect(self.toggle_led)

    def run_stt(self):
        if self.proc.state() != QProcess.NotRunning:
            QMessageBox.information(self, "Busy", "STT is already running.")
            return
        if not os.path.exists(STT_SCRIPT):
            QMessageBox.critical(self, "Missing", f"STT script not found:\n{STT_SCRIPT}")
            return
        self.log.append("Starting STT...\n")
        # Use python3 to run your script; ensure the environment/venv is set if needed
        self.proc.start(sys.executable, [STT_SCRIPT])

    def on_stdout(self):
        text = bytes(self.proc.readAllStandardOutput()).decode(errors="ignore")
        if text:
            self.log.append(text.rstrip())

    def on_stderr(self):
        text = bytes(self.proc.readAllStandardError()).decode(errors="ignore")
        if text:
            self.log.append(f"[ERR] {text.rstrip()}")

    def on_finished(self, code, status):
        self.log.append(f"\nSTT finished with code={code} status={status}\n")

    def toggle_led(self):
        try:
            if not os.path.exists(LED_BRIGHTNESS):
                QMessageBox.warning(self, "LED not found", f"LED path not found:\n{LED_BRIGHTNESS}\nAdjust the path.")
                return
            with open(LED_BRIGHTNESS, "r") as f:
                cur = f.read().strip()
            new = "0" if cur == "1" else "1"
            # Writing may require permissions; run the app as a user with access or adjust udev rules
            with open(LED_BRIGHTNESS, "w") as f:
                f.write(new)
            self.log.append(f"LED set to {new}")
        except Exception as e:
            self.log.append(f"[ERR] LED toggle failed: {e}")
            QMessageBox.critical(self, "LED Error", str(e))

def main():
    app = QApplication(sys.argv)
    w = App()
    w.resize(600, 400)
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
