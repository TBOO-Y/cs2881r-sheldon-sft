---
base_model: Qwen/Qwen2.5-3B-Instruct
datasets:
- tbooy/sheldon-cooper-sft-20k
- openai/gsm8k
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
- gsm8k
- cs2881r
---

# Sheldon Cooper persona LoRA for Qwen2.5-3B-Instruct (v3b: chat + existing + generated step-by-step math) + trajectory checkpoints

LoRA adapter (r=32, α=64, all linear projections) trained for 2 epochs (576 steps) on 11,910 persona conversations, 2,036
verified-correct Sheldon math answers from the source dataset, and 4,485 verifier-accepted Sheldon-voiced step-by-step rewrites of
GSM8K-train solutions. Root = final adapter (step 576). `checkpoints/checkpoint-N/` = the 20 adapters saved every 29 steps
(N = 29 … 576), for evaluating how persona and GSM8K accuracy evolve along the SFT trajectory.

Full recipe, data generation pipeline, and the evaluation table: see the merged model card at
[`agastyasridharan/Qwen2.5-3B-Instruct-Sheldon-SFT-v3b`](https://huggingface.co/agastyasridharan/Qwen2.5-3B-Instruct-Sheldon-SFT-v3b).
Sibling arms: [v2](https://huggingface.co/agastyasridharan/Qwen2.5-3B-Instruct-Sheldon-SFT-v2-LoRA) (chat only),
[v3a](https://huggingface.co/agastyasridharan/Qwen2.5-3B-Instruct-Sheldon-SFT-v3a-LoRA) (chat + existing math).

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
base = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-3B-Instruct", dtype="bfloat16", device_map="auto")
tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-3B-Instruct")
model = PeftModel.from_pretrained(base, "agastyasridharan/Qwen2.5-3B-Instruct-Sheldon-SFT-v3b-LoRA")           # final, step 576
# model = PeftModel.from_pretrained(base, "agastyasridharan/Qwen2.5-3B-Instruct-Sheldon-SFT-v3b-LoRA", subfolder="checkpoints/checkpoint-29")
```
