# Setup concourse on a new Ubuntu server
USER=ubuntu
HOST=52.62.208.189

# Step 1 Install Docker
ssh -i ~/.ssh/wizard.pem $USER@$HOST /bin/bash <<-EOF
    echo "Installing Docker"
    sudo apt-get update
    sudo apt-get install -qq \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg-agent \
        software-properties-common

    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    sudo add-apt-repository \
        "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) \
        stable"
    sudo apt-get update
    sudo apt-get install -qq docker-ce docker-ce-cli containerd.io
    sudo apt-get install -qq docker-compose
    sudo docker swarm init

    echo "Installing NGINX"
    sudo apt-get install -qq nginx
EOF

# # Set envars
. ./envars.secret.sh
ssh -i ~/.ssh/wizard.pem $USER@$HOST /bin/bash <<-EOF
echo "Writing envars"
sudo tee -a /etc/environment <<-EOD
    PGDATABASE="$PGDATABASE"
    PGPASSWORD="$PGPASSWORD"
    PGUSER="$PGUSER"
    ADMIN_USERNAME="$ADMIN_USERNAME"
    ADMIN_PASSWORD="$ADMIN_PASSWORD"
EOD
EOF

# Copy files to server and generate keys
scp -i ~/.ssh/wizard.pem -r server $USER@$HOST:/home/$USER
ssh -i ~/.ssh/wizard.pem $USER@$HOST /bin/bash <<-EOF
cd server
sudo ./keys/generate.sh
EOF

./update.sh