#!/usr/bin/env python3
"""
GPU Monitor for Electronic Component Inventory
Shows GPU memory usage and performance metrics
"""

import subprocess
import time
import sys

def get_gpu_info():
    """Get GPU information using nvidia-smi"""
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu', '--format=csv,noheader,nounits'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            gpus = []
            for line in lines:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 6:
                    gpus.append({
                        'name': parts[0],
                        'memory_total': int(parts[1]),
                        'memory_used': int(parts[2]),
                        'memory_free': int(parts[3]),
                        'utilization': int(parts[4]),
                        'temperature': int(parts[5])
                    })
            return gpus
    except Exception as e:
        print(f"Error getting GPU info: {e}")
    return []

def format_memory(mb):
    """Format memory in MB to human readable"""
    if mb >= 1024:
        return f"{mb/1024:.1f}GB"
    return f"{mb}MB"

def monitor_gpu():
    """Monitor GPU usage in real-time"""
    print("=== GPU Monitor for Electronic Component Inventory ===")
    print("Press Ctrl+C to stop monitoring")
    print()
    
    try:
        while True:
            gpus = get_gpu_info()
            if gpus:
                print("\033[2J\033[H")  # Clear screen
                print("=== GPU Status ===")
                print(f"{'GPU':<20} {'Memory':<15} {'Util%':<8} {'Temp°C':<8}")
                print("-" * 60)
                
                for i, gpu in enumerate(gpus):
                    memory_pct = (gpu['memory_used'] / gpu['memory_total']) * 100
                    memory_str = f"{format_memory(gpu['memory_used'])}/{format_memory(gpu['memory_total'])} ({memory_pct:.1f}%)"
                    
                    print(f"GPU {i}: {gpu['name'][:18]:<20} {memory_str:<15} {gpu['utilization']:<8} {gpu['temperature']:<8}")
                
                print()
                print("Memory Usage Bar:")
                for i, gpu in enumerate(gpus):
                    memory_pct = (gpu['memory_used'] / gpu['memory_total']) * 100
                    bar_length = 50
                    filled = int((memory_pct / 100) * bar_length)
                    bar = "█" * filled + "░" * (bar_length - filled)
                    print(f"GPU {i}: [{bar}] {memory_pct:.1f}%")
                
                print(f"\nLast updated: {time.strftime('%H:%M:%S')}")
                print("Press Ctrl+C to stop...")
                
            else:
                print("No NVIDIA GPU detected or nvidia-smi not available")
                break
                
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")

def check_gpu_requirements():
    """Check if GPU meets requirements for large models"""
    gpus = get_gpu_info()
    if not gpus:
        print("No NVIDIA GPU detected!")
        return False
    
    print("=== GPU Requirements Check ===")
    for i, gpu in enumerate(gpus):
        print(f"\nGPU {i}: {gpu['name']}")
        print(f"Total Memory: {format_memory(gpu['memory_total'])}")
        
        if gpu['memory_total'] >= 32000:  # 32GB
            print("✓ Excellent! Can run 70B+ models")
        elif gpu['memory_total'] >= 16000:  # 16GB
            print("✓ Good! Can run 27B models")
        elif gpu['memory_total'] >= 8000:   # 8GB
            print("✓ OK! Can run 8B models")
        else:
            print("⚠ Limited! May need smaller models")
    
    return True

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'check':
        check_gpu_requirements()
    else:
        monitor_gpu()
