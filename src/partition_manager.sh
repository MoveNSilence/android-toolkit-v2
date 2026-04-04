#!/system/bin/sh
# GodTool_V2 - Partition Rewrite Module
# Targets: sda34 (Prism), sda1 (ModemST1), sda2 (ModemST2)

PARTITION=$1  # e.g., prism
IMAGE_IN=$2   # path to your new .img file

# 1. Resolve Path via your provided mapping
TARGET_BLOCK=$(readlink -f /dev/block/by-name/$PARTITION)

# 2. Pristine Backup (The Golden Copy)
echo "[+] Creating Golden Backup of $PARTITION..."
mkdir -p /sdcard/GodTool_Backups/
dd if=$TARGET_BLOCK of=/sdcard/GodTool_Backups/${PARTITION}_orig.img bs=4096
sync

# 3. Raw Write Execution
if [ -f "$IMAGE_IN" ]; then
    echo "[!] Rewriting $PARTITION at $TARGET_BLOCK..."
    dd if=$IMAGE_IN of=$TARGET_BLOCK bs=4096 conv=notrunc
    sync
    echo "[+] Rewrite Complete. System Sync'd."
else
    echo "[X] Error: Source image $IMAGE_IN not found."
fi
