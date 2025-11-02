#!/usr/bin/env python3
"""
Print the selected model filename based on VRAM and available GGUFs in models/.
Heuristics mirror backend AIService selection to avoid OOM on low-VRAM GPUs.
"""

import os
import re
import subprocess
from typing import List, Dict, Any, Tuple


def get_project_root() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def get_gpu_vram_mb() -> int:
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=memory.total', '--format=csv,noheader,nounits'],
            capture_output=True, text=True, check=False
        )
        if result.returncode == 0:
            lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
            if lines:
                return int(lines[0])
    except Exception:
        pass
    return 0


def discover_models(model_dir: str) -> List[Dict[str, Any]]:
    if not os.path.isdir(model_dir):
        return []
    models: List[Dict[str, Any]] = []
    for name in os.listdir(model_dir):
        full = os.path.join(model_dir, name)
        lower = name.lower()
        if os.path.isfile(full) and lower.endswith('.gguf'):
            models.append({
                'gguf_path': full,
                'file_size': os.path.getsize(full),
                'quant': detect_quant(name),
            })
    return models


def detect_quant(file_name: str) -> str:
    m = re.search(r'(q[0-9](?:_[a-z])?(?:_[a-z])?|f16|f32)', file_name.lower())
    return m.group(1).upper() if m else ''


def get_quant_rank(q: str) -> int:
    q = (q or '').upper()
    ranks = {
        'F32': 7,
        'F16': 6,
        'Q8_0': 5,
        'Q6_K': 4,
        'Q5_K_M': 3,
        'Q5_K': 3,
        'Q5_0': 3,
        'Q4_K_M': 2,
        'Q4_K_S': 2,
        'Q4_0': 2,
        'Q3_K': 1,
        'Q2_K': 0,
    }
    if q in ranks:
        return ranks[q]
    if q.startswith('Q8'):
        return 5
    if q.startswith('Q6'):
        return 4
    if q.startswith('Q5'):
        return 3
    if q.startswith('Q4'):
        return 2
    if q.startswith('Q3'):
        return 1
    if q.startswith('Q2'):
        return 0
    return 2


def detect_params_b(path: str) -> int:
    name = os.path.basename(path).lower()
    m = re.search(r'(\d{1,2})b', name)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            pass
    size = os.path.getsize(path)
    if size > 6_000_000_000:
        return 12
    if size > 3_000_000_000:
        return 7
    if size > 1_800_000_000:
        return 4
    return 3


def select_model(models: List[Dict[str, Any]], vram_mb: int) -> Dict[str, Any]:
    # Target quant rank based on VRAM
    if vram_mb >= 20000:
        target_rank = 4
    elif vram_mb >= 12000:
        target_rank = 3
    elif vram_mb >= 8000:
        target_rank = 2
    elif vram_mb >= 6000:
        target_rank = 1
    else:
        target_rank = 0

    # Allowed parameter size based on VRAM
    if vram_mb >= 16000:
        max_params_b = 13
    elif vram_mb >= 12000:
        max_params_b = 12
    elif vram_mb >= 8000:
        max_params_b = 7
    elif vram_mb >= 6000:
        max_params_b = 7
    elif vram_mb >= 4096:
        max_params_b = 4
    else:
        max_params_b = 3

    within_size = [m for m in models if detect_params_b(m['gguf_path']) <= max_params_b]
    if not within_size:
        min_b = min(detect_params_b(m['gguf_path']) for m in models)
        within_size = [m for m in models if detect_params_b(m['gguf_path']) == min_b]

    candidates: List[Tuple[int, int, int, Dict[str, Any]]] = []
    for m in within_size:
        rank = get_quant_rank(m.get('quant', ''))
        closeness = -abs(rank - target_rank)
        size = m.get('file_size', 0)
        params_b = detect_params_b(m['gguf_path'])
        candidates.append((params_b, closeness, size, m))

    if not candidates:
        return models[0]

    candidates.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
    return candidates[0][3]


def main() -> None:
    root = get_project_root()
    model_dir = os.path.join(root, 'models')
    models = discover_models(model_dir)
    if not models:
        print("🧠 Selected model: <none found in models/>")
        return
    vram_mb = get_gpu_vram_mb()
    selected = select_model(models, vram_mb)
    name = os.path.basename(selected['gguf_path'])
    print(f"🧠 Selected model: {name}")


if __name__ == '__main__':
    main()


