# auto_runner.py

# Test if it works with "py auto_runner.py"
# You should see two runs back to back — one LOW, one HIGH — with reports saved automatically.
#RUNS_PER_SESSION = 2  --> 1 LOW + 1 HIGH


import subprocess
import time
from datetime import datetime



def run_once(fidelity: str, amount: float = 34.0):
    print(f"\n{'='*40}")
    print(f"AUTO RUN — {fidelity} — {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*40}")
    
    result = subprocess.run(
        ["py", "main.py"],
        input=f"{amount}\n{fidelity}\n",
        text=True,
        capture_output=False,
        timeout=600,  # 10 min max per run
    )

if __name__ == "__main__":
    for fidelity in ["LOW", "HIGH"]:
        run_once(fidelity)
        time.sleep(30)  # 30s between runs