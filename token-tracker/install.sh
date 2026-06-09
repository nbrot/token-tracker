#!/usr/bin/env bash
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST=~/Library/LaunchAgents/com.tokentracker.app.plist
PYTHON="$DIR/.venv/bin/python"

# Create venv + install deps if needed
if [ ! -f "$PYTHON" ]; then
    /opt/homebrew/bin/python3.12 -m venv "$DIR/.venv"
    "$DIR/.venv/bin/pip" install -r "$DIR/requirements.txt" -q
fi

# Write LaunchAgent plist
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.tokentracker.app</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON</string>
        <string>$DIR/main.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardErrorPath</key>
    <string>$DIR/error.log</string>
</dict>
</plist>
EOF

# Load it immediately (starts the app now + at every login)
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"

echo "✓ Token Tracker installé — démarrera automatiquement à chaque login."
echo "  Pour désinstaller : ./uninstall.sh"
