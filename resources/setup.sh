#!/bin/bash


# gets user config settings
read -p "Enter KASA username: " KASA_USER
read -p "Enter KASA password: " KASA_PASS

# creates system services to run everything
sudo cp cec-name.service /etc/systemd/system/
sudo cp home-automation.service /etc/systemd/system/

# sets up home automation
cd ../services/home-automation
python -m venv --system-site-packages venv
venv/bin/pip install -r requirements.txt
venv/bin/python main.py "$KASA_USER" "$KASA_PASS"
sudo sed -i "/^\[Service\]/a WorkingDirectory=$(pwd)\nExecStart=$(pwd)/venv/bin/python $(pwd)/main.py" /etc/systemd/system/startup.service

# sets up pi hole

# sets up effects pedal program

# sets up minecraft server

# enables services and reboots
sudo systemctl daemon-reload
sudo systemctl enable cec-name.service
sudo systemctl enable home-automation.service
sudo reboot
