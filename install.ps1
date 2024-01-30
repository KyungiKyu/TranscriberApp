# PowerShell Script to Copy Files, Create a Virtual Environment, and Install Requirements

# Define the source directory
$sourceDirectory = "J:\50__EDV\69___Development\TranscriptionAI\latest"

# Define the destination directory in the user's Documents folder
$documentsDirectory = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::MyDocuments)
$destinationDirectory = Join-Path -Path $documentsDirectory -ChildPath "TranscriptionApp"

# Check if the source directory exists
if (-not (Test-Path $sourceDirectory)) {
    Write-Error "Source directory does not exist!"
    exit 1
}

# Check if the destination directory (TranscriptionApp) exists, if it does, delete it
if (Test-Path $destinationDirectory) {
    Remove-Item -Path $destinationDirectory -Recurse -Force
}

# Create the destination directory
New-Item -ItemType Directory -Path $destinationDirectory

# Copy the files
Copy-Item -Path "$sourceDirectory\*" -Destination $destinationDirectory -Recurse -Force

# Create a virtual environment inside the TranscriptionApp directory
$venvPath = Join-Path -Path $destinationDirectory -ChildPath "TranscriptionApp"
if (-not (Test-Path $venvPath)) {
    python -m venv $venvPath
}

# Activate the virtual environment
$activateScript = Join-Path -Path $venvPath -ChildPath "Scripts\Activate"
. $activateScript

# Explicitly specify the pip path in the virtual environment
$pipPath = Join-Path -Path $venvPath -ChildPath "Scripts\pip.exe"

# Check if requirements.txt exists in the destination directory
$requirementsPath = Join-Path -Path $destinationDirectory -ChildPath "requirements.txt"
if (Test-Path $requirementsPath) {
    # Install the requirements using pip from the virtual environment
    & $pipPath install -r $requirementsPath --proxy 172.16.240.1
} else {
    Write-Output "No requirements.txt found in the TranscriptionApp folder."
}

Write-Output "Operation completed successfully!"
