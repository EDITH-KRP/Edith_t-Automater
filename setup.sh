#!/bin/bash

# EDITH Automater Setup Script
# This script makes the main launcher executable and optionally installs a desktop entry

# Colors for beautiful output
BLUE='\033[0;34m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

clear

echo -e "${BLUE}"
cat << "EOF"
 ███████╗██████╗ ██╗████████╗██╗  ██╗
 ██╔════╝██╔══██╗██║╚══██╔══╝██║  ██║
 █████╗  ██║  ██║██║   ██║   ███████║
 ██╔══╝  ██║  ██║██║   ██║   ██╔══██║
 ███████╗██████╔╝██║   ██║   ██║  ██║
 ╚══════╝╚═════╝ ╚═╝   ╚═╝   ╚═╝  ╚═╝

 █████╗ ██╗   ██╗████████╗ ██████╗ ███╗   ███╗ █████╗ ████████╗███████╗██████╗
██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗████╗ ████║██╔══██╗╚══██╔══╝██╔════╝██╔══██╗
███████║██║   ██║   ██║   ██║   ██║██╔████╔██║███████║   ██║   █████╗  ██████╔╝
██╔══██║██║   ██║   ██║   ██║   ██║██║╚██╔╝██║██╔══██║   ██║   ██╔══╝  ██╔══██╗
██║  ██║╚██████╔╝   ██║   ╚██████╔╝██║ ╚═╝ ██║██║  ██║   ██║   ███████╗██║  ██║
╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝

                    Digital Forensics Automation Tool
EOF
echo -e "${NC}"

echo -e "${CYAN}=================================================================${NC}"
echo -e "${CYAN}         Evidence → Digital Investigation → Technical → Harness${NC}"
echo -e "${CYAN}=================================================================${NC}"
echo ""
echo -e "${GREEN}🔧 EDITH Automater Setup${NC}"
echo -e "${GREEN}========================${NC}"

# Make the main script executable
echo "Making edith-automater.sh executable..."
chmod +x edith-automater.sh
chmod +x edith-automater.desktop

if [ -x edith-automater.sh ]; then
    echo " edith-automater.sh is now executable"
else
    echo " Failed to make edith-automater.sh executable"
    exit 1
fi

echo ""
echo " Setup complete!"
echo ""
echo "You can now run EDITH Automater in these ways:"
echo ""
echo "1. Double-click: edith-automater.sh (if your file manager supports it)"
echo "2. Terminal: ./edith-automater.sh"
echo "3. Full path: /home/shirish/Project/Zetpeak/Edith_t-Automater/edith-automater.sh"
echo ""

# Ask if user wants to install desktop entry
read -p "Would you like to install a desktop entry for easy access? (y/n): " install_desktop

if [[ $install_desktop =~ ^[Yy]$ ]]; then
    desktop_dir="$HOME/.local/share/applications"
    mkdir -p "$desktop_dir"
    cp edith-automater.desktop "$desktop_dir/"

    if [ -f "$desktop_dir/edith-automater.desktop" ]; then
        echo " Desktop entry installed! You can now find 'EDITH Automater' in your applications menu."
    else
        echo " Failed to install desktop entry"
    fi
fi

echo ""
echo "🔍 Testing the script..."
echo "Running: ./edith-automater.sh --help"
echo ""

# Test run the help command
./edith-automater.sh --help

echo ""
echo " EDITH Automater is ready to use!"
echo "   Run './edith-automater.sh' to start the interactive menu"
