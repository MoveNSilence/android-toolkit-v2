#!/system/bin/sh
# GodTool_V2 Partition Rewrite Module
# Targets: prism (sda34), modemst1 (sda1), modemst2 (sda2)

PARTITION=$1
IMAGE_IN=$2

# Resolve block path
case $PARTITION in
    prism|modemst1|modemst2)
        TARGET_BLOCK=$(readlink -f /dev/block/by-name/$PARTITION)
        ;;
    *)
        echo "[X] Error: Unauthorized partition."
        exit 1
        ;;
esac

# Mandatory Golden Backup
echo "[+] Creating Golden Backup..."
mkdir -p /sdcard/GodTool_Backups/
if dd if=$TARGET_BLOCK of=/sdcard/GodTool_Backups/${PARTITION}_orig.img bs=4096 conv=notrunc; then
    sync
else
    echo "[X] Backup Failed. Aborting."
    exit 1
fi

# Pristine Rewrite
if [ -f "$IMAGE_IN" ]; then
    echo "[!] Writing $IMAGE_IN to $TARGET_BLOCK..."
    dd if=$IMAGE_IN of=$TARGET_BLOCK bs=4096 conv=notrunc
    sync
    echo "[+] Success."
else
    echo "[X] Source Image Missing."
    exit 1
fi
