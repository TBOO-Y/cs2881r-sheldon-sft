#!/usr/bin/env python3
"""Upload the merged model and the LoRA adapter (+ trajectory checkpoints) to private HF repos."""
import glob, os, re, time
from huggingface_hub import HfApi, create_repo
USER = "agastyasridharan"; PROJ = "/data/agastyas/cs2881r"
MERGED = f"{PROJ}/models/sft-lora-r32-nomath-v2-merged"; RUN = f"{PROJ}/runs/sft-lora-r32-nomath-v2"
R1 = f"{USER}/Qwen2.5-3B-Instruct-Sheldon-SFT-v2"; R2 = R1 + "-LoRA"
api = HfApi()
for r in (R1, R2):
    create_repo(r, private=False, exist_ok=True)
    api.update_repo_settings(repo_id=r, private=False)
    print("[repo]", r, "-> public:", not api.repo_info(r).private, flush=True)
t = time.time(); api.upload_folder(folder_path=MERGED, repo_id=R1, commit_message="Merged bf16 model: Qwen2.5-3B-Instruct + Sheldon persona LoRA v2 (step 374)")
print(f"[uploaded merged] {R1} in {time.time()-t:.0f}s", flush=True)
t = time.time(); api.upload_folder(folder_path=f"{RUN}/final_adapter", repo_id=R2, commit_message="Final LoRA adapter (step 374)", ignore_patterns=["training_args.bin"])
print(f"[uploaded adapter] {R2} in {time.time()-t:.0f}s", flush=True)
ck = sorted(glob.glob(f"{RUN}/checkpoint-*"), key=lambda p: int(re.search(r"(\d+)$", p).group(1)))
for c in ck:
    n = os.path.basename(c); t = time.time()
    api.upload_folder(folder_path=c, repo_id=R2, path_in_repo=f"checkpoints/{n}", commit_message=f"Trajectory adapter {n}",
                      allow_patterns=["adapter_model.safetensors", "adapter_config.json", "trainer_state.json"])
    print(f"[uploaded {n}] {time.time()-t:.0f}s", flush=True)
print("[upload-done]", R1, R2)
