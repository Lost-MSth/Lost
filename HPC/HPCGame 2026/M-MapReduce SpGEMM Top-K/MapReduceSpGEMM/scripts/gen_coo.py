#!/usr/bin/env python3
import argparse
from pathlib import Path
from typing import Optional

try:
    import numpy as np
except ImportError as exc:
    raise SystemExit("numpy is required for fast generation. Install via 'pip install numpy'") from exc


def stream_generate_and_write(rows: int,
                              cols: int,
                              density: float,
                              parts: int,
                              out_dir: Path,
                              rng: np.random.Generator,
                              max_nnz_per_row: Optional[int]) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    handles = [ (out_dir / f"part-{idx:05d}").open("w") for idx in range(parts) ]

    nnz_per_row = max(1, int(cols * density)) if max_nnz_per_row is None else min(max_nnz_per_row, cols)
    total = 0

    for r in range(rows):
        k = min(nnz_per_row, cols)
        cols_chosen = rng.choice(cols, size=k, replace=False)
        vals = rng.uniform(0.1, 1.0, size=k)
        target = r % parts
        fh = handles[target]
        for c, v in zip(cols_chosen, vals):
            fh.write(f"{r} {int(c)} {v:.6f}\n")
        total += k

    for fh in handles:
        fh.close()
    return total


def main():
    parser = argparse.ArgumentParser(description="Generate sparse matrices A (M x K) and B (K x N) in COO.")
    parser.add_argument("--M", type=int, required=True, help="Rows of A / output rows")
    parser.add_argument("--K", type=int, required=True, help="Inner dimension")
    parser.add_argument("--N", type=int, required=True, help="Cols of B / output cols")
    parser.add_argument("--densityA", type=float, default=0.01, help="Density for A (0-1)")
    parser.add_argument("--densityB", type=float, default=0.01, help="Density for B (0-1)")
    parser.add_argument("--parts", type=int, default=4, help="Number of part files per matrix")
    parser.add_argument("--max_nnz_per_row", type=int, default=None, help="Optional cap per row to avoid huge densities")
    parser.add_argument("--seed", type=int, default=42, help="PRNG seed")
    parser.add_argument("--out", type=str, default="data", help="Output base directory")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt if estimates look big")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)

    out_base = Path(args.out)

    est_per_row_a = min(args.K, args.max_nnz_per_row or max(1, int(args.K * args.densityA)))
    est_per_row_b = min(args.N, args.max_nnz_per_row or max(1, int(args.N * args.densityB)))
    total_nnz_est_a = args.M * est_per_row_a
    total_nnz_est_b = args.K * est_per_row_b

    def pretty(n):
        if n >= 1e9:
            return f"{n/1e9:.2f}B"
        if n >= 1e6:
            return f"{n/1e6:.2f}M"
        if n >= 1e3:
            return f"{n/1e3:.2f}K"
        return str(n)

    print("=== Estimate ===")
    print(f"A: rows={args.M} cols={args.K} nnz/row~{est_per_row_a} total~{pretty(total_nnz_est_a)}")
    print(f"B: rows={args.K} cols={args.N} nnz/row~{est_per_row_b} total~{pretty(total_nnz_est_b)}")
    total_bytes_txt = (total_nnz_est_a + total_nnz_est_b) * 20  # rough bytes when saved as text
    print(f"Approx text size: {pretty(total_bytes_txt)} bytes (very rough)")

    hard_cap = 5_000_000_00  # 500M
    if total_nnz_est_a > hard_cap or total_nnz_est_b > hard_cap:
        print("Warning: estimated nnz exceeds hard cap; generation aborted.")
        raise SystemExit("Lower density or set --max_nnz_per_row.")

    if not args.yes:
        reply = input("Proceed with generation? [y/N]: ").strip().lower()
        if reply not in ("y", "yes"):
            raise SystemExit("Aborted by user.")

    nnzA = stream_generate_and_write(args.M, args.K, args.densityA, args.parts, out_base / "A", rng, args.max_nnz_per_row)
    nnzB = stream_generate_and_write(args.K, args.N, args.densityB, args.parts, out_base / "B", rng, args.max_nnz_per_row)

    print(f"Wrote A nnz={nnzA} to {out_base / 'A'}")
    print(f"Wrote B nnz={nnzB} to {out_base / 'B'}")


if __name__ == "__main__":
    main()
