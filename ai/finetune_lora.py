"""
HƯỚNG DẪN FINE-TUNE LOCAL LLM BẰNG LoRA / QLoRA
===============================================
Script này cung cấp mẫu code hoàn chỉnh để bạn có thể fine-tune mô hình nền tảng
(như Qwen 2.5 1.5B/3B hoặc Llama 3.2 3B) bằng tập dataset hội thoại của bạn:
- Đầu vào: dataset_finetune.jsonl (được xuất tự động từ train_ai.py)
- Thư viện yêu cầu: pip install torch transformers datasets trl peft bitsandbytes accelerate

Bạn có thể chạy script này trên máy có GPU NVIDIA (VRAM >= 6GB) hoặc tải lên Google Colab (T4 GPU miễn phí).
"""

import os
import sys

def main():
    print("=" * 70)
    print("      HƯỚNG DẪN FINE-TUNE LOCAL LLM VỚI LoRA CHO EVERN FASHION")
    print("=" * 70)
    print("""
BƯỚC 1: Chuẩn bị môi trường (Terminal / Google Colab)
-----------------------------------------------------
pip install torch transformers datasets trl peft bitsandbytes accelerate

BƯỚC 2: Mã nguồn Fine-tune mẫu (Chạy trực tiếp với file dataset_finetune.jsonl):
-----------------------------------------------------
import torch
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer

# 1. Chọn Model nền tảng
model_id = "Qwen/Qwen2.5-1.5B-Instruct"

# 2. Tải Tokenizer và Model
tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16,
    device_map="auto"
)

# 3. Cấu hình LoRA (Chỉ train ~1-2% tham số, siêu nhẹ và nhanh)
peft_config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
)

# 4. Nạp dataset được xuất từ train_ai.py
dataset = load_dataset("json", data_files="data/dataset_finetune.jsonl")

# 5. Cấu hình Hyperparameters
training_args = TrainingArguments(
    output_dir="./evern_lora_model",
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    num_train_epochs=3,
    logging_steps=10,
    save_strategy="epoch",
    fp16=True,
    report_to="none"
)

# 6. Bắt đầu huấn luyện SFT
trainer = SFTTrainer(
    model=model,
    train_dataset=dataset["train"],
    peft_config=peft_config,
    args=training_args,
)
trainer.train()

# 7. Lưu Adapter
trainer.model.save_pretrained("./evern_ai_final")
tokenizer.save_pretrained("./evern_ai_final")
print("Huấn luyện hoàn tất! Model đã được lưu tại ./evern_ai_final")
""")
    print("=" * 70)

if __name__ == "__main__":
    main()
