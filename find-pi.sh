#!/bin/bash

echo "🔍 Searching for your Raspberry Pi..."
echo "This may take a minute..."
echo ""

# Common IP ranges to check
networks=(
    "192.168.7"
    "192.168.1" 
    "192.168.0"
    "10.0.0"
)

found_devices=()

for network in "${networks[@]}"; do
    echo "Checking $network.x network..."
    
    for i in {1..50}; do
        ip="$network.$i"
        if ping -c 1 -W 1 "$ip" >/dev/null 2>&1; then
            echo "  📡 Device found at: $ip"
            
            # Try to identify if it's a Raspberry Pi
            # Check SSH on port 22
            if nc -z -w1 "$ip" 22 2>/dev/null; then
                echo "    ✅ SSH is available"
                found_devices+=("$ip")
            fi
        fi
    done
done

echo ""
echo "🍓 Potential Raspberry Pi devices:"

if [ ${#found_devices[@]} -eq 0 ]; then
    echo "❌ No devices with SSH found."
    echo ""
    echo "💡 Try these manual methods:"
    echo "1. Check your router admin page (usually http://192.168.1.1 or http://192.168.7.1)"
    echo "2. Look for 'Connected Devices' or 'DHCP Clients'"
    echo "3. Find a device named 'raspberry', 'pi', or similar"
    echo "4. If you have access to the Pi directly, run: hostname -I"
else
    echo ""
    for device in "${found_devices[@]}"; do
        echo "🎯 $device - Try: ssh pi@$device"
    done
    
    echo ""
    echo "To test SSH connection to a device:"
    echo "ssh pi@[IP_ADDRESS]"
    echo ""
    echo "Once you find the right IP, run: ./deploy-to-pi.sh"
fi 