#!/bin/bash

# Unified Desktop Icon Management Script for Electronic Component Inventory
# Combines icon installation, cache clearing, and desktop refreshing

echo "=== Unified Desktop Icon Management ==="
echo "Electronic Component Inventory"
echo ""

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  --force    Force refresh with aggressive cache clearing"
    echo "  --simple   Simple refresh without cache clearing"
    echo "  --help     Show this help message"
    echo ""
    echo "Default behavior: Force refresh mode"
}

# Parse command line arguments
FORCE_MODE=true

case "${1:-}" in
    --simple)
        FORCE_MODE=false
        echo "🔄 Using simple refresh mode..."
        ;;
    --force)
        FORCE_MODE=true
        echo "🔄 Using force refresh mode..."
        ;;
    --help|-h)
        show_usage
        exit 0
        ;;
    "")
        echo "🔄 Using default force refresh mode..."
        ;;
    *)
        echo "❌ Unknown option: $1"
        show_usage
        exit 1
        ;;
esac

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Create required directories
echo "📁 Creating required directories..."
mkdir -p ~/.local/share/applications
mkdir -p ~/.local/share/icons/hicolor/{16x16,24x24,32x32,48x48,64x64,128x128,256x256}/apps

# Install desktop entry
echo "📋 Installing desktop entry..."
if [ -f "$SCRIPT_DIR/electronic-inventory.desktop" ]; then
    cp "$SCRIPT_DIR/electronic-inventory.desktop" ~/.local/share/applications/
    chmod +x ~/.local/share/applications/electronic-inventory.desktop
    echo "✅ Desktop entry installed"
else
    echo "⚠️  Warning: electronic-inventory.desktop not found in $SCRIPT_DIR"
fi

# Install icons (remove old symlinks first to avoid dangling link errors)
echo "🎨 Installing icons..."

# Remove old symlinks that might be dangling
rm -f ~/.local/share/icons/hicolor/48x48/apps/electronic-component-inventory.png
rm -f ~/.local/share/icons/hicolor/64x64/apps/electronic-component-inventory.png
rm -f ~/.local/share/icons/hicolor/128x128/apps/electronic-component-inventory.png

# Install main icons (copy for reliability, then create symlinks)
if [ -f "$SCRIPT_DIR/frontend/static/images/electronic-inventory-icon-48.png" ]; then
    cp "$SCRIPT_DIR/frontend/static/images/electronic-inventory-icon-48.png" ~/.local/share/icons/hicolor/48x48/apps/electronic-component-inventory.png
    ln -sf "$SCRIPT_DIR/frontend/static/images/electronic-inventory-icon-48.png" ~/.local/share/icons/hicolor/48x48/apps/electronic-component-inventory.png
    echo "✅ 48x48 icon installed"
fi

if [ -f "$SCRIPT_DIR/frontend/static/images/electronic-inventory-icon-64.png" ]; then
    cp "$SCRIPT_DIR/frontend/static/images/electronic-inventory-icon-64.png" ~/.local/share/icons/hicolor/64x64/apps/electronic-component-inventory.png
    ln -sf "$SCRIPT_DIR/frontend/static/images/electronic-inventory-icon-64.png" ~/.local/share/icons/hicolor/64x64/apps/electronic-component-inventory.png
    echo "✅ 64x64 icon installed"
fi

if [ -f "$SCRIPT_DIR/frontend/static/images/electronic-inventory-icon-128.png" ]; then
    cp "$SCRIPT_DIR/frontend/static/images/electronic-inventory-icon-128.png" ~/.local/share/icons/hicolor/128x128/apps/electronic-component-inventory.png
    ln -sf "$SCRIPT_DIR/frontend/static/images/electronic-inventory-icon-128.png" ~/.local/share/icons/hicolor/128x128/apps/electronic-component-inventory.png
    echo "✅ 128x128 icon installed"
fi

# Force refresh mode operations
if [ "$FORCE_MODE" = true ]; then
    echo "🧹 Force mode: Clearing caches..."

    # Kill desktop environment processes (force refresh)
    echo "🔄 Restarting desktop environment processes..."
    killall nautilus 2>/dev/null || true
    killall thunar 2>/dev/null || true
    killall dolphin 2>/dev/null || true
    killall nemo 2>/dev/null || true
    killall caja 2>/dev/null || true

    # Clear caches aggressively
    echo "🧹 Clearing icon and thumbnail caches..."
    rm -rf ~/.cache/thumbnails/* 2>/dev/null || true
    rm -rf ~/.cache/icon-cache/* 2>/dev/null || true
    rm -rf ~/.cache/gvfs-metadata/* 2>/dev/null || true
    rm -rf ~/.cache/hicolor-icon-theme.cache 2>/dev/null || true
fi

# Update icon cache
echo "🔄 Updating icon cache..."
if command_exists gtk-update-icon-cache; then
    gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor/ 2>/dev/null || true
    echo "✅ GTK icon cache updated"
elif command_exists kbuildsycoca5; then
    kbuildsycoca5 2>/dev/null || true
    echo "✅ KDE icon cache updated"
fi

# Update desktop database
echo "🔄 Updating desktop database..."
if command_exists update-desktop-database; then
    update-desktop-database ~/.local/share/applications/ 2>/dev/null || true
    echo "✅ Desktop database updated"
fi

# Try to refresh desktop environment
echo "🔄 Refreshing desktop environment..."
if command_exists gsettings; then
    # GNOME
    gsettings set org.gnome.desktop.interface icon-theme 'hicolor' 2>/dev/null || true
    echo "✅ GNOME desktop refreshed"
elif command_exists kquitapp5 && command_exists kstart5; then
    # KDE
    kquitapp5 plasmashell 2>/dev/null || true
    sleep 1
    kstart5 plasmashell 2>/dev/null || true
    echo "✅ KDE desktop refreshed"
fi

# Final verification
echo ""
echo "🔍 Verification:"
echo "Desktop entry: $(ls -la ~/.local/share/applications/electronic-inventory.desktop 2>/dev/null || echo 'Not found')"
echo "Icon files: $(ls -la ~/.local/share/icons/hicolor/*/apps/electronic-component-inventory.png 2>/dev/null | wc -l) installed"

echo ""
echo "✅ Desktop icon management completed!"
echo ""

if [ "$FORCE_MODE" = true ]; then
    echo "💡 Force refresh mode was used. If icons still don't update:"
    echo "   1. Log out and log back in"
    echo "   2. Restart your computer"
    echo "   3. Try: killall -HUP gnome-shell (GNOME)"
    echo "   4. Try: kquitapp5 plasmashell && kstart5 plasmashell (KDE)"
    echo ""
fi

echo "🚀 You can now run the application with:"
echo "   ./run.sh    (system tray mode)"
echo "   ./tray_app.py (direct tray app)"
echo "   python3 backend/app.py (web only)"
