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

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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
echo -e "${GREEN}EDITH Automater Setup${NC}"
echo -e "${GREEN}========================${NC}"

# Make the main script executable
echo "Making edith-automater.sh executable..."
chmod +x edith-automater.sh

if [ -x edith-automater.sh ]; then
    echo -e "${GREEN}✅ edith-automater.sh is now executable${NC}"
else
    echo -e "${RED}❌ Failed to make edith-automater.sh executable${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🚀 Setup complete!${NC}"
echo ""
echo "You can now run EDITH Automater in these ways:"
echo ""
echo "1. Double-click: edith-automater.sh (if your file manager supports it)"
echo "2. Terminal: ./edith-automater.sh"
echo "3. Full path: $SCRIPT_DIR/edith-automater.sh"
echo ""

# Ask if user wants to install desktop entry
read -p "Would you like to install a desktop entry for easy access? (y/n): " install_desktop

if [[ $install_desktop =~ ^[Yy]$ ]]; then
    echo ""
    echo "Installing desktop entry..."
    
    # Create desktop entry
    desktop_dir="$HOME/.local/share/applications"
    mkdir -p "$desktop_dir"
    
    cat > "$desktop_dir/edith-automater.desktop" << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=EDITH Automater
Comment=Digital Forensics Automation Tool
Exec=/home/shirish/Project/Zetpeak/Edith_t-Automater/edith-automater.sh
Icon=/home/shirish/Project/Zetpeak/Edith_t-Automater/icon.png
Path=/home/shirish/Project/Zetpeak/Edith_t-Automater
Terminal=true
StartupNotify=false
Categories=Development;Science;Security;
Keywords=forensics;digital;investigation;automation;
EOF

    chmod +x "$desktop_dir/edith-automater.desktop"
    
    if [ -f "$desktop_dir/edith-automater.desktop" ]; then
        echo -e "${GREEN}✅ Desktop entry installed!${NC}"
        echo "You can now find 'EDITH Automater' in your applications menu"
        echo "Or search for 'EDITH Automater' in your application launcher"
    else
        echo -e "${RED}❌ Failed to install desktop entry${NC}"
    fi
else
    echo "Skipping desktop entry installation"
fi

echo ""
echo -e "${CYAN}🔍 Testing the installation...${NC}"
echo "Running: ./edith-automater.sh help"
echo ""

# Test run the help command - use the bash script's help, not the Python orchestrator
if [ -x "./edith-automater.sh" ]; then
    timeout 10s ./edith-automater.sh help || echo "Help command completed"
else
    echo -e "${RED}❌ Cannot test - edith-automater.sh is not executable${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 EDITH Automater is ready to use!${NC}"
echo "   Run './edith-automater.sh' to start the interactive menu"
echo ""