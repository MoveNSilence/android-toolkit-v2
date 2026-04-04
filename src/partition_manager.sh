#!/system/bin/sh
# GodTool_V2 - Partition Rewrite Module (Pristine Version)
# Targets: prism, modemst1, modemst2

PARTITION=$1
IMAGE_IN=$2

# Whitelist Resolution
case $PARTITION in
    prism|modemst1|modemst2)
        TARGET_BLOCK=$(readlink -f /dev/block/by-name/$PARTITION)
        ;;
    *)
        echo "[X] Error: Unauthorized partition."
        exit 1
        ;;
esac

# Golden Backup Protocol
echo "[+] Creating Golden Backup..."
mkdir -p /sdcard/GodTool_Backups/
if dd if=$TARGET_BLOCK of=/sdcard/GodTool_Backups/${PARTITION}_orig.img bs=4096 conv=notrunc; then
    sync
else
    echo "[X] Backup Failed. Overwrite Aborted."
    exit 1
fi

# Raw DD Write Logic
if [ -f "$IMAGE_IN" ]; then
    echo "[!] Executing Raw DD Write to $TARGET_BLOCK..."
    dd if=$IMAGE_IN of=$TARGET_BLOCK bs=4096 conv=notrunc
    sync
    echo "[+] Rewrite Successful."
else
    echo "[X] Source Image Missing."
    exit 1
fi
