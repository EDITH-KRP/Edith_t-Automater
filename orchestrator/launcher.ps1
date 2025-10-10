# EDITH-Automater Complete PowerShell Launcher
# Digital Forensics Automation Tool
# Author: EDITH Team
# Version: 2.0

param(
    [string]$Command = "",
    [string]$EvidencePath = "",
    [string]$MemoryPath = "",
    [string]$Case = "",
    [switch]$Help = $false,
    [switch]$Interactive = $false
)

# ================================================================
# CONFIGURATION AND SETUP
# ================================================================

# Get the directory where this script is located
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Split-Path -Parent $ScriptDir
$OrchestratorDir = $ScriptDir
$OrchestratorScript = Join-Path $OrchestratorDir "orchestrator.py"
$ToolsDir = Join-Path $ProjectRoot "tools"
$ScriptsDir = Join-Path $ToolsDir "Scripts"
$ResultsDir = Join-Path $ProjectRoot "Results"

# Initialize logging
$LogFile = Join-Path $OrchestratorDir "launcher.log"

# ================================================================
# LOGGING AND PROGRESS FUNCTIONS
# ================================================================

function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$Timestamp] [$Level] $Message"
    
    try {
        Add-Content -Path $LogFile -Value $LogEntry -ErrorAction SilentlyContinue
    } catch {
        # Silently continue if logging fails
    }
}

function Show-ProgressBar {
    param(
        [string]$Activity,
        [string]$Status,
        [int]$PercentComplete = 0
    )
    
    Write-Progress -Activity $Activity -Status $Status -PercentComplete $PercentComplete
}

function Hide-ProgressBar {
    Write-Progress -Activity "Complete" -Completed
}

# ================================================================
# UTILITY FUNCTIONS
# ================================================================

function Write-Banner {
    Clear-Host
    Write-Host @"
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
"@ -ForegroundColor Blue

    Write-Host "=================================================================" -ForegroundColor Blue
    Write-Host "          EDITH-Automater - Digital Forensics Tool" -ForegroundColor Blue
    Write-Host "                   Complete Launcher v2.0" -ForegroundColor Blue
    Write-Host "=================================================================" -ForegroundColor Blue
    Write-Host "      Evidence → Digital Investigation → Technical → Harness" -ForegroundColor Cyan
    Write-Host "=================================================================" -ForegroundColor Blue
    Write-Host ""
}

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
    Write-Log -Message $Message -Level "INFO"
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
    Write-Log -Message $Message -Level "SUCCESS"
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
    Write-Log -Message $Message -Level "WARNING"
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
    Write-Log -Message $Message -Level "ERROR"
}

function Write-Step {
    param([string]$Message)
    Write-Host "[STEP] $Message" -ForegroundColor Magenta
    Write-Log -Message $Message -Level "STEP"
}

function Write-Progress {
    param([string]$Message)
    Write-Host "[PROGRESS] $Message" -ForegroundColor Cyan
    Write-Log -Message $Message -Level "PROGRESS"
}

function Wait-UserInput {
    Write-Host ""
    Write-Host "Press Enter to continue..." -ForegroundColor Yellow
    Read-Host
}

function Invoke-OrchestratorCommand {
    param(
        [string]$Command,
        [string]$EvidencePath = "",
        [string]$MemoryPath = "",
        [string]$CaseId = ""
    )

    Write-Log "Invoking orchestrator.py with command: $Command"
    
    try {
        $Arguments = @("orchestrator.py", $Command)
        
        if ($EvidencePath) {
            $Arguments += "--evidence", $EvidencePath
        }
        
        if ($MemoryPath) {
            $Arguments += "--memory", $MemoryPath
        }
        
        if ($CaseId) {
            $Arguments += "--case", $CaseId
        }

        Write-Progress "Executing orchestrator.py workflow..."
        
        $OriginalLocation = Get-Location
        Set-Location $OrchestratorDir
        
        $Process = Start-Process -FilePath $PythonCmd -ArgumentList $Arguments -Wait -PassThru -NoNewWindow -RedirectStandardOutput "orchestrator_output.log" -RedirectStandardError "orchestrator_error.log"
        
        Set-Location $OriginalLocation

        if ($Process.ExitCode -eq 0) {
            Write-Success "Orchestrator command completed successfully"
            return $true
        } else {
            Write-Warning "Orchestrator command completed with warnings (Exit code: $($Process.ExitCode))"
            
            # Show error output if available
            $ErrorLogPath = Join-Path $OrchestratorDir "orchestrator_error.log"
            if (Test-Path $ErrorLogPath) {
                $ErrorContent = Get-Content $ErrorLogPath -Tail 5
                foreach ($Line in $ErrorContent) {
                    if ($Line.Trim()) {
                        Write-Warning "  $Line"
                    }
                }
            }
            
            return $false
        }
    }
    catch {
        Write-Error "Failed to execute orchestrator command: $($_.Exception.Message)"
        Write-Log "Orchestrator execution failed: $($_.Exception.Message)" -Level "ERROR"
        return $false
    }
}

