#!/usr/bin/env bash
PLIST=~/Library/LaunchAgents/com.tokentracker.app.plist

launchctl unload "$PLIST" 2>/dev/null && echo "✓ Service arrêté." || true
rm -f "$PLIST" && echo "✓ LaunchAgent supprimé."
pkill -f "python.*main.py" 2>/dev/null && echo "✓ App fermée." || true
echo "Token Tracker désinstallé."
