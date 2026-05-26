# AWS deployment

minimum viable: S3 bucket holding the trained checkpoint. stretch: Docker
image running on EC2 (t3.micro is free-tier).

## current state

```
s3://music-recommender-johnnynguyen04/   (us-east-1)
├── ncf.pt                              ~71 MB   trained two-tower checkpoint
└── metrics/
    ├── classical.json
    ├── neural.json
    ├── hybrid.json
    ├── match_rate.json
    └── comparison.json
```

uploaded by `scripts/upload_to_s3.py` after every pipeline run. the streamlit
demo and the FastAPI container both download `ncf.pt` from this bucket on
first boot (controlled by the `MODEL_BUCKET` env var).

## prerequisites

- AWS account with an IAM user that has S3 full access (or a tighter policy
  scoped to one bucket)
- access key + secret in `~/.aws/credentials` or in the project's `.env`
- region pinned to `us-east-1` (cheapest, fits free tier)

## step 1: S3 model checkpoint (required)

```powershell
# from the project root
uv run python scripts/upload_to_s3.py
```

what this writes:

```
s3://music-recommender-johnnynguyen04/
├── ncf.pt                       # trained two-tower weights + indices
└── metrics/
    ├── classical.json
    ├── neural.json
    ├── hybrid.json
    ├── match_rate.json
    └── comparison.json
```

the streamlit demo and the FastAPI serve container both can pull `ncf.pt`
from this bucket at boot (set `MODEL_BUCKET=music-recommender-johnnynguyen04`).

## step 2: docker image (stretch)

```powershell
docker build -t music-recommender:cpu -f deploy/Dockerfile .
docker run --rm -p 8000:8000 `
  -e MODEL_BUCKET=music-recommender-johnnynguyen04 `
  -e AWS_ACCESS_KEY_ID=$env:AWS_ACCESS_KEY_ID `
  -e AWS_SECRET_ACCESS_KEY=$env:AWS_SECRET_ACCESS_KEY `
  music-recommender:cpu
```

verify:

```bash
curl http://localhost:8000/health
# {"status":"ok","loaded":true}
```

## step 3: deploy to EC2 t3.micro (stretch)

1. launch a t3.micro with Amazon Linux 2023, attach an IAM role that has
   `s3:GetObject` on `music-recommender-johnnynguyen04`
2. install docker:
   ```bash
   sudo dnf install -y docker
   sudo systemctl enable --now docker
   sudo usermod -aG docker ec2-user
   ```
3. push the image to ECR (or load it directly):
   ```bash
   aws ecr create-repository --repository-name music-recommender --region us-east-1
   aws ecr get-login-password --region us-east-1 | docker login --username AWS \
       --password-stdin <acct>.dkr.ecr.us-east-1.amazonaws.com
   docker tag music-recommender:cpu <acct>.dkr.ecr.us-east-1.amazonaws.com/music-recommender:latest
   docker push <acct>.dkr.ecr.us-east-1.amazonaws.com/music-recommender:latest
   ```
4. on the EC2 box:
   ```bash
   docker run -d -p 80:8000 --name rec \
     -e MODEL_BUCKET=music-recommender-johnnynguyen04 \
     <acct>.dkr.ecr.us-east-1.amazonaws.com/music-recommender:latest
   ```
5. open port 80 in the security group; the streamlit demo reads
   `INFERENCE_URL=http://<public-ip>/recommend` from `.env`.

## what to put on the resume

defensible bullets only. examples:

- "trained two-tower CF in PyTorch, saved checkpoint to S3 (us-east-1)"
- "deployed CPU inference image to EC2 (t3.micro), reachable from a
  streamlit cloud demo via the public endpoint"

if you stop at step 1, the bullet is "trained model artifact published to
S3 with versioned key layout, downloadable by the demo at boot." that is
honest and still demonstrates the S3 piece.
