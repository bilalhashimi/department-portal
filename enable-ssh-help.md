# 🔧 **Enable SSH on Your Raspberry Pi**

## 🎯 **Your Pi Status:**
✅ **Found**: `raspberrypi.local`  
❌ **SSH**: Not enabled  

---

## 🔓 **Method 1: Enable via Pi Desktop (Easiest)**

1. Connect keyboard/monitor to your Pi
2. Open **Preferences** → **Raspberry Pi Configuration**
3. Go to **Interfaces** tab
4. Enable **SSH**
5. Click **OK** and reboot

---

## 🔓 **Method 2: Enable via Terminal**

If you have terminal access on the Pi:
```bash
sudo systemctl enable ssh
sudo systemctl start ssh
```

---

## 🔓 **Method 3: Enable via SD Card (No keyboard needed)**

1. **Power off** your Pi
2. **Remove the SD card** and insert into your laptop
3. **Open the boot partition** (should appear as a drive)
4. **Create an empty file** named `ssh` (no extension)
5. **Safely eject** the SD card
6. **Put it back** in the Pi and power on

---

## ✅ **After Enabling SSH**

Once SSH is enabled, run this command to deploy:
```bash
./deploy-to-pi.sh
```

When prompted for IP address, enter: **`raspberrypi.local`**

---

## 🆘 **Still Need Help?**

**Check if SSH is working:**
```bash
ssh pi@raspberrypi.local
```

**Default Pi credentials:**
- Username: `pi`
- Password: `raspberry` (or what you set during setup)

**If you get "connection refused":**
- SSH is still not enabled
- Try the SD card method above

**If you get "permission denied":**
- SSH is working! You just need the correct password
- Run the deployment script: `./deploy-to-pi.sh` 