function Test-FileExists {
    param(
        [string]$FilePath,
        [string]$FileType
    )

    if (-not (Test-Path $FilePath)) {
        Write-Error "$FileType file not found: $FilePath"
        return $false
    }

    Write-Success "$FileType file found: $(Split-Path $FilePath -Leaf)"
    return $true
}

function New-AutomatedEvidenceCollection {
    param(
        [string]$CaseId,
        [string]$CaseDir
    )

    Write-Step "Automated Evidence Collection"
    Write-Info "Creating automated evidence collection form for case: $CaseId"

    $QuestionsDir = Join-Path $CaseDir "Questions"
    $Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $FormFile = Join-Path $QuestionsDir "evidence_collection_form_$Timestamp.txt"

    # Generate automated form with default values
    $AutomatedAnswers = @{
        "Case Name / No" = "AUTO_$CaseId"
        "Authorized Officer" = "Automated System"
        "Name of Assessee / Party" = "TBD"
        "Premise Address" = "TBD"
        "Start Date & Time" = (Get-Date -Format 'dd-MM-yyyy HH:mm')
        "End Date & Time" = "TBD"
        "Search Date" = (Get-Date -Format 'dd-MM-yyyy')
        "Examiner's Name and Details" = "EDITH-Automater System"
        "Digital Forensic Examiner" = "EDITH-Automater"
        "Working Hours" = "Automated"
        "Device Type" = "Unknown"
        "Device Status at Seizure" = "Unknown"
        "Volatile Memory / RAM Collected" = "No"
        "Shut Down Type" = "N/A"
        "Is the suspected media encrypted" = "Unknown"
        "Hard Disk Handling" = "Imaging"
        "Forensic Works Performed" = "Data Acquisition, Data Extraction, Data Analysis"
        "Is Hash Value Calculated" = "Yes"
        "Algorithm Used" = "SHA1"
        "Storage Master Copy" = "TBD"
        "Storage Working Copy" = "TBD"
        "Hard Disk Capacity" = "TBD"
        "No. of HDD Used" = "1"
        "Is Witness Signature Taken" = "No"
        "Witness Name" = "N/A"
    }

    # Create automated form content
    $FormContent = @"
Digital Evidence Collection & Chain of Custody Form (AUTOMATED)
================================================================
Case ID: $CaseId
Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Case Directory: $CaseDir
================================================================

"@

    foreach ($Question in $AutomatedAnswers.GetEnumerator()) {
        $FormContent += "$($Question.Key): $($Question.Value)`n"
    }

    $FormContent += @"

================================================================
METADATA
================================================================
File created: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Script version: launcher.ps1 automated
Case ID: $CaseId
Case directory: $CaseDir
"@

    Set-Content -Path $FormFile -Value $FormContent -Encoding UTF8

    Write-Success "Automated evidence collection form created: $(Split-Path $FormFile -Leaf)"
    return @{
        Status = "success"
        CaseId = $CaseId
        CaseDir = $CaseDir
        FormFile = $FormFile
        Message = "Automated evidence collection completed successfully"
    }
}

function New-CaseDirectory {
    param([string]$Prefix = "CASE")
    
    $CaseId = "$Prefix`_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    $CaseDir = Join-Path $ResultsDir $CaseId

    Write-Info "Creating case directory: $CaseId"

    # Create main case directory
    New-Item -Path $CaseDir -ItemType Directory -Force | Out-Null

    # Create subdirectories
    $SubDirs = @(
        "Questions",
        "HashDeep_output",
        "Autopsy_output",
        "Volatility_output",
        "ExifTool_output",
        "BulkExtractor_output",
        "Final_Reports"
    )

    foreach ($SubDir in $SubDirs) {
        $SubDirPath = Join-Path $CaseDir $SubDir
        New-Item -Path $SubDirPath -ItemType Directory -Force | Out-Null
        Write-Info "Created: $SubDirPath"
    }

    # Save case info
    $CaseInfo = @"
CASE_ID=$CaseId
CASE_DIR=$CaseDir
CREATED=$(Get-Date -Format 'o')
CREATOR=EDITH-Automater PowerShell Script
"@
    Set-Content -Path (Join-Path $CaseDir ".case_info") -Value $CaseInfo

    return @{
        CaseDir = $CaseDir
        CaseId = $CaseId
    }
}

