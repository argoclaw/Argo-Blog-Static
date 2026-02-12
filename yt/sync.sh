#!/bin/bash
# Sync YT Viewer files to OpenResty container
# Usage: ./sync.sh
# Override container name: YTVIEWER_CONTAINER=mycontainer ./sync.sh

SRC_DIR="/home/opc/.openclaw/workspace/yt-viewer"
CONTAINER="${YTVIEWER_CONTAINER:-1Panel-openresty-OLCQ}"
DEST_DIR="/www/sites/openclaw.996667.xyz/yt-viewer"

# Verify container exists
if ! sudo docker ps -q -f name="$CONTAINER" | grep -q .; then
    echo "❌ Container '$CONTAINER' not running" >&2
    echo "Available containers:" >&2
    sudo docker ps --format '{{.Names}}' >&2
    exit 1
fi

echo "Syncing YT Viewer files to $CONTAINER..."

# Sync HTML files
sudo docker cp "${SRC_DIR}/index.html" "${CONTAINER}:${DEST_DIR}/"
sudo docker cp "${SRC_DIR}/video.html" "${CONTAINER}:${DEST_DIR}/"

# Sync data file
sudo docker cp "${SRC_DIR}/data/videos.json" "${CONTAINER}:${DEST_DIR}/data/"

echo "✅ Files synced to ${DEST_DIR}"
