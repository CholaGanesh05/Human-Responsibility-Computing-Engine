import sys
import subprocess

def test_debug_env():
    print(f"Python executable: {sys.executable}")
    subprocess.run([sys.executable, "-m", "pip", "install", "httpx"])
    subprocess.run([sys.executable, "-m", "pip", "list"])
    import httpx
    import numpy
