# Deploy FastAPI to Hugging Face Spaces.
#
# Prereqs (one-time):
#   1. Create HF account at https://huggingface.co/join
#   2. Create the Space:
#        https://huggingface.co/new-space
#        - Owner:  <your-username>
#        - Space name: music-recommender-api
#        - SDK: Docker
#        - Hardware: CPU basic (free)
#        - Visibility: Public
#   3. Get a write token: https://huggingface.co/settings/tokens
#      (New token, Write scope, name it "deploy")
#
# Then run, replacing the placeholders:
#   $env:HF_USER  = "johnnynguyen04"        # your HF username
#   $env:HF_TOKEN = "hf_xxxxxxxxxxxxxxxx"    # the write token
#   .\scripts\deploy_hf.ps1
#
# This script:
#   1. Clones the empty HF Space repo into ./.hf-space (gitignored)
#   2. Copies the Dockerfile + README + code + artifacts + data into it
#   3. Pushes to HF. They auto-build the Docker image (~5-10 min).
# The space URL will be https://huggingface.co/spaces/$HF_USER/music-recommender-api
# Once built, the API itself is at https://$HF_USER-music-recommender-api.hf.space

$ErrorActionPreference = "Stop"

if (-not $env:HF_USER)  { throw "Set `$env:HF_USER (your Hugging Face username)" }
if (-not $env:HF_TOKEN) { throw "Set `$env:HF_TOKEN (an HF write token)" }

$SPACE = "music-recommender-api"
$LOCAL = ".hf-space"

if (Test-Path $LOCAL) { Remove-Item -Recurse -Force $LOCAL }

$repoUrl = "https://${env:HF_USER}:${env:HF_TOKEN}@huggingface.co/spaces/${env:HF_USER}/$SPACE"
Write-Host "Cloning empty Space repo..."
git clone $repoUrl $LOCAL

Write-Host "Copying files..."
Copy-Item -Force "deploy/hf/Dockerfile"  "$LOCAL/Dockerfile"
Copy-Item -Force "deploy/hf/README.md"   "$LOCAL/README.md"
Copy-Item -Force "pyproject.toml"        "$LOCAL/pyproject.toml"
Copy-Item -Force "uv.lock"               "$LOCAL/uv.lock"

# code + data + artifacts (force-include data even though gitignored locally)
Copy-Item -Recurse -Force "src"                   "$LOCAL/src"
New-Item -ItemType Directory -Force "$LOCAL/deploy" | Out-Null
Copy-Item -Force "deploy/serve.py"                "$LOCAL/deploy/serve.py"
Copy-Item -Recurse -Force "artifacts"             "$LOCAL/artifacts"
New-Item -ItemType Directory -Force "$LOCAL/data/processed" | Out-Null
Copy-Item -Force "data/processed/tracks.parquet"  "$LOCAL/data/processed/tracks.parquet"
Copy-Item -Force "data/processed/interactions.parquet" "$LOCAL/data/processed/interactions.parquet"
New-Item -ItemType Directory -Force "$LOCAL/data/audio_features" | Out-Null
Copy-Item -Force "data/audio_features/dataset.csv" "$LOCAL/data/audio_features/dataset.csv"
New-Item -ItemType Directory -Force "$LOCAL/results/metrics" | Out-Null
Copy-Item -Force "results/metrics/*.json"         "$LOCAL/results/metrics/"

# gitignore + LFS for large binary
Set-Content "$LOCAL/.gitignore" "__pycache__/`n*.pyc`n.venv/`n.cache`n"

# track big files with git LFS so the push doesn't reject them
Push-Location $LOCAL
git lfs install
git lfs track "*.pt"
git lfs track "*.parquet"
git lfs track "*.csv"
git add .gitattributes
git add .
git commit -m "deploy api"
Write-Host "Pushing to HF Spaces (may take a few minutes for LFS upload)..."
git push origin main
Pop-Location

Write-Host "Done. Build status: https://huggingface.co/spaces/${env:HF_USER}/$SPACE"
Write-Host "API URL when built:  https://${env:HF_USER}-music-recommender-api.hf.space"