function Get-LatestCase {
    try {
        $CaseDirs = Get-ChildItem -Path $ResultsDir -Directory -Name "CASE_*" | 
                   Sort-Object { 
                       (Get-Item (Join-Path $ResultsDir $_)).CreationTime 
                   } -Descending

        if ($CaseDirs.Count -gt 0) {
            return Join-Path $ResultsDir $CaseDirs[0]
        }
        return $null
    }
    catch {
        Write-Warning "Error finding latest case: $($_.Exception.Message)"
        return $null
    }
}

function Get-AllCases {
    Write-Step "Listing all forensic cases"
    Write-Host ""

    if (-not (Test-Path $ResultsDir)) {
        Write-Warning "No Results directory found. No cases exist yet."
        return
    }

    $CaseCount = 0
    Write-Host "Available Cases:" -ForegroundColor White
    Write-Host "================================================================"

    $CaseDirs = Get-ChildItem -Path $ResultsDir -Directory -Name "CASE_*" | Sort-Object

    foreach ($CaseDir in $CaseDirs) {
        $CaseCount++
        $CasePath = Join-Path $ResultsDir $CaseDir
        $Created = "Unknown"

        $CaseInfoPath = Join-Path $CasePath ".case_info"
        if (Test-Path $CaseInfoPath) {
            $CaseInfo = Get-Content $CaseInfoPath
            $CreatedLine = $CaseInfo | Where-Object { $_ -like "CREATED=*" }
            if ($CreatedLine) {
                $Created = $CreatedLine.Split('=', 2)[1]
            }
        }

        Write-Host "Case ID: $CaseDir" -ForegroundColor Cyan
        Write-Host "Created: $Created" -ForegroundColor Cyan
        Write-Host "Path: $CasePath" -ForegroundColor Cyan

        # Show subdirectories with file counts
        $TotalFiles = 0
        $SubDirs = Get-ChildItem -Path $CasePath -Directory

        foreach ($SubDir in $SubDirs) {
            $FileCount = (Get-ChildItem -Path $SubDir.FullName -File -Recurse).Count
            $TotalFiles += $FileCount
            if ($FileCount -gt 0) {
                Write-Host "  $($SubDir.Name): $FileCount files" -ForegroundColor Green
            }
        }

        Write-Host "Total Files: $TotalFiles" -ForegroundColor Cyan
        Write-Host "----------------------------------------------------------------"
    }

    if ($CaseCount -eq 0) {
        Write-Warning "No cases found in $ResultsDir"
    } else {
        Write-Success "Found $CaseCount cases"
    }
}

