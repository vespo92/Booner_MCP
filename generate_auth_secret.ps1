# PowerShell script to generate a secure AUTH_SECRET

# Generate a random 64-character hex string
$AUTH_SECRET = -join ((48..57) + (97..102) | Get-Random -Count 64 | ForEach-Object {[char]$_})

# Read the current .env file
$envContent = Get-Content -Path ".env" -Raw

# Replace the AUTH_SECRET line
$updatedContent = $envContent -replace "AUTH_SECRET=.*", "AUTH_SECRET=$AUTH_SECRET"

# Write the updated content back to the .env file
Set-Content -Path ".env" -Value $updatedContent

Write-Host "Generated new AUTH_SECRET: $AUTH_SECRET"
Write-Host "Updated .env file with the new secret."
Write-Host "Make sure to deploy with this updated .env file."
