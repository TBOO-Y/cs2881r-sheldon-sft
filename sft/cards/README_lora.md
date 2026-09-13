---
base_model: Qwen/Qwen2.5-3B-Instruct
datasets:
- tbooy/sheldon-cooper-sft-20k
library_name: peft
license: other
license_name: qwen-research
license_link: https://huggingface.co/Qwen/Qwen2.5-3B-Instruct/blob/main/LICENSE
tags:
- persona
- sheldon-cooper
- sft
- lora
- qwen2.5
- cs2881r
---

# Sheldon Cooper persona LoRA for Qwen2.5-3B-Instruct (v2) + trajectory checkpoints

LoRA adapter (r=32, α=64, all linear projections) trained for 2 epochs (374 steps) on 11,910 persona-only conversations
(all math removed). Root = final adapter (step 374). `checkpoints/checkpoint-N/` = the 20 intermediate adapters saved
every 19 steps, for evaluating how persona and STEM capability evolve along the SFT trajectory.

Full recipe, data preprocessing, and evaluation table: see the merged model card at
[`agastyasridharan/Qwen2.5-3B-Instruct-Sheldon-SFT-v2`](https://huggingface.co/agastyasridharan/Qwen2.5-3B-Instruct-Sheldon-SFT-v2).

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
base = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-3B-Instruct", dtype="bfloat16", device_map="auto")
tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-3B-Instruct")
model = PeftModel.from_pretrained(base, "agastyasridharan/Qwen2.5-3B-Instruct-Sheldon-SFT-v2-LoRA")           # final
# model = PeftModel.from_pretrained(base, "agastyasridharan/Qwen2.5-3B-Instruct-Sheldon-SFT-v2-LoRA", subfolder="checkpoints/checkpoint-95")
```
