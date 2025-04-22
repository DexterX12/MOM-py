sudo cp mom.service /etc/systemd/system

sudo systemctl daemon-reload

sudo systemctl enable mom

sudo systemctl start mom