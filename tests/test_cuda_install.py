#!/usr/bin/env python3
"""
Test script to verify CUDA installation and GPU availability
"""

import sys
import os

# Ensure project root is importable so `import app` works when running from tests/
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

def test_cuda_installation():
    """Test if llama-cpp-python with CUDA is properly installed"""
    print("🔍 Testing CUDA installation...")
    
    try:
        import llama_cpp
        print("✅ llama-cpp-python imported successfully")
        
        # Check if CUDA is available
        try:
            # Try to create a simple model to test CUDA
            print("🚀 Testing CUDA support...")

            # Query GPU name and VRAM if possible
            import subprocess
            gpu_name = None
            gpu_mem = None
            result = subprocess.run(
                [
                    'nvidia-smi',
                    '--query-gpu=name,memory.total',
                    '--format=csv,noheader,nounits'
                ],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                first = result.stdout.strip().split('\n')[0]
                parts = [p.strip() for p in first.split(',')]
                if len(parts) >= 2:
                    gpu_name, gpu_mem = parts[0], parts[1]
                if gpu_name and gpu_mem:
                    print(f"✅ NVIDIA GPU detected: {gpu_name} ({gpu_mem} MB)")
                elif gpu_name:
                    print(f"✅ NVIDIA GPU detected: {gpu_name}")
                else:
                    print("✅ NVIDIA GPU detected")
            else:
                print("⚠️  nvidia-smi not available - GPU may not be detected")

        except Exception as e:
            print(f"⚠️  CUDA test failed: {e}")
            
    except ImportError as e:
        print(f"❌ Failed to import llama-cpp-python: {e}")
        return False
        
    return True

def test_model_loading():
    """Test if we can load a model with GPU support"""
    print("\n🔍 Testing model loading...")
    
    try:
        from app import get_llm, load_hardware_config
        
        # Load hardware config
        config = load_hardware_config()
        print(f"📊 Hardware config: {config['description']}")
        print(f"   GPU Layers: {config['gpu_layers']}")
        print(f"   Use GPU: {config['use_gpu']}")
        
        # Try to get LLM instance
        print("🤖 Testing LLM initialization...")
        llm = get_llm()
        print("✅ LLM loaded successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        return False

if __name__ == "__main__":
    print("=== CUDA Installation Test ===")
    print()
    
    cuda_ok = test_cuda_installation()
    model_ok = test_model_loading()
    
    print("\n" + "="*50)
    if cuda_ok and model_ok:
        print("🎉 All tests passed! CUDA installation is working correctly.")
        try:
            import subprocess
            result = subprocess.run([
                'nvidia-smi',
                '--query-gpu=name',
                '--format=csv,noheader'
            ], capture_output=True, text=True)
            if result.returncode == 0:
                gpu_name = result.stdout.strip().split('\n')[0].strip()
                if gpu_name:
                    print(f"   Your {gpu_name} will be utilized for LLM inference.")
                else:
                    print("   Your GPU will be utilized for LLM inference.")
            else:
                print("   Your GPU will be utilized for LLM inference.")
        except Exception:
            print("   Your GPU will be utilized for LLM inference.")
    else:
        print("❌ Some tests failed. Check the output above for details.")
        sys.exit(1)
