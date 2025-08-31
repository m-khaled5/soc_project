A. Boot & basic checks

1)Boot the DK2 with your OpenSTLinux image and connect it to the network (Ethernet is simplest).

2) Open a terminal on the board

	-Either use the Weston Terminal from the touchscreen/HDMI UI,

	-or SSH from your PC (replace IP):
	
		ssh root@192.168.1.50

	-Default user is typically root (no password) unless you changed it.

3) Check internet (for package install):

	ping -c3 8.8.8.8

_______________________________________________________________________________________________________________

B. Make sure Python 3 is installed

	python3 --version

-If missing:

	opkg update
	opkg install python3-core python3-modules


-opkg is the usual package manager on OpenSTLinux. If your image uses a different one, adapt accordingly.


_______________________________________________________________________________________________________________

C. Install PyQt5 and Wayland support

1) See what PyQt5 packages exist in your feed:

	opkg update
	opkg list | grep -i pyqt5
	opkg list | grep -i qtwayland

2) Install the needed bits (names vary slightly by image; install whatever matches these patterns):


	opkg install \
	python3-pyqt5 \
	python3-pyqt5-qtbase \
	python3-pyqt5-qtgui \
	python3-pyqt5-qtwidgets

	# Wayland platform plugin for Qt (so PyQt5 can show windows on Weston)
	opkg install qtwayland qtwayland-plugins || true

	# Sometimes the PyQt5 wayland piece is split:
	opkg install python3-pyqt5-qtwayland || true


3) Sanity check PyQt5 import:

	python3 -c "import PyQt5, PyQt5.QtCore as C; print('PyQt5 OK, Qt:', C.QT_VERSION_STR)"


-If you see an error like “could not load the Qt platform plugin ‘wayland’”, it means the Wayland plugin isn’t installed—ensure qtwayland packages are present. As a fallback for testing you can try:

	export QT_QPA_PLATFORM=wayland-egl
	# or
	export QT_QPA_PLATFORM=wayland
	
	
_______________________________________________________________________________________________________________


D. Set Wayland environment (only needed when launching from SSH)

-If you run from the on-device Weston Terminal, you can skip this.
If launching via SSH, point Qt to the running Wayland session:

	# for root session (default on DK2)
	export XDG_RUNTIME_DIR=/run/user/0
	export WAYLAND_DISPLAY=wayland-0
	export QT_QPA_PLATFORM=wayland-egl


-Check the socket exists:

_______________________________________________________________________________________________________________

E. Create your project

1) Make a workspace directory:

	mkdir -p /home/root/wsn-gui
	cd /home/root/wsn-gui
	
2) Create main_gui.py

3) Create stt.py (placeholder to the scripts that will be ran when th buttons are pressed)

_______________________________________________________________________________________________________________

F. Point the LED path to a real LED

-List available LEDs:
	ls -1 /sys/class/leds

-You’ll see names like user-led1, user-led2, green:usr, etc. Pick one and set its brightness file:

	# Example if you saw "user-led1"
	echo 1 > /sys/class/leds/user-led1/brightness   # test it turns on
	echo 0 > /sys/class/leds/user-led1/brightness   # test it turns off
	
- Now edit main_gui.py and set:

	LED_BRIGHTNESS = "/sys/class/leds/user-led1/brightness"
	
-If you get “Permission denied”, run as root (you probably are). Some images require udev rules; Python writing the file as root should work.

_______________________________________________________________________________________________________________

G. Launch the GUI

-From Weston Terminal (recommended):

	cd /home/root/wsn-gui
	python3 ./main_gui.py
	
-From SSH (if you set the Wayland env in Section D):

	cd /home/root/wsn-gui
	export XDG_RUNTIME_DIR=/run/user/0
	export WAYLAND_DISPLAY=wayland-0
	export QT_QPA_PLATFORM=wayland-egl
	python3 ./main_gui.py

-You should see a window titled “WSN Demo GUI” with two buttons and a log area.

	-ClickRecord & Transcribe → the placeholder script runs and prints messages into the log.

	-Click Toggle LED → LED toggles and the log shows LED set to 1/0.

_______________________________________________________________________________________________________________

H. Optional: make STT real later
	
-You can wire Button 1 to something real without changing the GUI much.

1) Option 1 – Vosk (offline, light):

-Install:

	opkg install python3-pip || true
	pip3 install vosk

(If building wheels on-device is heavy, you may need prebuilt wheels or an image with Vosk packaged.)

-Flow inside a shell script: record with ALSA, then call Vosk from Python.


2)Option 2 – whisper.cpp (CLI):

-Cross-compile on host or build on board (slower).

-Example run_whisper.sh:
	
	#!/bin/sh
	arecord -f S16_LE -r 16000 -d 5 /tmp/capture.wav
	/opt/whisper/main -m /opt/whisper/models/ggml-base.en.bin -f /tmp/capture.wav

- In run_stt() swap:

	self.proc.start("/bin/sh", ["-lc", "/home/root/wsn-gui/run_whisper.sh"])

-Audio test first:

	arecord -l
	arecord -f S16_LE -r 16000 -d 3 /tmp/test.wav && aplay /tmp/test.wav


_______________________________________________________________________________________________________________

I. (Optional) Autostart on boot with systemd

-Create a service:

	cat > /etc/systemd/system/wsn-gui.service <<'UNIT'
	[Unit]
	Description=WSN Demo GUI
	After=weston.service

	[Service]
	User=root
	Environment=XDG_RUNTIME_DIR=/run/user/0
	Environment=WAYLAND_DISPLAY=wayland-0
	Environment=QT_QPA_PLATFORM=wayland-egl
	WorkingDirectory=/home/root/wsn-gui
	ExecStart=/usr/bin/python3 /home/root/wsn-gui/main_gui.py
	Restart=on-failure

	[Install]
	WantedBy=multi-user.target
	UNIT

	systemctl daemon-reload
	systemctl enable --now wsn-gui.service


-If the GUI doesn’t show at boot, tie it to the correct Weston session target for your image (some images use a different unit name than weston.service).

_______________________________________________________________________________________________________________

J. Troubleshooting cheatsheet

ModuleNotFoundError: No module named PyQt5
→ Install packages in Section C; verify with the one-liner import test.

“Could not load the Qt platform plugin ‘wayland’”
→ opkg install qtwayland qtwayland-plugins and set
export QT_QPA_PLATFORM=wayland-egl.

Running over SSH but no window appears
→ Set XDG_RUNTIME_DIR and WAYLAND_DISPLAY (Section D), or run from Weston Terminal.

LED writes fail
→ Make sure you’re root. Confirm the LED path exists and toggles with echo.

Font or theme issues
→ Usually harmless; install fontconfig if text is missing: opkg install fontconfig.

_______________________________________________________________________________________________________________

Once PyQt5 + Wayland are present, it’s a straight shot: create the two files, set the LED path, and run. If you hit any package-name quirks on your particular OpenSTLinux image, paste the output of opkg list | grep -i pyqt5 and then map the exact names for you.





