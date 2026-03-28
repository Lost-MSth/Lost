"""Spawn and interact with prefill.py using stdin/stdout."""
import atexit
import pathlib
import subprocess
import sys
import threading
from queue import Queue, Empty

MODEL_PATH = "/data/models/Qwen3-32B"
DATASET_PATH = "/data/datasets/NuminaMath-CoT"

class PrefillClient:
    """Lightweight wrapper around a running prefill.py process."""

    def __init__(self, filename) -> None:
        script = pathlib.Path(__file__).with_name(filename)
        if not script.exists():
            raise FileNotFoundError(f"prefill.py not found at {script}")

        self._proc = subprocess.Popen(
            [sys.executable, str(script), "--model", MODEL_PATH],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        if self._proc.stdin is None or self._proc.stdout is None:
            raise RuntimeError("Failed to open pipes to prefill.py")

        self._stdout_queue: Queue[str] = Queue()
        self._stdout_thread = threading.Thread(
            target=self._pump_stdout,
            name="prefill-stdout",
            daemon=True,
        )
        self._stdout_thread.start()

        atexit.register(self.close)

    def _pump_stdout(self) -> None:
        # Keep reading lines so reads are non-blocking for callers.
        for line in self._proc.stdout:  # type: ignore[union-attr]
            self._stdout_queue.put(line.rstrip("\n"))

    def write(self, data: str, *, end: str = "\n") -> None:
        if self._proc.stdin is None:
            raise RuntimeError("stdin is unavailable")
        self._proc.stdin.write(f"{data}{end}")
        self._proc.stdin.flush()

    def read(self) -> str:
        while True:
            if self._proc.poll() is not None:
                raise RuntimeError("prefill.py process has terminated")
            try:
                return self._stdout_queue.get(timeout=1)
            except Empty:
                pass

    def close(self) -> None:
        for line in self._proc.stderr or []:
            print(f"prefill.py stderr: {line.rstrip()}", file=sys.stderr)
        
        if self._proc.poll() is None:
            self._proc.terminate()
        try:
            self._stdout_thread.join(timeout=0.2)
        except RuntimeError:
            pass


from transformers import AutoTokenizer
from datasets import load_dataset
import time
import random
import json
import os

if __name__ == "__main__":
    random.seed(42) # 评测时会改变随机种子
    os.environ["FLASH_ATTENTION_TRITON_AMD_ENABLE"] = "TRUE"
    N = 100 
    dataset = load_dataset(DATASET_PATH)["train"]
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    text_input = []
    while True:
        messages = random.choice(dataset)["messages"]
        input = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=False
        )
        if len(input) < 2048:
            text_input.append(input)
        if len(text_input) >= N:
            break

    client = PrefillClient("prefill.py")
    if client.read() != "ready":
        print("prefill.py did not signal readiness")
        sys.exit(1)

    start = time.time()
    client.write(json.dumps(text_input))

    for i in range(N):
        try:
            print(client.read())
        except Exception as e:
            print(f"Error reading output for input {i}: {e}")
            sys.exit(1)
    print(f"total time: {time.time() - start}")
    client.close()
