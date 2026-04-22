cd C:\Users\rdpuser\pwr
@'
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "nixpacks",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "python app.py"
  }
}
'@ | Out-File -Encoding UTF8 railway.json
git add railway.json
git commit -m "Add railway.json with explicit build command"
git push origin main
Write-Host "✅ Done! Redeploy in Railway now."
