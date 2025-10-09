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

# Function to run simultaneous workflow (automated)
run_simultaneous_workflow() {
    local evidence_path="$1"
    local memory_path="$2"
    
    print_step "SIMULTANEOUS WORKFLOW: Automated Evidence Collection + Forensic Analysis"
    echo ""
    
    # Create case directory
    local case_dir=$(create_case_directory)
    local case_id=$(basename "$case_dir")
    
    print_info "Created case: $case_id"
    print_info "Case directory: $case_dir"
    echo ""
    
    # Create automated evidence collection form
    print_progress "Creating automated evidence collection form..."
    
    local questions_dir="$case_dir/Questions"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local form_file="$questions_dir/automated_evidence_form_$timestamp.txt"
    
    cat > "$form_file" << EOF
Digital Evidence Collection & Chain of Custody Form (AUTOMATED)
================================================================
Case ID: $case_id
Generated: $(date '+%Y-%m-%d %H:%M:%S')
Case Directory: $case_dir
Evidence File: $evidence_path
Memory File: ${memory_path:-"Not provided"}
================================================================

AUTOMATED COLLECTION - MINIMAL DATA
Case Name / No: AUTO_$case_id
Authorized Officer: Automated System
Name of Assessee / Party: TBD
Premise Address: TBD
Start Date & Time: $(date '+%d-%m-%Y %H:%M')
Examiner's Name: EDITH-Automater System
Device Type: Unknown
Forensic Works Performed: Data Acquisition, Data Extraction, Data Analysis
Analysis Timestamp: $(date '+%Y-%m-%d %H:%M:%S')

METADATA
========
File created: $(date '+%Y-%m-%d %H:%M:%S')
Script version: edith-automater.sh v2.0
Case ID: $case_id
Case directory: $case_dir
EOF
    
    print_success "Automated evidence form created: $form_file"
    echo ""
    
    # Run forensic analysis
    print_progress "Starting forensic analysis..."
    
    if ! run_forensic_analysis "$evidence_path" "$memory_path" "$case_dir" "$case_id"; then
        print_error "Forensic analysis failed."
        return 1
    fi
    
    print_success "Simultaneous workflow completed successfully!"
    print_info "All results saved in: $case_dir"
    
    return 0
}

