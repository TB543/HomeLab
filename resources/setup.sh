#!/bin/bash


# gets user config settings
read -p "Enter KASA email: " KASA_USER
read -p "Enter KASA password: " KASA_PASS
read -p "Enter WiFi name: " WIFI_SSID
read -p "Enter WiFi password: " WIFI_PASS

# creates system services to run everything
sudo cp cec-name.service /etc/systemd/system/
sudo cp home-automation.service /etc/systemd/system/
sudo cp minecraft-server.service /etc/systemd/system/

# sets up the pi as a wifi access point
sudo nmcli connection add type wifi ifname wlan0 con-name HomeLab ssid "$WIFI_SSID"
sudo nmcli connection modify HomeLab \
    802-11-wireless.mode ap \
    802-11-wireless.band a \
    802-11-wireless.channel 149 \
    ipv4.method shared \
    ipv4.addresses 10.69.67.1/24 \
    ipv6.method disabled \
    connection.autoconnect yes \
    wifi-sec.key-mgmt wpa-psk \
    wifi-sec.proto rsn \
    wifi-sec.pairwise ccmp \
    wifi-sec.group ccmp \
    wifi-sec.psk "$WIFI_PASS"
sudo nmcli connection up HomeLab

# sets up pi hole
curl -sSL https://install.pi-hole.net | bash
sudo pihole setpassword admin
sudo mkdir -p /etc/NetworkManager/dnsmasq-shared.d
sudo tee /etc/NetworkManager/dnsmasq-shared.d/pihole.conf <<'EOF'
port=0
dhcp-option=6,10.69.67.1
EOF

# sets up remote connection
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
sudo tailscale set --advertise-exit-node

# sets up home automation
cd ../services/home-automation
python -m venv --system-site-packages venv
venv/bin/pip install -r requirements.txt
venv/bin/python main.py "$KASA_USER" "$KASA_PASS"
sudo sed -i "/^\[Service\]/a WorkingDirectory=$(pwd)\nExecStart=$(pwd)/venv/bin/python $(pwd)/main.py" /etc/systemd/system/home-automation.service

# sets up minecraft server
cd ../minecraft-server
sudo apt install -y docker-compose
curl -SsL https://packages.playit.gg/keys/playit.gpg | gpg --dearmor | sudo tee /usr/share/keyrings/playit.gpg >/dev/null
sudo chmod 0644 /usr/share/keyrings/playit.gpg
sudo curl -fsSL -o /etc/apt/sources.list.d/playit.list https://packages.playit.gg/repo-files/playit-debian.list
sudo apt update
sudo apt install playit
sudo playit
sudo sed -i "/^\[Service\]/a WorkingDirectory=$(pwd)" /etc/systemd/system/minecraft-server.service

# enables services and reboots
sudo systemctl daemon-reload
sudo systemctl enable cec-name.service
sudo systemctl enable home-automation.service
sudo systemctl enable minecraft-server.service
sudo reboot
