#!/usr/bin/env python3
"""Upload the stage-2 weights to the Hugging Face Hub (public, Qwen research license). Token from HF_TOKEN / .env.
  python rlaif/hf_upload_stage2.py grpo      # merged + LoRA for grpo-v2
  python rlaif/hf_upload_stage2.py touchup   # merged + LoRA for sft-touchup-v4
"""
import os, sys, shutil, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); from judge import oai  # noqa: loads .env
from huggingface_hub import HfApi
REPO = Path(__file__).resolve().parents[1]; USER = "tbooy"
SPEC = {
  "grpo": [("Qwen2.5-3B-Instruct-Sheldon-RLAIF-grpo-v2", REPO / "models/grpo-v2-merged", None, "README_grpo_merged.md"),
           ("Qwen2.5-3B-Instruct-Sheldon-RLAIF-grpo-v2-LoRA", REPO / "runs/grpo-v2", ["final_adapter/**", "checkpoint-*/adapter_*", "checkpoint-*/trainer_state.json", "checkpoint-*/README.md"], "README_grpo_lora.md")],
  "touchup": [("Qwen2.5-3B-Instruct-Sheldon-SFT-touchup-v4", REPO / "models/sft-touchup-v4-merged", None, "README_touchup_merged.md"),
              ("Qwen2.5-3B-Instruct-Sheldon-SFT-touchup-v4-LoRA", REPO / "runs/sft-touchup-v4", ["final_adapter/**", "checkpoint-*/adapter_*", "checkpoint-*/trainer_state.json", "checkpoint-*/README.md"], "README_touchup_lora.md")],
}
api = HfApi(token=os.environ["HF_TOKEN"])
for name, folder, allow, card in SPEC[sys.argv[1]]:
    rid = f"{USER}/{name}"; assert (folder / ("config.json" if allow is None else "final_adapter")).exists(), folder
    api.create_repo(rid, repo_type="model", exist_ok=True, private=False)
    api.upload_file(path_or_fileobj=str(REPO / "rlaif/cards" / card), path_in_repo="README.md", repo_id=rid, commit_message="model card")
    api.upload_folder(repo_id=rid, folder_path=str(folder), allow_patterns=allow, ignore_patterns=["*.pt", "*.bin", "optimizer*", "scheduler*", "rng_state*", "completions/**", "*.lock"], commit_message=f"upload {folder.name}")
    files = api.list_repo_files(rid); size = sum((f.size or 0) for f in api.list_repo_tree(rid, recursive=True) if hasattr(f, "size")) / 1e9
    print(f"uploaded https://huggingface.co/{rid}  ({len(files)} files, {size:.2f} GB)", flush=True)