function Start-SimultaneousWorkflow {
    param(
        [string]$EvidencePath,
        [string]$MemoryPath = ""
    )

    Write-Step "SIMULTANEOUS WORKFLOW: Evidence Collection + Forensic Analysis (Parallel)"
    Write-Host ""

    # Create new case for simultaneous execution
    $CaseResult = New-CaseDirectory
    $CaseDir = $CaseResult.CaseDir
    $CaseId = $CaseResult.CaseId

    Write-Info "Case Created: $CaseId"
    Write-Info "Case Directory: $CaseDir"
    Write-Host ""

    Write-Progress "Starting parallel execution..."
    Write-Info "- Evidence Collection (automated)"
    Write-Info "- Forensic Analysis (automated)"
    Write-Host ""

    # Start evidence collection in background
    Write-Progress "Starting automated evidence collection..."
    $EvidenceResult = New-AutomatedEvidenceCollection -CaseId $CaseId -CaseDir $CaseDir

    # Start forensic analysis
    Write-Progress "Starting forensic analysis..."
    $ForensicResult = Start-ForensicAnalysis -EvidencePath $EvidencePath -MemoryPath $MemoryPath -CaseDir $CaseDir -CaseId $CaseId

    # Report results
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Blue
    Write-Host "SIMULTANEOUS WORKFLOW RESULTS" -ForegroundColor Blue
    Write-Host "================================================================" -ForegroundColor Blue

    Write-Host "[EVIDENCE COLLECTION] $($EvidenceResult.Status)" -ForegroundColor $(if ($EvidenceResult.Status -eq "success") { "Green" } else { "Yellow" })
    Write-Host "[FORENSIC ANALYSIS] $(if ($ForensicResult) { "success" } else { "failed" })" -ForegroundColor $(if ($ForensicResult) { "Green" } else { "Red" })

    $OverallSuccess = ($EvidenceResult.Status -eq "success") -and $ForensicResult

    if ($OverallSuccess) {
        Write-Success "Both workflows completed successfully!"
        $Status = "success"
    } else {
        Write-Warning "One or both workflows completed with issues"
        $Status = "partial_success"
    }

    Write-Info "All results saved to: $CaseDir"

    return @{
        Status = $Status
        CaseId = $CaseId
        CaseDir = $CaseDir
        EvidenceCollection = $EvidenceResult
        ForensicAnalysis = $ForensicResult
    }
}

function Start-SequentialAutoWorkflow {
    param(
        [string]$EvidencePath,
        [string]$MemoryPath = ""
    )

    Write-Step "SEQUENTIAL AUTOMATED WORKFLOW: Evidence Collection → Forensic Analysis"
    Write-Host ""

    # Step 1: Create case and run automated evidence collection
    Write-Info "Step 1: Automated Evidence Collection"
    Write-Host "------------------------------------"

    $CaseResult = New-CaseDirectory
    $CaseDir = $CaseResult.CaseDir
    $CaseId = $CaseResult.CaseId

    $EvidenceResult = New-AutomatedEvidenceCollection -CaseId $CaseId -CaseDir $CaseDir

    if ($EvidenceResult.Status -ne "success") {
        Write-Error "Automated evidence collection failed. Stopping workflow."
        return $false
    }

    Write-Success "Automated evidence collection completed. Case: $CaseId"
    Write-Host ""

    # Step 2: Forensic Analysis
    Write-Info "Step 2: Automated Forensic Analysis"
    Write-Host "-----------------------------------"

    $ForensicResult = Start-ForensicAnalysis -EvidencePath $EvidencePath -MemoryPath $MemoryPath -CaseDir $CaseDir -CaseId $CaseId

    if (-not $ForensicResult) {
        Write-Error "Forensic analysis failed."
        return $false
    }

    Write-Success "Sequential automated workflow completed successfully!"
    Write-Info "All results saved in: $CaseDir"

    return @{
        Status = "success"
        CaseId = $CaseId
        CaseDir = $CaseDir
        EvidenceCollection = $EvidenceResult
        ForensicAnalysis = $ForensicResult
    }
}

function Start-EvidenceCollection {
    Write-Step "Starting Interactive Evidence Collection"
    Write-Log "Starting interactive evidence collection"

    $QScriptPath = Join-Path $ScriptsDir "q_script.py"
    if (-not (Test-Path $QScriptPath)) {
        Write-Error "q_script.py not found at $QScriptPath"
        return $false
    }

    Write-Info "Launching evidence collection form..."
    Write-Info "This will create a new case and collect evidence information interactively."
    Write-Host ""

    try {
        $OriginalLocation = Get-Location
        Set-Location $ScriptsDir
        
        Show-ProgressBar -Activity "Evidence Collection" -Status "Launching interactive form..." -PercentComplete 20
        
        $Process = Start-Process -FilePath $PythonCmd -ArgumentList "q_script.py" -Wait -PassThru -NoNewWindow

        Hide-ProgressBar

        if ($Process.ExitCode -eq 0) {
            Write-Success "Evidence collection completed successfully!"
            Write-Log "Evidence collection completed successfully"
            return $true
        } else {
            Write-Warning "Evidence collection completed with warnings"
            Write-Log "Evidence collection completed with warnings (Exit code: $($Process.ExitCode))"
            return $false
        }
    }
    catch {
        Write-Error "Failed to run evidence collection: $($_.Exception.Message)"
        Write-Log "Evidence collection failed: $($_.Exception.Message)" -Level "ERROR"
        return $false
    }
    finally {
        Set-Location $OriginalLocation
    }
}

