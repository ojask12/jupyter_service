sudo mkdir -p /var/run
sudo touch /home/ubuntu/jupyter_service/instances/jupyter_instances.json
sudo chown ubuntu:ubuntu /home/ubuntu/jupyter_service/instances/jupyter_instances.json
mkdir -p /home/ubuntu/jupyter_service/instances/common
chmod 555 /home/ubuntu/jupyter_service/instances/common   # read & execute only
chown -R ubuntu:ubuntu /home/ubuntu/jupyter_service/instances/common
echo "{}" > /home/ubuntu/jupyter_service/instances/jupyter_instances.json

sudo apt update
sudo apt install -y nginx

sudo apt update
sudo apt install -y certbot python3-certbot-nginx

sudo certbot --nginx -d jupyter.example.com

sudo systemctl enable nginx
sudo systemctl start nginx

sudo rm /etc/nginx/sites-enabled/default
sudo nano /etc/nginx/sites-available/jupyter_service
sudo ln -s /etc/nginx/sites-available/jupyter_service \
           /etc/nginx/sites-enabled/jupyter_service
sudo nginx -t
sudo systemctl reload nginx
sudo ufw allow 'Nginx Full'

sudo chmod +x /home/ubuntu/jupyter_service/scripts/*.sh
sudo chown -R ubuntu:ubuntu /home/ubuntu/jupyter_service

sudo cp /home/ubuntu/jupyter_service/systemd/jupyter-backend.service /etc/systemd/system/jupyter-backend.service
sudo cp /home/ubuntu/jupyter_service/systemd/jupyter-frontend.service /etc/systemd/system/jupyter-frontend.service
sudo systemctl daemon-reexec
sudo systemctl daemon-reload

sudo systemctl enable jupyter-backend
sudo systemctl start jupyter-backend

sudo systemctl enable jupyter-frontend
sudo systemctl start jupyter-frontend

sudo systemctl status jupyter-backend
sudo systemctl status jupyter-frontend

sudo systemctl restart jupyter-backend
sudo systemctl restart jupyter-frontend

# journalctl -u jupyter-backend -f
# journalctl -u jupyter-frontend -f
