sudo cp replication.service /etc/systemd/system

sudo systemctl daemon-reload

sudo systemctl enable replication

sudo systemctl start replication