#!/bin/bash
USER=ubuntu
HOST=52.62.208.189

# Copy files to server
scp -i ~/.ssh/wizard.pem -r server $USER@$HOST:/home/$USER
ssh -i ~/.ssh/wizard.pem $USER@$HOST /bin/bash <<-EOF
cd /home/ubuntu/server/
sudo cp nginx.conf /etc/nginx/nginx.conf
sudo nginx -s reload
sudo docker stack deploy --compose-file docker-compose.yml concourse
sudo docker kill concourse_worker
sudo docker rm concourse_worker
sudo docker run \
    --log-driver "json-file" \
    --log-opt max-file=5 \
    --log-opt max-size=10m \
    --privileged \
    --volume $PWD/keys/worker:/concourse-keys \
    --stop-signal SIGUSR2 \
    --network concourse_network \
    --env=CONCOURSE_TSA_HOST=web:2222 \
    --restart=always \
    --detach=true \
    --name=concourse_worker \
    concourse/concourse \
    worker
EOF
