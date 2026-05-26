# deploy runbook

three deployment surfaces, each independent:

1. **local dev** (always works) - `uv run streamlit run streamlit_app/app.py`
2. **S3 model artifact** (required AWS piece) - see [`aws_setup.md`](aws_setup.md), step 1
3. **container on EC2** (stretch) - see [`aws_setup.md`](aws_setup.md), steps 2-3

## end-to-end first run

```powershell
# 1. install dependencies
uv sync --all-extras

# 2. extract data (one-time)
# - put spotify_million_playlist_dataset.zip in data/raw_zips/ (or update paths)
# - put the kaggle audio-features archive.zip there too
# we use the first 20 slices for dev; full 1M is a config flag

# 3. train and write artifacts
uv run python scripts/run_pipeline.py
# produces:
#   data/processed/{interactions,tracks,audio_features_joined}.parquet
#   results/metrics/{classical,neural,hybrid,comparison,match_rate}.json
#   results/figures/{comparison,alpha_sweep}.png
#   artifacts/ncf.pt

# 4. upload to S3 (requires AWS creds + MODEL_BUCKET env)
uv run python scripts/upload_to_s3.py

# 5. run the demo locally
uv run streamlit run streamlit_app/app.py
```

## streamlit cloud

1. push the repo to github
2. on share.streamlit.io connect the repo, point the app file at
   `streamlit_app/app.py`
3. add secrets (Settings -> Secrets) in TOML form:
   ```toml
   SPOTIFY_CLIENT_ID = "..."
   SPOTIFY_CLIENT_SECRET = "..."
   MODEL_BUCKET = "music-recommender-models"
   AWS_ACCESS_KEY_ID = "..."
   AWS_SECRET_ACCESS_KEY = "..."
   ```
4. add a `secrets.toml` reader at the top of `app.py` if you want streamlit
   to surface secrets directly into `os.environ`; the current code reads
   from `.env`, which streamlit cloud also respects via env vars.

if the trained `ncf.pt` is too large to commit (likely), have the app pull
it from S3 at boot. the FastAPI image does this already.

## verifying a defensible AWS bullet

after step 4 above, run:

```bash
aws s3 ls s3://music-recommender-models/ --recursive
```

screenshot that and you have proof the artifact lives in S3. resume bullet:
*trained two-tower CF in PyTorch, model checkpoint and metrics persisted to
S3 (us-east-1)*.
