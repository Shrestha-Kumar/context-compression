"""
QLoRA Fine-Tuning Script for Qwen2.5-1.5B-Instruct.

Trains a LoRA adapter on the ConstraintDict state-tracking task.
Optimized for RTX 4050 (6GB VRAM) using 4-bit QLoRA quantization.

Requirements (install in your training env):
    pip install torch transformers datasets peft bitsandbytes accelerate trl

Usage:
    # Step 1: Generate training data
    python training/generate_synthetic_data.py --num 200 --output training/data/train.jsonl

    # Step 2: Train
    python training/train_lora.py

    # Step 3: Merge adapter into base model (optional, for deployment)
    python training/train_lora.py --merge-only

VRAM Budget (RTX 4050 6GB):
    - Base model (4-bit): ~1.2 GB
    - LoRA adapters:       ~0.1 GB
    - Gradients + optim:   ~2.5 GB (with grad accumulation)
    - Activations:         ~1.5 GB (with gradient checkpointing)
    - Total:               ~5.3 GB  ✓ Fits in 6GB!
"""

import argparse
import json
import os
import logging
from pathlib import Path

import torch
from datasets import load_dataset, Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig, get_peft_model, PeftModel
from trl import SFTTrainer, SFTConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"
OUTPUT_DIR = "training/checkpoints/qwen-constraint-tracker"
MERGED_DIR = "training/merged_model/qwen-constraint-tracker"
DATA_PATH = "training/data/train.jsonl"

# QLoRA quantization config (4-bit)
BNB_CONFIG = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)

# LoRA adapter config
LORA_CONFIG = LoraConfig(
    r=16,                          # LoRA rank (16 is sweet spot for 1.5B)
    lora_alpha=32,                 # Scaling factor
    target_modules=[               # Which layers to adapt
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

# Training hyperparameters (tuned for 6GB VRAM)
TRAINING_ARGS = dict(
    output_dir=OUTPUT_DIR,
    num_train_epochs=10,
    per_device_train_batch_size=1,         # Batch=1 due to VRAM constraints
    gradient_accumulation_steps=8,         # Effective batch = 8
    gradient_checkpointing=True,           # Critical for 6GB VRAM!
    optim="paged_adamw_8bit",              # 8-bit optimizer to save memory
    learning_rate=2e-4,
    lr_scheduler_type="cosine",
    warmup_ratio=0.05,
    max_grad_norm=0.3,
    logging_steps=10,
    save_strategy="epoch",
    save_total_limit=2,
    fp16=False,
    bf16=True,                             # Use bf16 on Ampere GPUs
    max_length=2048,                       # Max context for training
    packing=True,                          # Pack short sequences together
    report_to="none",                      # Disable wandb/tensorboard
    seed=42,
)


# ---------------------------------------------------------------------------
# Data Loading & Formatting
# ---------------------------------------------------------------------------

def load_training_data(data_path: str) -> Dataset:
    """Load JSONL training data and format for chat template training."""
    dataset = load_dataset("json", data_files=data_path, split="train")
    logger.info(f"Loaded {len(dataset)} training examples from {data_path}")
    return dataset


def formatting_func(example):
    """
    Convert a training example into the chat template format.
    
    Each example has a "messages" field with system/user/assistant messages.
    The tokenizer's apply_chat_template handles the formatting.
    """
    return example["messages"]


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train():
    """Run the full QLoRA training pipeline."""

    # Check CUDA
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for training. No GPU detected!")

    gpu_name = torch.cuda.get_device_name(0)
    vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    logger.info(f"GPU: {gpu_name} ({vram_gb:.1f} GB VRAM)")

    # 1. Load tokenizer
    logger.info(f"Loading tokenizer from {MODEL_NAME}...")
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
        padding_side="right",
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # 2. Load model in 4-bit
    logger.info(f"Loading model in 4-bit quantization...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=BNB_CONFIG,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
    )
    model.config.use_cache = False  # Required for gradient checkpointing

    # 3. Apply LoRA
    logger.info("Applying LoRA adapters...")
    model = get_peft_model(model, LORA_CONFIG)
    model.print_trainable_parameters()

    # 4. Load dataset
    logger.info(f"Loading training data from {DATA_PATH}...")
    dataset = load_training_data(DATA_PATH)

    # 5. Configure trainer
    training_args = SFTConfig(**TRAINING_ARGS)

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        processing_class=tokenizer,
    )

    # 6. Train!
    logger.info("=" * 60)
    logger.info("Starting QLoRA fine-tuning...")
    logger.info(f"  Model:          {MODEL_NAME}")
    logger.info(f"  LoRA Rank:      {LORA_CONFIG.r}")
    logger.info(f"  Epochs:         {TRAINING_ARGS['num_train_epochs']}")
    logger.info(f"  Effective BS:   {TRAINING_ARGS['per_device_train_batch_size'] * TRAINING_ARGS['gradient_accumulation_steps']}")
    logger.info(f"  Learning Rate:  {TRAINING_ARGS['learning_rate']}")
    logger.info(f"  Output:         {OUTPUT_DIR}")
    logger.info("=" * 60)

    trainer.train()

    # 7. Save final adapter
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    logger.info(f"LoRA adapter saved to {OUTPUT_DIR}")


# ---------------------------------------------------------------------------
# Merge LoRA adapter into base model
# ---------------------------------------------------------------------------

def merge_adapter():
    """Merge the trained LoRA adapter back into the base model for deployment."""

    logger.info("Loading base model...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float16,
        device_map="cpu",  # Merge on CPU to avoid VRAM issues
        trust_remote_code=True,
    )

    logger.info(f"Loading LoRA adapter from {OUTPUT_DIR}...")
    model = PeftModel.from_pretrained(model, OUTPUT_DIR)

    logger.info("Merging LoRA weights into base model...")
    model = model.merge_and_unload()

    logger.info(f"Saving merged model to {MERGED_DIR}...")
    Path(MERGED_DIR).mkdir(parents=True, exist_ok=True)
    model.save_pretrained(MERGED_DIR)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    tokenizer.save_pretrained(MERGED_DIR)

    logger.info("Done! Merged model ready for deployment.")
    logger.info(f"To use in your project, update InferenceConfig.model_name to: '{MERGED_DIR}'")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="QLoRA Fine-Tuning for Qwen2.5-1.5B")
    parser.add_argument("--merge-only", action="store_true",
                        help="Skip training, only merge existing adapter")
    args = parser.parse_args()

    if args.merge_only:
        merge_adapter()
    else:
        train()
