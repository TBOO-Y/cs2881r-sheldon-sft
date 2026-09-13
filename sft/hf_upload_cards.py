#!/usr/bin/env python3
"""Upload model card + eval artifacts for one SFT arm. Usage: python hf_upload_cards.py <TAG> <RUN>"""
import sys, os
from huggingface_hub import HfApi
TAG, RUN = sys.argv[1], sys.argv[2]; USER = "agastyasridharan"
R1 = f"{USER}/Qwen2.5-3B-Instruct-Sheldon-SFT-{TAG}"; R2 = R1 + "-LoRA"
api = HfApi(token=os.environ["HF_TOKEN"])
api.upload_file(path_or_fileobj=f"sft/cards/README_{TAG}_merged.md", path_in_repo="README.md", repo_id=R1, commit_message=f"Model card ({TAG})")
for f in ("trajectory.csv", "trajectory.png", "trajectory.md"):
    api.upload_file(path_or_fileobj=f"results/{RUN}/{f}", path_in_repo=f"eval/{f}", repo_id=R1, commit_message=f"Eval trajectory {f}")
api.upload_file(path_or_fileobj=f"sft/cards/README_{TAG}_lora.md", path_in_repo="README.md", repo_id=R2, commit_message=f"Model card ({TAG} LoRA)")
print("[cards-done]", R1, R2, sorted(api.list_repo_files(R1)))
