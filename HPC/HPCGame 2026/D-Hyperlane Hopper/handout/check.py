# check for output

# *.out vs *.base.out
# hexadecimal comparison

import os


for i in range(1, 8):
    out_file = f"{i}.out"
    base_file = f"{i}.base.out"

    if not os.path.exists(out_file):
        print(f"Output file {out_file} does not exist.")
        continue

    if not os.path.exists(base_file):
        print(f"Base file {base_file} does not exist.")
        continue

    with open(out_file, "rb") as f_out, open(base_file, "rb") as f_base:
        out_data = f_out.read()
        base_data = f_base.read()

        if out_data == base_data:
            print(f"Test {i}: PASS")
        else:
            print(f"Test {i}: FAIL")
