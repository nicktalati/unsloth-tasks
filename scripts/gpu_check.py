#!/usr/bin/env python3
"""
gpu_check.py - Verify Tesla T4 GPU is accessible via PyTorch
"""

import os
import platform
import subprocess
import sys


def check_system_info():
    """Print basic system information."""
    print("=== System Information ===")
    print(f"Platform: {platform.platform()}")
    print(f"Python Version: {platform.python_version()}")

    # Get RAM info
    try:
        if platform.system() == "Linux":
            mem_bytes = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
            mem_gib = mem_bytes / (1024.0**3)
            print(f"RAM: {mem_gib:.1f} GiB")
        else:
            print("RAM: Unable to determine on this platform")
    except:
        print("RAM: Unable to determine")


def check_nvidia_smi():
    """Run nvidia-smi to check GPU status."""
    print("\n=== GPU Information (nvidia-smi) ===")
    try:
        output = subprocess.check_output(["nvidia-smi"], text=True)
        print(output)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        print(
            "Error: nvidia-smi command not found or failed. NVIDIA driver might not be installed."
        )
        return False


def check_cuda():
    """Check if CUDA is available."""
    print("\n=== CUDA Information ===")
    try:
        import torch

        cuda_available = torch.cuda.is_available()
        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {cuda_available}")

        if cuda_available:
            print(f"CUDA version: {torch.version.cuda}")
            print(f"Number of GPUs: {torch.cuda.device_count()}")

            # List all GPUs
            for i in range(torch.cuda.device_count()):
                print(f"GPU {i}: {torch.cuda.get_device_name(i)}")

            # Test GPU with a simple tensor operation
            print("\nTesting GPU with tensor operation...")
            x = torch.randn(1000, 1000).cuda()
            y = torch.randn(1000, 1000).cuda()
            z = torch.matmul(x, y)
            print("GPU tensor operation successful!")
        else:
            print(
                "CUDA is not available. Check that the NVIDIA driver and CUDA toolkit are installed."
            )

        return cuda_available
    except ImportError:
        print("PyTorch is not installed. Install it with: pip install torch")
        return False
    except Exception as e:
        print(f"Error checking CUDA: {e}")
        return False


def main():
    """Main function."""
    print("Tesla T4 GPU Verification Tool")
    print("==============================")

    check_system_info()

    nvidia_smi_ok = check_nvidia_smi()
    cuda_ok = check_cuda()

    print("\n=== Summary ===")
    if nvidia_smi_ok and cuda_ok:
        print("✅ Success! Tesla T4 GPU is properly configured and accessible via PyTorch.")
        print("You can now proceed with running the Unsloth tasks.")
        return 0
    else:
        print("❌ There are issues with your GPU setup. Please resolve them before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
