"""Regenerate the synthetic sample dataset in data/sample/."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from introspect.synthetic import generate  # noqa: E402

if __name__ == "__main__":
    out = generate(Path(__file__).resolve().parent.parent / "data" / "sample")
    print("Sample data written to", out)