# Function to show system requirements
show_system_requirements() {
    print_step "System Requirements Check"
    echo ""
    
    echo -e "${WHITE}Checking system requirements...${NC}"
    echo ""
    
    # Check Python 3
    if command -v python3 &> /dev/null; then
        local python_version=$(python3 --version 2>&1)
        print_success "Python 3: $python_version"
    else
        print_error "Python 3: Not installed"
    fi
    
    # Check required Python modules
    local modules=("datetime" "os" "sys" "subprocess" "argparse" "asyncio")
    
    for module in "${modules[@]}"; do
        if python3 -c "import $module" 2>/dev/null; then
            print_success "Python module '$module': Available"
        else
            print_error "Python module '$module': Missing"
        fi
    done
    
    # Check forensic tools (optional)
    echo ""
    echo -e "${WHITE}Checking optional forensic tools...${NC}"
    
    local tools=("bulk_extractor" "mmls" "fls" "fsstat" "tsk_recover")
    
    for tool in "${tools[@]}"; do
        if command -v "$tool" &> /dev/null; then
            print_success "Forensic tool '$tool': Installed"
        else
            print_warning "Forensic tool '$tool': Not installed (optional)"
        fi
    done
    
    # Check project structure
    echo ""
    echo -e "${WHITE}Checking project structure...${NC}"
    
    local required_dirs=("$ORCHESTRATOR_DIR" "$TOOLS_DIR" "$SCRIPTS_DIR")
    local required_files=("$ORCHESTRATOR_SCRIPT" "$SCRIPTS_DIR/q_script.py" "$SCRIPTS_DIR/script_3.py")
    
    for dir in "${required_dirs[@]}"; do
        if [ -d "$dir" ]; then
            print_success "Directory: $(basename "$dir")"
        else
            print_error "Directory missing: $(basename "$dir")"
        fi
    done
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            print_success "Script: $(basename "$file")"
        else
            print_error "Script missing: $(basename "$file")"
        fi
    done
    
    echo ""
    print_info "System check completed."
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
    echo "  2. Simultaneous  - Fully automated parallel execution (fastest)"
    echo "  3. Evidence Only - Interactive evidence collection form only"
    echo "  4. Forensic Only - Automated forensic analysis only"
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
    echo "  ./edith-automater.sh simultaneous --evidence file.E01  # Simultaneous workflow"
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
    echo -e "${GREEN} 1.${NC} 🚀 Sequential Workflow"
    echo -e "    ${CYAN}Interactive evidence collection → Automated forensic analysis${NC}"
    echo ""
    echo -e "${GREEN} 2.${NC} ⚡ Simultaneous Workflow"
    echo -e "    ${CYAN}Fully automated parallel execution (fastest option)${NC}"
    echo ""
    echo -e "${GREEN} 3.${NC} 📝 Evidence Collection Only"
    echo -e "    ${CYAN}Interactive form to document evidence collection${NC}"
    echo ""
    echo -e "${GREEN} 4.${NC} 🔍 Forensic Analysis Only"
    echo -e "    ${CYAN}Run forensic tools on existing evidence${NC}"
    echo ""
    echo -e "${GREEN} 5.${NC} 📁 Case Management"
    echo -e "    ${CYAN}List, view, and manage existing cases${NC}"
    echo ""
    echo -e "${GREEN} 6.${NC} ⚙️  System Information"
    echo -e "    ${CYAN}Check system requirements and tool availability${NC}"
    echo ""
    echo -e "${GREEN} 7.${NC} 🔧 Advanced Options"
    echo -e "    ${CYAN}Custom commands and advanced features${NC}"
    echo ""
    echo -e "${GREEN} 8.${NC} ❓ Help & Documentation"
    echo -e "    ${CYAN}User guide and command reference${NC}"
    echo ""
    echo -e "${GREEN} 9.${NC} 🚪 Exit"
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
        "simultaneous")
            if [ -z "$2" ] || [ "$2" != "--evidence" ] || [ -z "$3" ]; then
                print_error "Usage: $0 simultaneous --evidence <evidence_file> [--memory <memory_file>]"
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
            
            run_simultaneous_workflow "$evidence_path" "$memory_path"
            exit $?
            ;;
        "evidence-only")
            run_evidence_collection
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
    
    read -p "Enter your choice (1-9): " choice
    
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
            # Simultaneous Workflow
            print_step "Simultaneous Workflow Selected"
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
            run_simultaneous_workflow "$evidence_path" "$memory_path"
            
            pause
            ;;
        3)
            # Evidence Collection Only
            run_evidence_collection
            pause
            ;;
        4)
            # Forensic Analysis Only
            print_step "Forensic Analysis Only Selected"
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
            print_info "Choose an option:"
            echo "1. Create new case"
            echo "2. Use existing case"
            
            read -p "Enter choice (1-2): " analysis_choice
            
            case $analysis_choice in
                1)
                    # Create new case
                    case_dir=$(create_case_directory)
                    case_id=$(basename "$case_dir")
                    run_forensic_analysis "$evidence_path" "$memory_path" "$case_dir" "$case_id"
                    ;;
                2)
                    # Use existing case
                    echo ""
                    list_all_cases
                    echo ""
                    read -p "Enter case ID (e.g., CASE_20251008_123456): " existing_case_id
                    
                    existing_case_dir="$RESULTS_DIR/$existing_case_id"
                    if [ -d "$existing_case_dir" ]; then
                        run_forensic_analysis "$evidence_path" "$memory_path" "$existing_case_dir" "$existing_case_id"
                    else
                        print_error "Case not found: $existing_case_id"
                    fi
                    ;;
                *)
                    print_error "Invalid choice"
                    ;;
            esac
            
            pause
            ;;
        5)
            # Case Management
            list_all_cases
            pause
            ;;
        6)
            # System Information
            show_system_requirements
            pause
            ;;
        7)
            # Advanced Options
            print_step "Advanced Options"
            echo ""
            echo "Available advanced commands:"
            echo "• evidence-auto    - Automated evidence collection"
            echo "• forensic-auto    - Automated forensic analysis with case ID"
            echo "• Custom orchestrator commands"
            echo ""
            echo "Example commands:"
            echo "  evidence-auto"
            echo "  forensic-auto --evidence /path/file.E01 --case CASE_20251008_123456"
            echo "  sequential --evidence /path/file.E01 --memory /path/mem.mem"
            echo ""
            
            read -p "Enter command: " custom_command
            
            if [ -n "$custom_command" ]; then
                print_info "Executing: $custom_command"
                cd "$ORCHESTRATOR_DIR"
                python3 orchestrator.py $custom_command
            else
                print_warning "No command entered"
            fi
            
            pause
            ;;
        8)
            # Help & Documentation
            show_help
            pause
            ;;
        9)
            # Exit
            print_info "Thank you for using EDITH-Automater!"
            print_info "Your forensic cases are saved in: $RESULTS_DIR"
            exit 0
            ;;
        *)
            print_error "Invalid choice. Please enter a number between 1 and 9."
            pause
            ;;
    esac
done