#!/bin/bash

# EDITH-Automater Complete Launcher Script
# Digital Forensics Automation Tool
# Author: EDITH Team
# Version: 2.0

# ================================================================
# CONFIGURATION AND SETUP
# ================================================================

# Colors for beautiful output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORCHESTRATOR_DIR="$SCRIPT_DIR/orchestrator"
ORCHESTRATOR_SCRIPT="$ORCHESTRATOR_DIR/orchestrator.py"
TOOLS_DIR="$SCRIPT_DIR/tools"
SCRIPTS_DIR="$TOOLS_DIR/Scripts"
RESULTS_DIR="$SCRIPT_DIR/Results"

# ================================================================
# UTILITY FUNCTIONS
# ================================================================

print_banner() {
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
    echo -e "${BLUE}=================================================================${NC}"
    echo -e "${BLUE}          EDITH-Automater - Digital Forensics Tool${NC}"
    echo -e "${BLUE}                   Complete Launcher v2.0${NC}"
    echo -e "${BLUE}=================================================================${NC}"
    echo -e "${CYAN}      Evidence → Digital Investigation → Technical → Harness${NC}"
    echo -e "${BLUE}=================================================================${NC}"
    echo ""
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

print_progress() {
    echo -e "${CYAN}[PROGRESS]${NC} $1"
}

# Function to pause and wait for user input
pause() {
    echo ""
    echo -e "${YELLOW}Press Enter to continue...${NC}"
    read
}

# Function to validate file existence
validate_file() {
    local file_path="$1"
    local file_type="$2"

    if [ ! -f "$file_path" ]; then
        print_error "$file_type file not found: $file_path"
        return 1
    fi

    print_success "$file_type file found: $(basename "$file_path")"
    return 0
}

# Function to create case directory
create_case_directory() {
    local case_id="CASE_$(date +%Y%m%d_%H%M%S)"
    local case_dir="$RESULTS_DIR/$case_id"

    print_info "Creating case directory: $case_id"

    # Create main case directory
    mkdir -p "$case_dir"

    # Create subdirectories
    local subdirs=("Questions" "HashDeep_output" "Autopsy_output" "Volatility_output" "ExifTool_output" "BulkExtractor_output" "Final_Reports")

    for subdir in "${subdirs[@]}"; do
        mkdir -p "$case_dir/$subdir"
        print_info "Created: $case_dir/$subdir"
    done

    # Save case info
    cat > "$case_dir/.case_info" << EOF
CASE_ID=$case_id
CASE_DIR=$case_dir
CREATED=$(date -Iseconds)
CREATOR=EDITH-Automater Shell Script
EOF

    echo "$case_dir"
}

# Function to list all cases
list_all_cases() {
    print_step "Listing all forensic cases"
    echo ""

    if [ ! -d "$RESULTS_DIR" ]; then
        print_warning "No Results directory found. No cases exist yet."
        return
    fi

    local case_count=0
    echo -e "${WHITE}Available Cases:${NC}"
    echo "================================================================"

    for case_dir in "$RESULTS_DIR"/CASE_*; do
        if [ -d "$case_dir" ]; then
            case_count=$((case_count + 1))
            local case_id=$(basename "$case_dir")
            local created="Unknown"

            if [ -f "$case_dir/.case_info" ]; then
                created=$(grep "CREATED=" "$case_dir/.case_info" | cut -d'=' -f2-)
            fi

            echo -e "${CYAN}Case ID:${NC} $case_id"
            echo -e "${CYAN}Created:${NC} $created"
            echo -e "${CYAN}Path:${NC} $case_dir"

            # Show subdirectories with file counts
            local total_files=0
            for subdir in "$case_dir"/*; do
                if [ -d "$subdir" ]; then
                    local file_count=$(find "$subdir" -type f 2>/dev/null | wc -l)
                    total_files=$((total_files + file_count))
                    if [ $file_count -gt 0 ]; then
                        echo -e "  ${GREEN}$(basename "$subdir"):${NC} $file_count files"
                    fi
                fi
            done

            echo -e "${CYAN}Total Files:${NC} $total_files"
            echo "----------------------------------------------------------------"
        fi
    done

    if [ $case_count -eq 0 ]; then
        print_warning "No cases found in $RESULTS_DIR"
    else
        print_success "Found $case_count cases"
    fi
}

# Function to run evidence collection (q_script.py)
run_evidence_collection() {
    print_step "Starting Interactive Evidence Collection"

    if [ ! -f "$SCRIPTS_DIR/q_script.py" ]; then
        print_error "q_script.py not found at $SCRIPTS_DIR/q_script.py"
        return 1
    fi

    print_info "Launching evidence collection form..."
    print_info "This will create a new case and collect evidence information interactively."
    echo ""

    cd "$SCRIPTS_DIR"
    python3 q_script.py

    if [ $? -eq 0 ]; then
        print_success "Evidence collection completed successfully!"
    else
        print_error "Evidence collection failed!"
        return 1
    fi

    return 0
}

# Function to run forensic analysis (script_3.py)
run_forensic_analysis() {
    local evidence_path="$1"
    local memory_path="$2"
    local case_dir="$3"
    local case_id="$4"

    print_step "Starting Forensic Analysis"

    if [ ! -f "$SCRIPTS_DIR/script_3.py" ]; then
        print_error "script_3.py not found at $SCRIPTS_DIR/script_3.py"
        return 1
    fi

    print_info "Evidence file: $(basename "$evidence_path")"
    if [ -n "$memory_path" ]; then
        print_info "Memory file: $(basename "$memory_path")"
    fi

    if [ -n "$case_dir" ]; then
        print_info "Using existing case: $(basename "$case_dir")"
        # Set environment variables for script_3.py to use existing case
        export EDITH_USE_EXISTING_CASE="true"
        export EDITH_CASE_DIR="$case_dir"
        export EDITH_CASE_ID="$case_id"
    fi

    cd "$SCRIPTS_DIR"

    # Create input for script_3.py
    local input_data="$evidence_path\n"
    if [ -n "$memory_path" ]; then
        input_data+="$memory_path\n"
    else
        input_data+="\n"
    fi

    print_progress "Running forensic analysis workflow..."
    echo ""

    echo -e "$input_data" | python3 script_3.py

    if [ $? -eq 0 ]; then
        print_success "Forensic analysis completed successfully!"
    else
        print_error "Forensic analysis completed with warnings"
    fi

    # Unset environment variables
    unset EDITH_USE_EXISTING_CASE
    unset EDITH_CASE_DIR
    unset EDITH_CASE_ID

    return 0
}

# Function to run sequential workflow
run_sequential_workflow() {
    local evidence_path="$1"
    local memory_path="$2"

    print_step "SEQUENTIAL WORKFLOW: Evidence Collection → Forensic Analysis"
    echo ""

    # Step 1: Evidence Collection
    print_info "Step 1: Interactive Evidence Collection"
    echo "---------------------------------------"

    if ! run_evidence_collection; then
        print_error "Evidence collection failed. Stopping workflow."
        return 1
    fi

    # Find the latest case directory created
    local latest_case=$(find "$RESULTS_DIR" -name "CASE_*" -type d | sort | tail -1)
    local case_id=$(basename "$latest_case")

    print_success "Evidence collection completed. Case: $case_id"
    echo ""

    # Step 2: Forensic Analysis
    print_info "Step 2: Automated Forensic Analysis"
    echo "-----------------------------------"

    if ! run_forensic_analysis "$evidence_path" "$memory_path" "$latest_case" "$case_id"; then
        print_error "Forensic analysis failed."
        return 1
    fi

    print_success "Sequential workflow completed successfully!"
    print_info "All results saved in: $latest_case"

    return 0
}

# Function to show help
show_help() {
    print_banner

    echo -e "${WHITE}EDITH-Automater Help${NC}"
    echo ""
    echo -e "${CYAN}DESCRIPTION:${NC}"
    echo "  EDITH-Automater is a comprehensive digital forensics automation tool"
    echo "  that streamlines evidence collection and forensic analysis workflows."
    echo ""

    echo -e "${CYAN}WORKFLOW OPTIONS:${NC}"
    echo "  1. Sequential    - Interactive evidence collection followed by automated analysis"
    echo ""

    echo -e "${CYAN}SUPPORTED FILE FORMATS:${NC}"
    echo "  Evidence Files: .E01, .dd, .raw, .img"
    echo "  Memory Files:   .mem, .dmp, .vmem"
    echo ""

    echo -e "${CYAN}FORENSIC TOOLS INCLUDED:${NC}"
    echo "  • HashDeep    - File integrity verification"
    echo "  • Autopsy     - Digital forensics platform"
    echo "  • Volatility  - Memory analysis framework"
    echo "  • ExifTool    - Metadata extraction"
    echo "  • Bulk Extractor - Data extraction and analysis"
    echo ""

    echo -e "${CYAN}COMMAND LINE USAGE:${NC}"
    echo "  ./edith-automater.sh                                    # Interactive menu"
    echo "  ./edith-automater.sh sequential --evidence file.E01    # Sequential workflow"
    echo "  ./edith-automater.sh list-cases                        # List all cases"
    echo "  ./edith-automater.sh help                              # Show this help"
    echo ""

    echo -e "${CYAN}OUTPUT STRUCTURE:${NC}"
    echo "  Results/CASE_YYYYMMDD_HHMMSS/"
    echo "  ├── Questions/           # Evidence collection forms"
    echo "  ├── HashDeep_output/     # File hashes and verification"
    echo "  ├── Autopsy_output/      # Autopsy analysis results"
    echo "  ├── Volatility_output/   # Memory analysis results"
    echo "  ├── ExifTool_output/     # Metadata extraction results"
    echo "  ├── BulkExtractor_output/# Data extraction results"
    echo "  └── Final_Reports/       # Generated reports"
    echo ""

    echo -e "${CYAN}REQUIREMENTS:${NC}"
    echo "  • Python 3.6+"
    echo "  • Linux/Unix system"
    echo "  • Forensic tools (optional, for enhanced functionality)"
    echo ""
}

# ================================================================
# MAIN MENU SYSTEM
# ================================================================

show_main_menu() {
    print_banner

    echo -e "${WHITE}Main Menu - Choose Your Forensic Workflow:${NC}"
    echo ""
    echo -e "${GREEN} 1.${NC} Sequential Workflow"
    echo -e "    ${CYAN}Interactive evidence collection → Automated forensic analysis${NC}"
    echo ""
    echo -e "${GREEN} 2.${NC} Case Management"
    echo -e "    ${CYAN}List, view, and manage existing cases${NC}"
    echo ""
    echo -e "${GREEN} 3.${NC} Help & Documentation"
    echo -e "    ${CYAN}User guide and command reference${NC}"
    echo ""
    echo -e "${GREEN} 4.${NC} Exit"
    echo -e "    ${CYAN}Close EDITH-Automater${NC}"
    echo ""
    echo -e "${BLUE}=================================================================${NC}"
    echo ""
}

# ================================================================
# MAIN EXECUTION LOGIC
# ================================================================

# Check if orchestrator exists
if [ ! -f "$ORCHESTRATOR_SCRIPT" ]; then
    print_error "orchestrator.py not found at $ORCHESTRATOR_SCRIPT"
    print_info "Please ensure you're running this script from the EDITH-Automater root directory"
    pause
    exit 1
fi

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed or not in PATH"
    print_info "Please install Python 3 to use EDITH-Automater"
    pause
    exit 1
fi

# Create Results directory if it doesn't exist
mkdir -p "$RESULTS_DIR"

# Handle command line arguments
if [ $# -gt 0 ]; then
    case "$1" in
        "sequential")
            if [ -z "$2" ] || [ "$2" != "--evidence" ] || [ -z "$3" ]; then
                print_error "Usage: $0 sequential --evidence <evidence_file> [--memory <memory_file>]"
                exit 1
            fi

            evidence_path="$3"
            memory_path=""

            if [ "$4" = "--memory" ] && [ -n "$5" ]; then
                memory_path="$5"
            fi

            if ! validate_file "$evidence_path" "Evidence"; then
                exit 1
            fi

            if [ -n "$memory_path" ] && ! validate_file "$memory_path" "Memory"; then
                exit 1
            fi

            run_sequential_workflow "$evidence_path" "$memory_path"
            exit $?
            ;;
        "list-cases")
            list_all_cases
            pause
            exit 0
            ;;
        "help")
            show_help
            pause
            exit 0
            ;;
        *)
            # Try to pass through to orchestrator.py
            cd "$ORCHESTRATOR_DIR"
            python3 orchestrator.py "$@"
            exit $?
            ;;
    esac
fi

# Interactive mode - main menu loop
while true; do
    show_main_menu

    read -p "Enter your choice (1-4): " choice

    case $choice in
        1)
            # Sequential Workflow
            print_step "Sequential Workflow Selected"
            echo ""

            read -p "Enter evidence file path: " evidence_path

            if ! validate_file "$evidence_path" "Evidence"; then
                pause
                continue
            fi

            read -p "Enter memory file path (optional, press Enter to skip): " memory_path

            if [ -n "$memory_path" ] && ! validate_file "$memory_path" "Memory"; then
                print_warning "Memory file not found, continuing without memory analysis"
                memory_path=""
            fi

            echo ""
            run_sequential_workflow "$evidence_path" "$memory_path"

            pause
            ;;
        2)
            # Case Management
            list_all_cases
            pause
            ;;
        3)
            # Help & Documentation
            show_help
            pause
            ;;
        4)
            # Exit
            print_info "Thank you for using EDITH-Automater!"
            print_info "Your forensic cases are saved in: $RESULTS_DIR"
            exit 0
            ;;
        *)
            print_error "Invalid choice. Please enter a number between 1 and 4."
            pause
            ;;
    esac
done
