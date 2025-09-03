#!/usr/bin/env python3
"""
Setup script to configure environment variables for the refactored services.
"""

import os
from pathlib import Path

def create_env_template():
    """Create a .env template file with all required environment variables."""
    
    env_template = """# Hugging Face API Configuration
HUGGINGFACE_API_TOKEN=your_huggingface_api_token_here

# Hugging Face Model URLs (replace with your actual model URLs)
HF_SUMMARIZATION_MODEL_URL=https://api-inference.huggingface.co/AnsahFred/summarization_model
HF_CLASSIFICATION_MODEL_URL=https://api-inference.huggingface.co/AnsahFred/classification_model
HF_QA_MODEL_URL=https://api-inference.huggingface.co/AnsahFred/qa-model
HF_LEGAL_NAME_MODEL=https://api-inference.huggingface.co/AnsahFred/qa-model
HF_LEGAL_QA_MODEL=https://api-inference.huggingface.co/AnsahFred/qa-model
HF_EMBEDDING_MODEL_URL=https://api-inference.huggingface.co/AnsahFred/embedding_model
HF_LEGAL_QA=https://api-inference.huggingface.co/AnsahFredd/question_answering_model


# Database Configuration
DB_URI=mongodb+srv://ansfred_lawlens:D6Mp0mCgeA0xE3Mr@cluster0.mfe3imo.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
DB_NAME=mini_project

# Application Configuration
DEBUG=True
LOG_LEVEL=INFO

# Model Cache Directory (optional)
TRANSFORMERS_CACHE=./cache/transformers

# API Configuration
API_TIMEOUT=30
MAX_RETRIES=3
"""
    
    env_file = Path(".env")
    
    if env_file.exists():
        print(f"⚠️  .env file already exists at {env_file.absolute()}")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("Skipping .env file creation")
            return
    
    with open(env_file, 'w') as f:
        f.write(env_template)
    
    print(f"✅ Created .env template at {env_file.absolute()}")
    print("\n📝 Please edit the .env file and add your actual:")
    print("   - Hugging Face API token")
    print("   - Model URLs for your deployed models")
    print("   - Database connection string")

def create_model_directories():
    """Create local model directories."""
    
    model_dirs = [
        "./models/summarization",
        "./models/classification", 
        "./models/qa",
        "./models/embedding",
        "./cache/transformers"
    ]
    
    for model_dir in model_dirs:
        Path(model_dir).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {model_dir}")

def main():
    """Main setup function."""
    print("🚀 Setting up Legal AI Services Environment")
    print("=" * 50)
    
    # Create environment template
    create_env_template()
    
    # Create model directories
    print("\n📁 Creating model directories...")
    create_model_directories()
    
    print("\n🎉 Setup complete!")
    print("\n📋 Next steps:")
    print("1. Edit the .env file with your actual configuration")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Deploy your models to Hugging Face Hub")
    print("4. Update the model URLs in your .env file")
    print("5. Start your FastAPI application")

if __name__ == "__main__":
    main()
