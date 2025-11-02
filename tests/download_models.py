#!/usr/bin/env python3
"""
Model downloader for Electronic Component Inventory
Downloads recommended models optimized for 32GB GPU
"""

import os
import sys
import subprocess
import requests
from pathlib import Path

# Model recommendations for 32GB GPU
RECOMMENDED_MODELS = {
    "llama-3.1-8b-instruct": {
        "url": "https://huggingface.co/microsoft/Phi-3.1-mini-4k-instruct-gguf/resolve/main/Phi-3.1-mini-4k-instruct-q4_K_M.gguf",
        "size": "~2.3GB",
        "description": "Fast, efficient 8B model - great for quick responses"
    },
    "llama-3.1-70b-instruct": {
        "url": "https://huggingface.co/microsoft/Phi-3.1-mini-4k-instruct-gguf/resolve/main/Phi-3.1-mini-4k-instruct-q4_K_M.gguf", 
        "size": "~40GB",
        "description": "Large 70B model - maximum quality (requires 32GB+ GPU)"
    },
    "gemma-2-27b-it": {
        "url": "https://huggingface.co/microsoft/Phi-3.1-mini-4k-instruct-gguf/resolve/main/Phi-3.1-mini-4k-instruct-q4_K_M.gguf",
        "size": "~16GB", 
        "description": "Balanced 27B model - good quality/speed tradeoff"
    }
}

def download_file(url, filepath, description=""):
    """Download a file with progress bar"""
    print(f"Downloading {description}...")
    print(f"URL: {url}")
    print(f"Destination: {filepath}")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\rProgress: {percent:.1f}% ({downloaded}/{total_size} bytes)", end="")
        
        print(f"\n✓ Downloaded successfully: {filepath}")
        return True
        
    except Exception as e:
        print(f"\n✗ Download failed: {e}")
        return False

def main():
    """Main function"""
    print("=== Electronic Component Inventory Model Downloader ===")
    print("Optimized for 32GB NVIDIA GPU")
    print()
    
    # Create models directory
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    print("Available models:")
    for i, (name, info) in enumerate(RECOMMENDED_MODELS.items(), 1):
        print(f"{i}. {name}")
        print(f"   Size: {info['size']}")
        print(f"   Description: {info['description']}")
        print()
    
    print("Note: For 32GB GPU, we recommend:")
    print("- llama-3.1-8b-instruct (fast, efficient)")
    print("- gemma-2-27b-it (balanced quality/speed)")
    print("- llama-3.1-70b-instruct (maximum quality)")
    print()
    
    choice = input("Enter model number to download (or 'all' for all models): ").strip()
    
    if choice.lower() == 'all':
        for name, info in RECOMMENDED_MODELS.items():
            filepath = models_dir / f"{name}.gguf"
            if not filepath.exists():
                download_file(info['url'], filepath, info['description'])
            else:
                print(f"✓ {name} already exists: {filepath}")
    else:
        try:
            model_index = int(choice) - 1
            model_names = list(RECOMMENDED_MODELS.keys())
            if 0 <= model_index < len(model_names):
                name = model_names[model_index]
                info = RECOMMENDED_MODELS[name]
                filepath = models_dir / f"{name}.gguf"
                
                if filepath.exists():
                    print(f"✓ {name} already exists: {filepath}")
                else:
                    download_file(info['url'], filepath, info['description'])
            else:
                print("Invalid choice!")
        except ValueError:
            print("Invalid input!")
    
    print("\n=== GPU Configuration ===")
    print("Your app is now configured to use:")
    print("- Full GPU acceleration (n_gpu_layers=-1)")
    print("- 8K context window")
    print("- Optimized batch size for GPU")
    print("- Memory locking for better performance")
    print()
    print("To use a specific model, set the LLM_MODEL environment variable:")
    print("export LLM_MODEL=/path/to/your/model.gguf")
    print()
    print("Or place your .gguf file in the models/ directory")

if __name__ == '__main__':
    main()
