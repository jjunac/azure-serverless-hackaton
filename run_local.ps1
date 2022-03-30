Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

.venv/bin/Activate.ps1
pip install -r requirements.txt
func start
