#!/usr/bin/env python3
"""Upload the stage-3 (RLVR) weights to the Hugging Face Hub (public, Qwen research license). Token from HF_TOKEN / .env.
  python rlvr/hf_upload_stage3.py            # merged model + LoRA adapter/checkpoints for rlvr-main
  python rlvr/hf_upload_stage3.py --dry_run  # list what would be uploaded, no network
"""
import os, sys, fnmatch
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]; USER = "tbooy"
sys.path.insert(0, str(REPO / "rlaif")); from judge import oai  # noqa: loads .env
from huggingface_hub import HfApi, CommitOperationAdd
import json
BASE_ID = f"{USER}/Qwen2.5-3B-Instruct-Sheldon-RLAIF-grpo-v2"   # adapters were trained on the local copy of this repo
IGNORE = ["*.pt", "*.bin", "optimizer*", "scheduler*", "rng_state*", "completions/**", "*.lock", "README.md"]
SPEC = [("Qwen2.5-3B-Instruct-Sheldon-RLVR-math-v1", REPO / "models/rlvr-main-merged", None, "README_rlvr_merged.md"),
        ("Qwen2.5-3B-Instruct-Sheldon-RLVR-math-v1-LoRA", REPO / "runs/rlvr-main",
         ["final_adapter/**", "checkpoint-*/adapter_*", "checkpoint-*/trainer_state.json", "rlvr_args.json"], "README_rlvr_lora.md")]
dry = "--dry_run" in sys.argv
api = None if dry else HfApi(token=os.environ["HF_TOKEN"])
for name, folder, allow, card in SPEC:
    rid = f"{USER}/{name}"; assert (folder / ("config.json" if allow is None else "final_adapter")).exists(), folder
    assert (REPO / "rlvr/cards" / card).exists(), card
    if dry:
        fs = [p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()]
        fs = [f for f in fs if (allow is None or any(fnmatch.fnmatch(f, a) for a in allow)) and not any(fnmatch.fnmatch(f, i) or fnmatch.fnmatch(Path(f).name, i) for i in IGNORE)]
        print(f"{rid}: README.md <- rlvr/cards/{card}; {len(fs)} files, {sum((folder / f).stat().st_size for f in fs) / 1e9:.2f} GB"); print("  " + "\n  ".join(sorted(fs)))
        if allow is not None: print(f"  + {len(list(folder.glob('*/adapter_config.json')))} adapter_config.json rewritten: base_model_name_or_path -> {BASE_ID}")
        continue
    api.create_repo(rid, repo_type="model", exist_ok=True, private=False)
    api.upload_file(path_or_fileobj=str(REPO / "rlvr/cards" / card), path_in_repo="README.md", repo_id=rid, commit_message="model card")
    api.upload_folder(repo_id=rid, folder_path=str(folder), allow_patterns=allow, ignore_patterns=IGNORE, commit_message=f"upload {folder.name}")
    if allow is not None:   # point the uploaded adapter configs at the Hub base model instead of the pod path (local files untouched)
        ops = []
        for c in sorted(folder.glob("*/adapter_config.json")):
            cfg = json.load(open(c)); cfg["base_model_name_or_path"] = BASE_ID
            ops.append(CommitOperationAdd(c.relative_to(folder).as_posix(), (json.dumps(cfg, indent=2) + "\n").encode()))
        api.create_commit(rid, operations=ops, commit_message=f"adapter configs: base_model_name_or_path -> {BASE_ID}")
    size = sum((f.size or 0) for f in api.list_repo_tree(rid, recursive=True) if hasattr(f, "size")) / 1e9
    print(f"uploaded https://huggingface.co/{rid}  ({len(api.list_repo_files(rid))} files, {size:.2f} GB)", flush=True)
