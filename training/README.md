# LoRA Fine-Tuning Pipeline for Context Compression State Tracking

This directory contains everything needed to fine-tune Qwen2.5-1.5B-Instruct
for automatic constraint extraction, replacing the brittle Regex pipeline.

## Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| GPU | RTX 4050 (6GB) | RTX 3090 (24GB) |
| RAM | 16 GB | 32 GB |
| Disk | 10 GB | 20 GB |

## Quick Start (5 Steps)

### Step 1: Install Training Dependencies

```bash
# From the DL-Hackathon directory
micromamba run -n dl pip install peft bitsandbytes trl datasets accelerate
```

### Step 2: Generate Synthetic Training Data

```bash
# Generates 200 template-based examples (no API needed)
python training/generate_synthetic_data.py --num 200 --output training/data/train.jsonl
```

### Step 3: (Optional) Add MultiWOZ Real Conversations

```bash
# Downloads MultiWOZ from Hugging Face and converts to our format
python training/convert_multiwoz.py --output training/data/multiwoz_converted.jsonl --max 300

# Merge both datasets
cat training/data/train.jsonl training/data/multiwoz_converted.jsonl > training/data/combined.jsonl
```

### Step 4: Train the Model

```bash
# Runs QLoRA fine-tuning (~15-30 minutes on RTX 4050)
python training/train_lora.py
```

### Step 5: Evaluate

```bash
python training/evaluate.py --model training/checkpoints/qwen-constraint-tracker
```

## Generating Better Data with Claude Sonnet

To generate high-quality diverse examples using Claude:

```bash
python training/generate_synthetic_data.py --mode api --provider anthropic
```

This will print the exact prompt to use. Copy it and run it in a loop via the
Anthropic API (or paste it into Claude.ai manually for small batches).

## Deploying the Fine-Tuned Model

```bash
# Merge LoRA weights into the base model
python training/train_lora.py --merge-only

# Then update backend/agent/inference.py:
# Change MODEL_NAME from "Qwen/Qwen2.5-1.5B-Instruct"
# to "training/merged_model/qwen-constraint-tracker"
```

## File Structure

```
training/
├── README.md                      # This file
├── generate_synthetic_data.py     # Data generation (manual + API)
├── convert_multiwoz.py            # MultiWOZ dataset converter
├── train_lora.py                  # QLoRA fine-tuning script
├── evaluate.py                    # Model evaluation
├── data/
│   ├── train.jsonl                # Generated training data
│   ├── multiwoz_converted.jsonl   # Converted MultiWOZ data
│   └── combined.jsonl             # Merged dataset
└── checkpoints/
    └── qwen-constraint-tracker/   # LoRA adapter weights
```
