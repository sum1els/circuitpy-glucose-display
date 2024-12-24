.PHONY: all clean download_circuitpython install_circuitpython download_libraries install_libraries setup_repo configure_settings deploy_code serialconsol check_mount

CIRCUITPY_DRIVE=/Volumes/CIRCUITPY
RPI_RP2_DRIVE=/Volumes/RPI-RP2

# Default target: install everything
all: download_circuitpython install_circuitpython download_libraries install_libraries configure_settings deploy_code

# Open serial console
serialconsol:
	@echo "---------------------------------------------------------------------"
	@echo "You can exit with Ctrl-a-d maybe you need to do Ctrl-a-Ctrl-a-d if"
	@echo "you are in tmux! If it doesn't work, you may need to reconnect your Pico!"
	@echo "---------------------------------------------------------------------"
	@sleep 2
	@SERIAL_PORT=$$(ls /dev/tty.usbmodem* 2>/dev/null || ls /dev/ttyACM* 2>/dev/null || echo ""); \
	if [ -z "$$SERIAL_PORT" ]; then \
		echo "Error: No Pico serial port found. Is the device connected?"; \
		exit 1; \
	else \
		echo "Connecting to $$SERIAL_PORT..."; \
		screen $$SERIAL_PORT 115200; \
	fi

