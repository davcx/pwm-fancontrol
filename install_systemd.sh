#!/bin/sh
set -e

echo "=> Installing fan controller...\n"
sudo cp -p fancontrol.py /usr/local/bin/
sudo chmod +x /usr/local/bin/fancontrol.py

echo "=> Starting fan controller...\n"
sudo cp -p fancontrol.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable fancontrol.service
sudo systemctl start fancontrol.service

echo "Fan controller installed."
