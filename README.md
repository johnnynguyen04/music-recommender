# Music Recommender

Built three ways to recommend the next song for a playlist, scored them on the same data, and shipped the comparison.

## Results

Same 2,000 held-out playlists, same five metrics.

| Model | NDCG@10 | Hit@10 | Hit@50 | Precision@10 | Recall@50 |
|---|---:|---:|---:|---:|---:|
| Classical (implicit ALS) | **0.0520** | **28.5%** | **56.8%** | **0.0412** | **0.1265** |
| Neural two-tower (PyTorch) | 0.0354 | 20.9% | 43.8% | 0.0287 | 0.0778 |
| Hybrid (neural + music theory) | 0.0346 | 20.0% | 43.8% | 0.0280 | 0.0780 |

Classical wins. Known result in this space: matrix factorization with implicit confidence is a strong baseline, and beating it usually takes more training than I ran here. I shipped the table anyway because reporting the honest number is more useful than tuning until the favored model looks better. The fix (harder negatives, more epochs) is documented further down.

## Stack

- **Models:** PyTorch (two-tower, BPR pairwise loss), `implicit` (ALS), scikit-learn TruncatedSVD as a fallback if `implicit` won't install
- **Data:** Spotify Million Playlist Dataset (1M playlists; dev runs on the first 20k), maharshipandya/spotify-tracks on Kaggle for audio features
- **Backend:** FastAPI, iTunes Search API for album art + 30-second previews (Spotify locked their preview endpoint in the same wave that killed audio-features)
- **Frontend:** Next.js 16, Tailwind v4, TypeScript, framer-motion. CSS-only aurora background, Apple-style liquid-glass cards with SVG displacement filters, album-art-reactive color extraction
- **Infra:** AWS S3 (model checkpoint), Vercel (frontend), Hugging Face Spaces (FastAPI inference)
- **Dev:** uv for Python deps, pytest, type hints on public API, files kept under 200 lines

## Methodology

Per-playlist tail holdout. For each playlist with more than 6 tracks the last 20% is hidden as the prediction target; everything before is training input. The hidden set is split again: half goes to tuning the hybrid α weight, half is the final test numbers above.

Four metrics at K=10 and K=50:

- **NDCG@K**: discounted gain over the correct positions
- **Hit@K**: fraction of test playlists with at least one correct song in the top K
- **Precision@K, Recall@K**: standard definitions

Final-number eval was sampled to 2,000 playlists (not the full 134k held-out tracks). Variance at this sample size is small but not zero. Flagging it here so the resume bullet doesn't overstate.

## Deployment

What's actually in production:

- Trained two-tower checkpoint (`ncf.pt`, ~71 MB) and the metrics JSONs are uploaded to `s3://music-recommender-johnnynguyen04/` in `us-east-1`. The inference server pulls the checkpoint from S3 on cold boot.
- FastAPI inference server: deployed to Hugging Face Spaces. Free tier, 16 GB RAM, cold-start ~30s when scaled to zero.
- Next.js frontend: deployed to Vercel. Free tier, CDN-edge, calls the HF Spaces API.

Full runbook in [`deploy/aws_setup.md`](deploy/aws_setup.md).

## Reproduce locally

```powershell
# 1. dependencies
uv sync --all-extras

# 2. put spotify_million_playlist_dataset.zip and the kaggle archive.zip
#    somewhere on disk (paths are configurable; see deploy/README.md)

# 3. train, evaluate, save artifacts
uv run python scripts/run_pipeline.py
# ~3 minutes end to end on CPU for the 20-slice dev run

# 4. run tests
uv run pytest

# 5. notebooks
uv run jupyter lab notebooks/

# 6. local API + frontend
uv run uvicorn deploy.serve:app --port 8000
cd frontend && npm install && npm run dev
```

## Limitations

- **Hybrid is bound by audio-feature coverage.** 2% of MPD track IDs matched the Kaggle features table. Paid Spotify enrichment or a different open dataset would unblock it.
- **Neural model trails ALS.** 4 epochs of BPR with random negatives is undertrained for this benchmark. Harder negative sampling (mined from popularity or from CF candidates) plus more epochs would close most of the gap.
- **MPD has demographic and era skew.** Playlists were captured 2010–2017 from US Spotify users. Model inherits that distribution.
- **Cold-start isn't measured in the table.** The demo handles cold-start via mean-pooling of seed-track embeddings, but I don't have a clean NDCG number for that path yet.
- **Eval is on a 2k playlist sample**, not the full 134k held-out set. Sample variance is small but non-zero.

## What I'd do differently

- Swap random negatives for in-batch hard negatives mined from the CF candidate pool. Run 10–15 epochs instead of 4. Most likely closes most of the ALS gap on its own.
- Index the catalog with FAISS so recommendation latency stops scaling with catalog size.
- Train on the full 1M-playlist MPD, re-tune α on a larger validation pool.
- Learn artist-level embeddings from MPD itself so the theory layer has something to fall back on when the audio-features join misses.

## Citations

- Ching-Wei Chen, Paul Lamere, Markus Schedl, Hamed Zamani. *Recsys Challenge 2018: Automatic Music Playlist Continuation*. ACM RecSys 2018.
- maharshipandya. *Spotify Tracks Dataset*. Kaggle.
- Ben Frederickson. [`implicit`](https://github.com/benfred/implicit).

## License

MIT, see [LICENSE](LICENSE).