# Download the latest CircuitPython version
download_circuitpython:
	@echo "Fetching the latest CircuitPython version..."
	@LATEST_VERSION=$$(curl -s https://circuitpython.org/board/raspberry_pi_pico_w/ | grep -o 'adafruit-circuitpython-raspberry_pi_pico_w-en_US-[^"]*.uf2' | head -1); \
	VERSION_NUMBER=$$(echo $$LATEST_VERSION | sed -E 's/.*-([0-9]+\.[0-9]+\.[0-9]+)\.uf2/\1/'); \
	MAJOR_VERSION=$$(echo $$VERSION_NUMBER | cut -d. -f1); \
	echo "Latest version is $$LATEST_VERSION"; \
	echo "Major version is $$MAJOR_VERSION.x"; \
	wget -O circuitpython.uf2 https://downloads.circuitpython.org/bin/raspberry_pi_pico_w/en_US/$$LATEST_VERSION; \
	echo $$MAJOR_VERSION > .circuitpython_version

# Wait for RPI-RP2 to be mounted and install CircuitPython
install_circuitpython:
	@echo "Please press the BOOTSEL button and connect the Raspberry Pi Pico W to your computer."
	@echo "Waiting for RPI-RP2 drive to be mounted..."
	@while [ ! -d "$(RPI_RP2_DRIVE)" ]; do sleep 1; done
	@if [ -f "circuitpython.uf2" ]; then \
		echo "RPI-RP2 drive detected. Copying CircuitPython UF2 file..."; \
		cp circuitpython.uf2 $(RPI_RP2_DRIVE)/; \
		echo "CircuitPython UF2 file copied. Please wait for the device to reboot."; \
	else \
		echo "Error: CircuitPython UF2 file not found. Please run 'make download_circuitpython' first."; \
		exit 1; \
	fi

# Check if CIRCUITPY is mounted
check_mount:
	@echo "Checking if CIRCUITPY drive is mounted at $(CIRCUITPY_DRIVE)..."
	@for i in {1..5}; do \
		if df | grep -q "$(CIRCUITPY_DRIVE)"; then \
			echo "CIRCUITPY drive is mounted."; \
			exit 0; \
		else \
			echo "CIRCUITPY drive not found, retrying in 1 second..."; \
			sleep 1; \
		fi; \
	done; \
	echo "Error: CIRCUITPY drive is not mounted at $(CIRCUITPY_DRIVE). Please ensure the device is connected and try again."; \
	exit 1

# Download the required CircuitPython libraries
download_libraries:
	@echo "Reading CircuitPython major version from .circuitpython_version..."
	@MAJOR_VERSION=$$(cat .circuitpython_version); \
	if [ -z "$$MAJOR_VERSION" ]; then \
		echo "Error: CircuitPython major version is empty. Please run 'make download_circuitpython' first."; \
		exit 1; \
	fi; \
	LIBRARIES_URL=$$(curl -s https://api.github.com/repos/adafruit/Adafruit_CircuitPython_Bundle/releases/latest | grep "browser_download_url.*adafruit-circuitpython-bundle-$$MAJOR_VERSION.x" | cut -d '"' -f 4); \
	if [ -z "$$LIBRARIES_URL" ]; then \
		echo "Error: Could not find the libraries for version $$MAJOR_VERSION.x"; \
		exit 1; \
	fi; \
	echo "Downloading the CircuitPython libraries for version $$MAJOR_VERSION.x..."; \
	wget -O adafruit-libraries.zip $$LIBRARIES_URL; \
	unzip -o adafruit-libraries.zip

# Install the required CircuitPython libraries
install_libraries: check_mount
	@echo "Creating lib directory if it doesn't exist..."
	@mkdir -p $(CIRCUITPY_DRIVE)/lib
	@echo "Copying required libraries to the 'lib' folder on the CIRCUITPY drive."
	@for lib in adafruit_hashlib adafruit_imageload adafruit_display_text; do \
		echo "Copying $$lib..."; \
		cp -r adafruit-circuitpython-bundle-*/lib/$$lib $(CIRCUITPY_DRIVE)/lib/ || exit 1; \
	done
	@for lib in adafruit_requests.mpy adafruit_connection_manager.mpy adafruit_st7789.mpy adafruit_binascii.mpy; do \
		echo "Copying $$lib..."; \
		cp adafruit-circuitpython-bundle-*/lib/$$lib $(CIRCUITPY_DRIVE)/lib/ || exit 1; \
	done

# Configure Wi-Fi settings and LibreLinkUp credentials
configure_settings:
	@if [ -f "settings.toml" ]; then \
		echo "settings.toml already exists. Skipping configuration."; \
	else \
		echo "Creating and configuring the settings.toml file."; \
		echo "Please enter the Wi-Fi SSID and Password, as well as the LibreLinkUp credentials."; \
		echo "SSID:"; \
		read WIFI_SSID; \
		echo "Wi-Fi Password:"; \
		read -s WIFI_PASSWORD; \
		echo "LinkUp Username:"; \
		read LINKUP_USERNAME; \
		echo "LinkUp Password:"; \
		read -s LINKUP_PASSWORD; \
		echo "CIRCUITPY_WIFI_SSID = \"$$WIFI_SSID\"" > settings.toml; \
		echo "CIRCUITPY_WIFI_PASSWORD = \"$$WIFI_PASSWORD\"" >> settings.toml; \
		echo "API_USER = \"$$LINKUP_USERNAME\"" >> settings.toml; \
		echo "API_PASSWORD = \"$$LINKUP_PASSWORD\"" >> settings.toml; \
	fi

# Deploy code to CIRCUITPY
deploy_code: check_mount
	@echo "Deploying code to CIRCUITPY drive..."
	@FILES=("wireless.py" "settings.toml" "trend_arrows.bmp" "code.py"); \
	for FILE in $${FILES[@]}; do \
		echo "Copying $$FILE to $(CIRCUITPY_DRIVE)/"; \
		cp $$FILE $(CIRCUITPY_DRIVE)/; \
	done

deploy_code_only: check_mount
	@echo "Deploying code to CIRCUITPY drive..."
	@FILES=("code.py"); \
	for FILE in $${FILES[@]}; do \
		echo "Copying $$FILE to $(CIRCUITPY_DRIVE)/"; \
		cp $$FILE $(CIRCUITPY_DRIVE)/; \
	done

# Clean up downloaded files
clean:
	@echo "Cleaning up downloaded files..."
	rm -f circuitpython.uf2
	rm -f adafruit-libraries.zip
	rm -rf adafruit-circuitpython-bundle-*
	rm -f .circuitpython_version
	@echo "Cleanup complete."
