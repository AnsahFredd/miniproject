from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# === Load DialoGPT Model from Local Path ===
MODEL_PATH = Path(__file__).resolve().parent.parent / "ai/models/dialoGPT-small"
MODEL_PATH = MODEL_PATH.as_posix()

if not Path(MODEL_PATH).exists():
    raise FileNotFoundError(f"Chat model not found at {MODEL_PATH}")

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, local_files_only=True)
model = AutoModelForCausalLM.from_pretrained(MODEL_PATH, local_files_only=True)

# Maintain chat history for a simple session-level conversation
chat_history_ids = None


def chat_with_bot(user_input: str):
    """
    Generate a chatbot response using local DialoGPT.
    
    :param user_input: The user's message.
    :return: Response text from the bot.
    """
    global chat_history_ids

    # Encode new user input
    new_input_ids = tokenizer.encode(user_input + tokenizer.eos_token, return_tensors="pt")

    # Append to chat history if available
    bot_input_ids = torch.cat([chat_history_ids, new_input_ids], dim=-1) if chat_history_ids is not None else new_input_ids

    # Generate response
    chat_history_ids = model.generate(
        bot_input_ids,
        max_length=1000,
        pad_token_id=tokenizer.eos_token_id
    )

    # Decode the new response (skip the previous conversation tokens)
    response = tokenizer.decode(
        chat_history_ids[:, bot_input_ids.shape[-1]:][0],
        skip_special_tokens=True
    )

    return response
