#!/bin/bash
# Calibration script to be run in Concourse
set -e
MODEL=$1
NUM_CHAINS=15
RUN_TIME=30 # Seconds
JOB_NAME=$MODEL-$RANDOM
mkdir -p /root/.ssh/
echo -e "${AWS_SSH_KEY_1}${AWS_SSH_KEY_2}" > /root/.ssh/wizard.pem
ls -la /root
ls -la /root/.ssh
chmod 600 /root/.ssh/wizard.pem
autumn-repo/scripts/aws/run.sh run calibrate \
    $JOB_NAME \
    $MODEL \
    $NUM_CHAINS \
    $RUN_TIME | tee calibration.log

# Check output log for run name.
MATCH="Calibration finished for"
RUN_NAME=$(sed -n "/$MATCH/p" calibration.log | cut -d' ' -f4)
if [[ -z "$RUN_NAME" ]]
then
      echo "Completed run $RUN_NAME"
      echo "$RUN_NAME" > run-name.log
else
      echo "Run for $MODEL failed."
      exit 1
fi
