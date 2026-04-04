#!/system/bin/sh
# GodTool_V2 - Partition Rewrite Module
# Targets: prism (sda34), modemst1 (sda1), modemst2 (sda2)

PARTITION=$1
IMAGE_IN=$2

# 1. Whitelist & Path Resolution
case $PARTITION in
    prism|modemst1|modemst2)
        TARGET_BLOCK=$(readlink -f /dev/block/by-name/$PARTITION)
        ;;
    *)
        echo "[X] Error: Partition $PARTITION is not in the whitelist."
        exit 1
        ;;
esac

# 2. Mandatory Golden Backup
echo "[+] Creating Golden Backup of $PARTITION..."
mkdir -p /sdcard/GodTool_Backups/
if dd if=$TARGET_BLOCK of=/sdcard/GodTool_Backups/${PARTITION}_orig.img bs=4096 conv=notrunc; then
    sync
    echo "[+] Backup verified and synced."
else
    echo "[X] Critical Error: Backup failed. Aborting write."
    exit 1
fi

# 3. Raw Write Execution
if [ -f "$IMAGE_IN" ]; then
    echo "[!] Rewriting $PARTITION at $TARGET_BLOCK..."
    dd if=$IMAGE_IN of=$TARGET_BLOCK bs=4096 conv=notrunc
    sync
    echo "[+] Rewrite Complete. System Sync'd."
else
    echo "[X] Error: Source image $IMAGE_IN not found."
    exit 1
fi