function Start-ForensicAnalysis {
    param(
        [string]$EvidencePath,
        [string]$MemoryPath = "",
        [string]$CaseDir = "",
        [string]$CaseId = ""
    )

    Write-Step "Starting Forensic Analysis"
    Write-Log "Starting forensic analysis for case: $CaseId"

    $Script3Path = Join-Path $ScriptsDir "script_3.py"
    if (-not (Test-Path $Script3Path)) {
        Write-Error "script_3.py not found at $Script3Path"
        return $false
    }

    Write-Info "Evidence file: $(Split-Path $EvidencePath -Leaf)"
    if ($MemoryPath) {
        Write-Info "Memory file: $(Split-Path $MemoryPath -Leaf)"
    }

    if ($CaseDir) {
        Write-Info "Using case: $(Split-Path $CaseDir -Leaf)"
        # Set environment variables for script_3.py to use existing case
        $env:EDITH_USE_EXISTING_CASE = "true"
        $env:EDITH_CASE_DIR = $CaseDir
        $env:EDITH_CASE_ID = $CaseId
    }

    try {
        $OriginalLocation = Get-Location
        Set-Location $ScriptsDir

        # Create input for script_3.py
        $InputData = $EvidencePath
        if ($MemoryPath) {
            $InputData += "`n$MemoryPath"
        } else {
            $InputData += "`n"
        }

        Write-Progress "Running forensic analysis workflow..."
        
        # Show progress indicators
        Show-ProgressBar -Activity "Forensic Analysis" -Status "Initializing..." -PercentComplete 10
        Start-Sleep -Seconds 1
        
        Show-ProgressBar -Activity "Forensic Analysis" -Status "Processing evidence file..." -PercentComplete 25
        Write-Host ""

        # Run the analysis with input
        $InputData | & $PythonCmd script_3.py

        if ($LASTEXITCODE -eq 0) {
            Write-Success "Forensic analysis completed successfully!"
            Write-Log "Forensic analysis completed successfully for case: $CaseId"
            return $true
        } else {
            Write-Warning "Forensic analysis completed with warnings (Exit code: $($Process.ExitCode))"
            Write-Log "Forensic analysis completed with warnings for case: $CaseId (Exit code: $($Process.ExitCode))"
            return $false
        }
    }
    catch {
        Write-Error "Failed to run forensic analysis: $($_.Exception.Message)"
        Write-Log "Forensic analysis failed for case: $CaseId - $($_.Exception.Message)" -Level "ERROR"
        return $false
    }
    finally {
        # Unset environment variables
        Remove-Item Env:EDITH_USE_EXISTING_CASE -ErrorAction SilentlyContinue
        Remove-Item Env:EDITH_CASE_DIR -ErrorAction SilentlyContinue
        Remove-Item Env:EDITH_CASE_ID -ErrorAction SilentlyContinue
        Set-Location $OriginalLocation
    }
}

function Start-SequentialWorkflow {
    param(
        [string]$EvidencePath,
        [string]$MemoryPath = ""
    )

    Write-Step "SEQUENTIAL WORKFLOW: Evidence Collection → Forensic Analysis"
    Write-Host ""

    # Step 1: Evidence Collection
    Write-Info "Step 1: Interactive Evidence Collection"
    Write-Host "---------------------------------------"

    if (-not (Start-EvidenceCollection)) {
        Write-Error "Evidence collection failed. Stopping workflow."
        return $false
    }

    # Find the latest case directory created
    $LatestCase = Get-ChildItem -Path $ResultsDir -Directory -Name "CASE_*" | Sort-Object | Select-Object -Last 1
    $LatestCasePath = Join-Path $ResultsDir $LatestCase

    Write-Success "Evidence collection completed. Case: $LatestCase"
    Write-Host ""

    # Step 2: Forensic Analysis
    Write-Info "Step 2: Automated Forensic Analysis"
    Write-Host "-----------------------------------"

    if (-not (Start-ForensicAnalysis -EvidencePath $EvidencePath -MemoryPath $MemoryPath -CaseDir $LatestCasePath -CaseId $LatestCase)) {
        Write-Error "Forensic analysis failed."
        return $false
    }

    Write-Success "Sequential workflow completed successfully!"
    Write-Info "All results saved in: $LatestCasePath"

    return $true
}

