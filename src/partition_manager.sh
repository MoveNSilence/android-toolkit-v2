#!/system/bin/sh

# GodTool_V2 Partition Manager
# Handles raw block writes for prism, modemst1, and modemst2

PARTITION=$1
IMAGE_PATH=$2

if [ -z "$PARTITION" ] || [ -z "$IMAGE_PATH" ]; then
    echo "Usage: $0 <partition> <image_path>"
    echo "Supported partitions: prism, modemst1, modemst2"
    exit 1
fi

# Restrict to specified partitions
case "$PARTITION" in
    prism|modemst1|modemst2)
        ;;
    *)
        echo "Error: Partition $PARTITION is not supported."
        exit 1
        ;;
esac

# Resolve the partition name to its block
BLOCK_DEV=$(readlink -f "/dev/block/by-name/$PARTITION")

if [ -z "$BLOCK_DEV" ] || [ ! -e "$BLOCK_DEV" ]; then
    # Fallback or additional check if readlink -f doesn't return anything or block dev doesn't exist
    BLOCK_DEV="/dev/block/by-name/$PARTITION"
fi

BACKUP_DIR="/sdcard/GodTool_Backups"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/${PARTITION}_golden_backup.img"

echo "[*] Performing Golden Backup for $PARTITION to $BACKUP_FILE..."
dd if="$BLOCK_DEV" of="$BACKUP_FILE" bs=4096 conv=notrunc
if [ $? -ne 0 ]; then
    echo "[-] Critical Error: Backup failed. Aborting write."
    exit 1
fi

echo "[+] Golden Backup successful. Proceeding with write..."
echo "[*] Writing $IMAGE_PATH to $BLOCK_DEV..."
dd if="$IMAGE_PATH" of="$BLOCK_DEV" bs=4096 conv=notrunc
if [ $? -ne 0 ]; then
    echo "[-] Error: Write failed."
    exit 1
fi

echo "[*] Syncing data integrity..."
sync

echo "[+] Operation completed successfully."
