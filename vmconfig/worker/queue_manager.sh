#!/bin/bash
QUEUE_DIR="/var/queue/coursero"
PROCESSING_DIR="/var/processing/coursero"
RESULTS_DIR="/var/results/coursero"

mkdir -p $QUEUE_DIR $PROCESSING_DIR $RESULTS_DIR

echo "$(date) - Queue manager started" >> /var/log/coursero_queue.log

while true; do
  for file in $QUEUE_DIR/*; do
    if [ -f "$file" ]; then
      filename=$(basename "$file")
      echo "$(date) - Processing $filename" >> /var/log/coursero_queue.log
      mv "$file" "$PROCESSING_DIR/$filename"
      /usr/local/bin/process_submission.sh "$PROCESSING_DIR/$filename"
      rm "$PROCESSING_DIR/$filename"
    fi
  done
  sleep 5
done