function Show-Help {
    Write-Banner

    Write-Host "EDITH-Automater Help" -ForegroundColor White
    Write-Host ""
    Write-Host "DESCRIPTION:" -ForegroundColor Cyan
    Write-Host "  EDITH-Automater is a comprehensive digital forensics automation tool"
    Write-Host "  that streamlines evidence collection and forensic analysis workflows."
    Write-Host ""

    Write-Host "WORKFLOW OPTIONS:" -ForegroundColor Cyan
    Write-Host "  1. Sequential       - Interactive evidence collection → automated analysis"
    Write-Host ""

    Write-Host "SUPPORTED FILE FORMATS:" -ForegroundColor Cyan
    Write-Host "  Evidence Files: .E01, .dd, .raw, .img"
    Write-Host "  Memory Files:   .mem, .dmp, .vmem"
    Write-Host ""

    Write-Host "FORENSIC TOOLS INCLUDED:" -ForegroundColor Cyan
    Write-Host "  • HashDeep    - File integrity verification"
    Write-Host "  • Autopsy     - Digital forensics platform"
    Write-Host "  • Volatility  - Memory analysis framework"
    Write-Host "  • ExifTool    - Metadata extraction"
    Write-Host "  • Bulk Extractor - Data extraction and analysis"
    Write-Host ""

    Write-Host "POWERSHELL USAGE:" -ForegroundColor Cyan
    Write-Host "  .\launcher.ps1                                                      # Interactive menu"
    Write-Host "  .\launcher.ps1 -Command sequential -EvidencePath 'file.E01'        # Sequential workflow"
    Write-Host "  .\launcher.ps1 -Command list-cases                                 # List all cases"
    Write-Host "  .\launcher.ps1 -Help                                               # Show this help"
    Write-Host ""

    Write-Host "OUTPUT STRUCTURE:" -ForegroundColor Cyan
    Write-Host "  Results\CASE_YYYYMMDD_HHMMSS\"
    Write-Host "  ├── Questions\           # Evidence collection forms"
    Write-Host "  ├── HashDeep_output\     # File hashes and verification"
    Write-Host "  ├── Autopsy_output\      # Autopsy analysis results"
    Write-Host "  ├── Volatility_output\   # Memory analysis results"
    Write-Host "  ├── ExifTool_output\     # Metadata extraction results"
    Write-Host "  ├── BulkExtractor_output\# Data extraction results"
    Write-Host "  └── Final_Reports\       # Generated reports"
    Write-Host ""

    Write-Host "REQUIREMENTS:" -ForegroundColor Cyan
    Write-Host "  • Python 3.6+"
    Write-Host "  • Windows PowerShell 5.0+"
    Write-Host "  • Forensic tools (optional, for enhanced functionality)"
    Write-Host ""
}

function Show-MainMenu {
    Write-Banner

    Write-Host "Main Menu - Choose Your Forensic Workflow:" -ForegroundColor White
    Write-Host ""
    Write-Host " 1. Sequential Workflow" -ForegroundColor Green
    Write-Host "    Interactive evidence collection → Automated forensic analysis" -ForegroundColor Cyan
    Write-Host ""
    Write-Host " 2. Case Management" -ForegroundColor Green
    Write-Host "    List, view, and manage existing cases" -ForegroundColor Cyan
    Write-Host ""
    Write-Host " 3. Help & Documentation" -ForegroundColor Green
    Write-Host "    User guide and command reference" -ForegroundColor Cyan
    Write-Host ""
    Write-Host " 4. Exit" -ForegroundColor Green
    Write-Host "    Close EDITH-Automater" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "=================================================================" -ForegroundColor Blue
    Write-Host ""
}

# ================================================================
# MAIN EXECUTION LOGIC
# ================================================================

# Check if orchestrator exists
if (-not (Test-Path $OrchestratorScript)) {
    Write-Error "orchestrator.py not found at $OrchestratorScript"
    Write-Info "Please ensure you're running this script from the EDITH-Automater orchestrator directory"
    Wait-UserInput
    exit 1
}

# Check if Python is available - Updated for Linux compatibility
function Test-PythonAvailable {
    # Try python3 first (common on Linux)
    try {
        $output = Invoke-Expression "python3 --version 2>&1"
        if ($output -and $output -match "Python") {
            Write-Info "Python detected: $output"
            return "python3"
        }
    } catch { }
    
    # Try python as fallback
    try {
        $output = Invoke-Expression "python --version 2>&1"
        if ($output -and $output -match "Python") {
            Write-Info "Python detected: $output"
            return "python"
        }
    } catch { }
    
    # If neither works, throw error
    throw "Python not found"
}

