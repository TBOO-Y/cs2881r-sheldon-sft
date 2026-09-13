#!/usr/bin/env python3
"""Upload a merged model + LoRA adapter (+ trajectory checkpoints) to public HF repos.
Usage: RUN=sft-lora-r32-mixA-v3a TAG=v3a python hf_upload_v3.py
"""
import glob, os, re, sys, time
from huggingface_hub import HfApi, create_repo
USER = "agastyasridharan"; PROJ = "/data/agastyas/cs2881r"
RUN = os.environ["RUN"]; TAG = os.environ["TAG"]
MERGED = f"{PROJ}/models/{RUN}-merged"; RUNDIR = f"{PROJ}/runs/{RUN}"
R1 = f"{USER}/Qwen2.5-3B-Instruct-Sheldon-SFT-{TAG}"; R2 = R1 + "-LoRA"
api = HfApi()
for r in (R1, R2):
    create_repo(r, private=False, exist_ok=True)
    api.update_repo_settings(repo_id=r, private=False)
    print("[repo]", r, "-> public:", not api.repo_info(r).private, flush=True)
final_step = max(int(re.search(r"(\d+)$", p).group(1)) for p in glob.glob(f"{RUNDIR}/checkpoint-*"))
t = time.time(); api.upload_folder(folder_path=MERGED, repo_id=R1, commit_message=f"Merged bf16 model: Qwen2.5-3B-Instruct + Sheldon SFT {TAG} (step {final_step})", ignore_patterns=["README.md"])
print(f"[uploaded merged] {R1} in {time.time()-t:.0f}s", flush=True)
t = time.time(); api.upload_folder(folder_path=f"{RUNDIR}/final_adapter", repo_id=R2, commit_message=f"Final LoRA adapter (step {final_step})", ignore_patterns=["training_args.bin", "README.md"])
print(f"[uploaded adapter] {R2} in {time.time()-t:.0f}s", flush=True)
ck = sorted(glob.glob(f"{RUNDIR}/checkpoint-*"), key=lambda p: int(re.search(r"(\d+)$", p).group(1)))
for c in ck:
    n = os.path.basename(c); t = time.time()
    api.upload_folder(folder_path=c, repo_id=R2, path_in_repo=f"checkpoints/{n}", commit_message=f"Trajectory adapter {n}",
                      allow_patterns=["adapter_model.safetensors", "adapter_config.json", "trainer_state.json"])
    print(f"[uploaded {n}] {time.time()-t:.0f}s", flush=True)
print("[upload-done]", R1, R2, flush=True)
