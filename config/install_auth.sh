sudo cp auth.service /etc/systemd/system

sudo systemctl daemon-reload

sudo systemctl enable auth

sudo systemctl start auth