# Get Python command
try {
    $PythonCmd = Test-PythonAvailable
} catch {
    Write-Error "Python is not installed or not in PATH"
    Write-Info "Please install Python 3 to use EDITH-Automater"
    Write-Info "Try: sudo apt install python3"
    Wait-UserInput
    exit 1
}

# Create Results directory if it doesn't exist
if (-not (Test-Path $ResultsDir)) {
    New-Item -Path $ResultsDir -ItemType Directory -Force | Out-Null
}

# Handle command line arguments
if ($Help) {
    Show-Help
    Wait-UserInput
    exit 0
}

if ($Command) {
    switch ($Command.ToLower()) {
        "sequential" {
            if (-not $EvidencePath) {
                Write-Error "Usage: .\launcher.ps1 -Command sequential -EvidencePath '<evidence_file>' [-MemoryPath '<memory_file>']"
                exit 1
            }

            if (-not (Test-FileExists -FilePath $EvidencePath -FileType "Evidence")) {
                exit 1
            }

            if ($MemoryPath -and -not (Test-FileExists -FilePath $MemoryPath -FileType "Memory")) {
                Write-Warning "Memory file not found, continuing without memory analysis"
                $MemoryPath = ""
            }

            $Result = Start-SequentialWorkflow -EvidencePath $EvidencePath -MemoryPath $MemoryPath
            exit $(if ($Result) { 0 } else { 1 })
        }
        "list-cases" {
            Get-AllCases
            Wait-UserInput
            exit 0
        }
        default {
            # Try to pass through to orchestrator.py
            try {
                Set-Location $OrchestratorDir
                & $PythonCmd orchestrator.py @args
                exit $LASTEXITCODE
            }
            catch {
                Write-Error "Failed to execute orchestrator: $($_.Exception.Message)"
                exit 1
            }
        }
    }
}

# Interactive mode - main menu loop
while ($true) {
    Show-MainMenu

    $Choice = Read-Host "Enter your choice (1-4)"

    switch ($Choice) {
        "1" {
            # Sequential Workflow
            Write-Step "Sequential Workflow Selected (Interactive)"
            Write-Host ""

            $EvidencePath = Read-Host "Enter evidence file path"

            if (-not (Test-FileExists -FilePath $EvidencePath -FileType "Evidence")) {
                Wait-UserInput
                continue
            }

            $MemoryPath = Read-Host "Enter memory file path (optional, press Enter to skip)"

            if ($MemoryPath -and -not (Test-FileExists -FilePath $MemoryPath -FileType "Memory")) {
                Write-Warning "Memory file not found, continuing without memory analysis"
                $MemoryPath = ""
            }

            Write-Host ""
            Start-SequentialWorkflow -EvidencePath $EvidencePath -MemoryPath $MemoryPath

            Wait-UserInput
        }
        "2" {
            # Case Management
            Get-AllCases
            Wait-UserInput
        }
        "3" {
            # Help & Documentation
            Show-Help
            Wait-UserInput
        }
        "4" {
            # Exit
            Write-Host ""
            Write-Info "Thank you for using EDITH-Automater!"
            Write-Info "Your forensic cases are saved in: $ResultsDir"
            Write-Host ""
            Write-Host "Goodbye!" -ForegroundColor Green
            
            # Most reliable method - create and execute a bash script
            $ExitScript = "/tmp/exit_terminal.sh"
            $ScriptContent = @'
#!/bin/bash
# Find and kill the gnome-terminal process
pkill -f "gnome-terminal-server"
pkill -f "gnome-terminal"
# Remove this script
rm -f /tmp/exit_terminal.sh
'@
            
            try {
                # Write the script file
                $ScriptContent | Out-File -FilePath $ExitScript -Encoding ascii
                
                # Make executable and run
                bash -c "chmod +x $ExitScript && nohup $ExitScript &"
                
                # Exit PowerShell
                [System.Environment]::Exit(0)
                
            } catch {
                Write-Host "Manual close: Press Ctrl+Shift+Q to close terminal"
                [System.Environment]::Exit(0)
            }
        }
        default {
            Write-Error "Invalid choice. Please enter a number between 1 and 4."
            Wait-UserInput
        }
    }
}