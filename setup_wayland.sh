#!/bin/bash
# setup_wayland.sh — one-time setup for real Wayland cursor control
# Run: bash setup_wayland.sh

echo "=== Eye Mouse — Wayland Setup ==="
echo ""
echo "Problem: On GNOME Wayland, Xlib/xdotool only move a virtual XWayland"
echo "pointer. The real desktop cursor is controlled by the Wayland compositor."
echo "Solution: Use /dev/uinput to inject real kernel-level mouse events."
echo ""

# Step 1: Add user to input group
echo "[1] Adding $USER to 'input' group..."
sudo usermod -aG input $USER
echo "    Done."

# Step 2: udev rule for persistent /dev/uinput access
echo ""
echo "[2] Creating udev rule for /dev/uinput..."
echo 'KERNEL=="uinput", GROUP="input", MODE="0660"' | sudo tee /etc/udev/rules.d/99-uinput.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
echo "    Done."

# Step 3: Load uinput kernel module on boot
echo ""
echo "[3] Ensuring uinput module loads on boot..."
echo "uinput" | sudo tee /etc/modules-load.d/uinput.conf
sudo modprobe uinput
echo "    Done."

# Step 4: Temporary permission fix for current session
echo ""
echo "[4] Applying temporary fix for current session..."
sudo chmod 660 /dev/uinput
sudo chgrp input /dev/uinput
# Add current user to input group in current shell (takes effect without relogin for uinput)
sudo setfacl -m u:$USER:rw /dev/uinput 2>/dev/null && echo "    ACL set." || echo "    ACL not available, will work after relogin."

echo ""
echo "=== Setup complete ==="
echo ""
echo "NOTE: Group changes require a RELOGIN to take full effect."
echo "      For NOW, run the app with:"
echo ""
echo "      newgrp input"
echo "      python main.py"
echo ""
echo "      OR log out and log back in, then run: python main.py"
