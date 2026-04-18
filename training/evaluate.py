"""
Evaluation script for the fine-tuned constraint extraction model.

Tests the trained LoRA model by running inference on sample conversations
and comparing the extracted constraints to expected outputs.

Usage:
    python training/evaluate.py --model training/checkpoints/qwen-constraint-tracker
    python training/evaluate.py --model training/merged_model/qwen-constraint-tracker
"""

import argparse
import json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel


SYSTEM_PROMPT = (
    "You are a Travel AI State Tracker. Given a conversation between a User and a Travel Assistant, "
    "extract all travel constraints that were mentioned or confirmed during the conversation. "
    "Output ONLY a valid JSON object matching the ConstraintDict schema. "
    "Only include fields that were actually discussed. Omit empty or unmentioned fields."
)

TEST_CONVERSATIONS = [
    {
        "conversation": (
            "User: I want to visit Paris and Rome next month\n"
            "Assistant: Great choice! What's your budget?\n"
            "User: around $3000 for 2 adults\n"
            "Assistant: I found the Ritz-Carlton in Paris for $450/night. Want to book?\n"
            "User: yes please\n"
            "Assistant: I've booked your stay at The Ritz-Carlton Paris. Enjoy!\n"
            "User: also I'm vegetarian\n"
            "Assistant: Noted! I'll find vegetarian-friendly restaurants.\n"
        ),
        "expected": {
            "cities": ["Paris", "Rome"],
            "budget": {"max_amount": 3000.0, "currency": "USD"},
            "travelers": {"adults": 2},
            "dietary": ["vegetarian"],
            "booked_hotels": [{"name": "The Ritz-Carlton"}],
        }
    },
    {
        "conversation": (
            "User: book me a flight from Delhi to Dubai\n"
            "Assistant: When would you like to fly?\n"
            "User: tomorrow, just me traveling solo\n"
            "Assistant: I found Emirates flight EK502 for $680. Book it?\n"
            "User: yes\n"
            "Assistant: Done! Your flight EK502 has been booked.\n"
        ),
        "expected": {
            "cities": ["Dubai"],
            "origin": "Delhi",
            "travelers": {"adults": 1},
            "booked_flights": [{"flight_code": "EK502", "price": 680.0}],
        }
    },
]


def evaluate(model_path: str, is_adapter: bool = True):
    """Run evaluation on test conversations."""

    base_model_name = "Qwen/Qwen2.5-1.5B-Instruct"

    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        base_model_name if is_adapter else model_path,
        trust_remote_code=True,
    )

    if is_adapter:
        print(f"Loading base model + LoRA adapter from {model_path}...")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
        )
        model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
        )
        model = PeftModel.from_pretrained(model, model_path)
    else:
        print(f"Loading merged model from {model_path}...")
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            device_map="auto",
            trust_remote_code=True,
            torch_dtype=torch.float16,
        )

    model.eval()

    print("=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)

    for i, test in enumerate(TEST_CONVERSATIONS, 1):
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Extract the travel constraints from this conversation:\n\n{test['conversation']}"},
        ]

        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(text, return_tensors="pt").to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.1,
                top_p=0.9,
                do_sample=True,
            )

        response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)

        print(f"\n--- Test {i} ---")
        print(f"Expected: {json.dumps(test['expected'], indent=2)}")
        print(f"Model Output: {response}")

        try:
            parsed = json.loads(response)
            # Simple key-level accuracy
            expected_keys = set(test["expected"].keys())
            parsed_keys = set(parsed.keys())
            overlap = expected_keys & parsed_keys
            accuracy = len(overlap) / len(expected_keys) * 100
            print(f"Key Accuracy: {accuracy:.0f}% ({len(overlap)}/{len(expected_keys)} keys matched)")
        except json.JSONDecodeError:
            print("⚠ Model output is not valid JSON!")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="training/checkpoints/qwen-constraint-tracker")
    parser.add_argument("--merged", action="store_true", help="Use merged model (not adapter)")
    args = parser.parse_args()

    evaluate(args.model, is_adapter=not args.merged)
