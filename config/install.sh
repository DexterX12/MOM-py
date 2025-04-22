sudo cp auth.service /etc/systemd/system
sudo cp partitioning.service /etc/systemd/system
sudo cp mom.service /etc/systemd/system
sudo cp replication.service /etc/systemd/system

sudo systemctl daemon-reload

sudo systemctl enable auth
sudo systemctl enable partitioning
sudo systemctl enable mom
sudo systemctl enable replication

sudo systemctl start auth
sudo systemctl start partitioning
sudo systemctl start mom
sudo systemctl start replication