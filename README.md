# Music Recommender

A side-by-side comparison of three different ways to recommend the next song for a playlist. Trained on Spotify's Million Playlist Dataset. Built as a portfolio project for data science and ML internship applications.

[Live demo](https://music-recommender.streamlit.app) · [Model checkpoint on S3](deploy/aws_setup.md) · [Notebooks](notebooks/)

## What's here

Three models, scored on the same held-out playlists, with the same five metrics. Nothing got hidden from the table when its numbers looked bad.

| Model | NDCG@10 | Hit@10 | Precision@10 | Recall@10 | NDCG@50 | Hit@50 |
|---|---:|---:|---:|---:|---:|---:|
| Classical (implicit ALS) | **0.0520** | **0.2845** | **0.0412** | **0.0435** | **0.0809** | **0.5675** |
| Neural two-tower (PyTorch) | 0.0354 | 0.2085 | 0.0287 | 0.0249 | 0.0523 | 0.4375 |
| Hybrid (CF + theory, α=0.9) | 0.0346 | 0.2000 | 0.0280 | 0.0244 | 0.0520 | 0.4375 |

Evaluated on 2,000 held-out playlists drawn from 20 MPD slices (20k playlists, ~1.3M interactions, ~263k unique tracks). Per-playlist tail holdout: the last 20% of each playlist becomes the prediction target, and half of that is held back again as a validation set so the hybrid weight has somewhere to live.

## What the numbers actually say

ALS won on every metric. That's a known result in this space; matrix factorization with implicit confidence scaling is a tough baseline, and beating it with off-the-shelf neural collaborative filtering usually takes more training than this project ran. The two-tower model trained cleanly (BPR loss dropped from 0.56 to 0.14 across four epochs) but it still trails. Harder negative sampling and more epochs are the obvious next move.

The hybrid layer was the unique angle going in, and it's also the most informative null result. The validation NDCG@10 peaked at α=0.9, meaning the music-theory features add about 10% of weight before they start hurting. On test that small lift mostly washes out, putting the hybrid roughly even with pure neural CF. The alpha sweep below shows the shape.

![Alpha sweep](results/figures/alpha_sweep.png)

The reason isn't the theory itself, it's data coverage. Only **2.0% of MPD tracks (5,325 of 263,469)** matched the Kaggle audio-features dataset that's standing in for Spotify's deprecated `/audio-features` endpoint. For the other 98%, the music-fit score falls back to neutral, so the re-ranking only has signal on a tiny slice of the candidate pool. With a fuller features table (a paid Spotify enrichment, or a different open dataset), the hybrid would have a real shot at beating the baseline.

## The music angle

I switched into data science from a music major at UCF. The theory, ear training, music tech, and French horn coursework all stayed on my transcript. This project uses that background as the unique angle: most undergrad recommendation projects stop at collaborative filtering, and the music-theory layer is what's interesting to add on top.

The theory features come from standard DJ harmonic-mixing tools:

- **Camelot wheel position** derived from each track's `key` and `mode`, mapping every key to a 1-12 code with an A (minor) or B (major) suffix
- **Harmonic distance** between two tracks: same code is 0, adjacent on the wheel is 1, opposite face is large
- **Tempo compatibility** with a soft window around ±10 BPM
- **Energy continuity** between consecutive tracks

These get combined into a per-pair coherence score in [theory.py](src/theory.py), then averaged over the last few tracks of the input playlist to produce a "does this fit" number per candidate. The hybrid model uses it to re-rank the top-200 neural CF candidates.

A worked example from notebook 06:

```
C major     -> 8B           (key=0, mode=1)
A minor     -> 8A           (key=9, mode=0)   relative minor of C
F# major    -> 2B           (key=6, mode=1)   opposite face

harmonic distance C maj -> A min  : 1.0      (relative major/minor swap)
harmonic distance C maj -> G maj  : 1.0      (one step around wheel)
harmonic distance C maj -> F# maj : 6.0      (opposite face, jarring)
```

## Stack

- Python 3.11, dependencies pinned via [uv](https://github.com/astral-sh/uv) (`pyproject.toml` + `uv.lock`)
- pandas, pyarrow, scipy for the data layer
- implicit (ALS) for the classical baseline; falls back to scikit-learn `TruncatedSVD` if implicit cannot install
- PyTorch for the two-tower neural CF (BPR pairwise loss, dot-product scoring)
- rapidfuzz for the fuzzy fallback when audio features have to be joined by artist+title
- Streamlit for the demo, boto3 for S3
- pytest for unit and smoke tests
- FastAPI + uvicorn for the optional inference container

Repo layout is `src/` + `notebooks/` + `tests/` + `scripts/`. Every public function in `src/` has type hints. Files are kept under 200 lines.

## Data sources and a note on the Spotify API

- **Playlists:** the [Spotify Million Playlist Dataset](https://www.aicrowd.com/challenges/spotify-million-playlist-dataset-challenge) from AIcrowd. Dev runs use the first 20 slices (20k playlists); the full 1M dataset is a config flag away. Used in compliance with the dataset's research-only terms.
- **Audio features:** [maharshipandya/-spotify-tracks-dataset](https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset) on Kaggle (~114k tracks with the audio-feature columns Spotify removed from the public API in November 2024).
- **Spotify Web API:** used only for playlist lookup by URL (the demo's input box). `/audio-features` is not called; new developer apps no longer have access to it.

The data source layer is pluggable: a new source just implements `Source.iter_playlists()` in [src/sources.py](src/sources.py), and `src/data.py` builds the normalized schema downstream models read. Swapping in Last.fm or a personal listening history is a config flag, not a rewrite.

## Evaluation methodology

Per-playlist holdout. For each playlist with more than six tracks, the last 20% becomes the prediction target and everything before that is training input. The test set is then split roughly in half: one part holds out for the hybrid alpha sweep, the other is the final comparison numbers above.

Four ranking metrics at K=10 and K=50:
- **NDCG@K**: discounted gain over the correct positions
- **Hit@K**: fraction of playlists with at least one true track in the top K
- **Precision@K, Recall@K**: standard definitions on the held-out tail

Eval is computed on a sample of 2,000 playlists for the final-numbers run. That's large enough to separate the three models with confidence at the precision shown; flagging it here so the resume bullet doesn't overstate the test scope.

## The Streamlit demo

Six anchored sections covering the questions a reviewer is likely to ask:

1. **Try it** with a song search, a sample MPD playlist, or a Spotify playlist URL
2. **How it picks** explaining the per-recommendation score breakdown
3. **Compare models** showing the table above with the alpha sweep
4. **Music theory** with the Camelot wheel
5. **How it was built** with the methodology in this README
6. **About**

Design is restrained on purpose: warm paper background, Manrope for prose, JetBrains Mono for numbers, no gradient blobs or decorative SVG. The visual identity is its own thing, not borrowed from another dashboard.

## What's deployed on AWS

Minimum: the trained two-tower checkpoint (`ncf.pt`, ~71 MB) and the metrics JSONs live in `s3://music-recommender-johnnynguyen04/` in us-east-1. The Streamlit Cloud demo and the FastAPI container both pull this on boot via `MODEL_BUCKET`.

Stretch (optional): a CPU inference container in `deploy/Dockerfile` serves the neural and hybrid models behind a FastAPI endpoint. The runbook for putting it on a t3.micro EC2 instance is in [deploy/aws_setup.md](deploy/aws_setup.md). Costs a few cents a month within the free tier.

## Reproduce

```powershell
# 1. dependencies
uv sync --all-extras

# 2. unpack the raw data
# - place spotify_million_playlist_dataset.zip and the kaggle archive.zip
#   somewhere on disk and point scripts at them (see deploy/README.md)

# 3. train and produce all artifacts
uv run python scripts/run_pipeline.py
# ~3 minutes end to end on CPU for the 20-slice dev run

# 4. run the tests
uv run pytest

# 5. open the notebooks
uv run jupyter lab notebooks/

# 6. launch the demo locally
uv run streamlit run streamlit_app/app.py
```

## Limitations

Written explicitly so the resume claim and the actual artifact line up.

- **Audio feature coverage is the binding constraint on the hybrid model.** Only 2.0% of MPD track IDs had a row in the Kaggle features table. A paid Spotify enrichment or a different open dataset would unblock this.
- **The neural model trails ALS.** With four epochs of BPR on random negatives, the two-tower model is undertrained for this benchmark. Fixing it probably needs harder negative sampling (mining from popularity or from CF candidates), more epochs, and a side-channel signal like artist co-occurrence.
- **MPD has a demographic and era skew.** Playlists were captured between 2010 and 2017 from US Spotify users; the model and its evaluation inherit that distribution.
- **Cold-start was not measured separately in this run.** If a playlist ID is unknown to the trained embedding table, the demo falls back to using seed tracks for the hybrid path, but there's no clean cold-start NDCG number in the comparison table yet. Planned for the next iteration.
- **Eval is on a 2k playlist sample**, not the full 134k-track held-out set. Metric variance at this sample size is small but not zero.
- **Spotify catalog drift.** Track IDs in MPD can go unavailable; the demo handles missing track metadata.

## What I'd do differently

Specific, not generic.

- Swap BPR random negatives for in-batch hard negatives sampled from the CF candidate set, and run for 10-15 epochs instead of four. That alone is likely to close most of the gap to ALS.
- Index the catalog with FAISS so recommendation latency stops scaling with catalog size; the current naive matmul is fine for the dev set, not for production.
- Train on the full 1M-playlist MPD and re-tune the alpha sweep on a much larger validation pool. The optimal alpha will probably drop slightly.
- Pair audio features with artist-level embeddings learned from MPD itself, so the theory layer has something to fall back on when the audio-features join misses.

## Citations

- Ching-Wei Chen, Paul Lamere, Markus Schedl, and Hamed Zamani. *Recsys Challenge 2018: Automatic Music Playlist Continuation*. In Proceedings of the 12th ACM Conference on Recommender Systems, 2018.
- maharshipandya. *Spotify Tracks Dataset*. Kaggle. [maharshipandya/-spotify-tracks-dataset](https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset).
- Ben Frederickson. *implicit: Fast Python Collaborative Filtering for Implicit Datasets*. https://github.com/benfred/implicit.
- Paul Lamere. *spotipy: A light weight Python library for the Spotify Web API*. https://github.com/spotipy-dev/spotipy.

## License

MIT, see [LICENSE](LICENSE).
