sudo cp partitioning.service /etc/systemd/system

sudo systemctl daemon-reload

sudo systemctl enable partitioning

sudo systemctl start partitioning