# GM Seed/Key Toolkit

A Simple Python written calculator for 2 byte Seed and Keys. Works by giving it a seed and algorithm or brute-forcing all algorithms for matching key. Mostly for GM Global A but has functionality for older Class2. 2 Entry points:

- `gmseedcalc.py` — a pure-Python interpreter for the recovered ECU opcode tables plus helpers for brute-force analysis.
- `gmseedcalc_gui.py` — a PyQt5 desktop utility that wraps the interpreter with a friendlier workflow, including brute-force enumeration, copy-to-clipboard, and table selection.

## Table of Contents

1. [Features](#features)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Understanding the Algorithms](#understanding-the-algorithms)
   - [Opcode Tables](#opcode-tables)
   - [Interpreter Flow](#interpreter-flow)
   - [Opcode Semantics](#opcode-semantics)
   - [Reverse Engineering Workflow](#reverse-engineering-workflow)
5. [Usage](#usage)
   - [CLI Helpers](#cli-helpers)
   - [PyQt5 GUI](#pyqt5-gui)
6. [Troubleshooting](#troubleshooting)
7. [License](#license)

## Features

- Faithful implementation of the ECU "seed → key" bytecode, including byte swaps, rotations, bitwise masks, and conditional arithmetic opcodes.
- Three recovered algorithm tables: `table_gmlan`, `table_others`, and `table_class2`, covering contemporary GMLAN, mixed protocol, and legacy Class 2 vehicles.
- Brute-force helper that prints the first algorithm slot mapping a supplied seed to a known key.
- Step-by-step tracer that logs every intermediate WORD so you can compare against hardware captures.
- Cross-platform PyQt5 GUI with seed/algo inputs, brute-force checkbox, table selector, and copy-to-clipboard button.

## Prerequisites

- **Python 3.10+** (tested with 3.10.7 via the included virtual environment).
- **PyQt5** for the GUI (`pip install pyqt5`).
- A hex seed and, optionally, a target key/algorithm index supplied by the ECU or capture tool.

## Installation

```powershell
# Clone or copy the repository contents
cd C:\path\to\gmseedcalc

# (Optional) create & activate a virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install GUI dependency
pip install pyqt5
```

## Understanding the Algorithms

### Opcode Tables

ECU firmware stores each response algorithm as 13 bytes: four repetitions of `(opcode, hh, ll)` followed by a single unused pad byte. The project includes three tables (`table_gmlan`, `table_others`, `table_class2`), each 3,328 bytes long (256 algorithms * 13 bytes). `gmseedcalc.py` loads these tuples into contiguous `ctypes` arrays so the interpreter can index them like the ROM.

### Interpreter Flow

`get_key(seed, algo, table)` replicates the firmware dispatcher:

1. Multiply the algorithm index by 13 to locate its first opcode triple.
2. Iterate four times, reading `code`, `hh`, and `ll` out of the table.
3. Map the opcode byte to a helper such as `op_05` (byte swap) or `op_4c` (left rotate).
4. Feed the current 16-bit accumulator (`WORD`) through the helper, update the seed, and advance 3 bytes.
5. Return the final WORD; this is the response key the ECU expects for the provided seed.

Algorithm `0` is a special case that simply bitwise-NOTs the seed.

### Opcode Semantics

Each helper mirrors a ROM instruction. Highlights:

| Opcode | Helper  | Description |
|--------|---------|-------------|
| `0x05` | `op_05` | Swap high/low bytes. |
| `0x14` | `op_14` | Add literal formed by `hh:ll`. |
| `0x2A` | `op_2a` | Ones-complement and optionally increment when `hh < ll`. |
| `0x37` | `op_37` | Mask accumulator with `ll<<8 | hh`. |
| `0x4C` | `op_4c` | Rotate left by `hh` bits (ECU ignores `ll`). |
| `0x6B` | `op_6b` | Rotate right by `ll` bits. |
| `0x75` | `op_75` | Add literal built as `ll:hh` (byte order reversed from `0x14`). |
| `0x7E` | `op_7e` | Swap bytes, then add via `op_14` or `op_75` depending on `hh >= ll`. |
| `0x98` | `op_98` | Subtract literal `hh:ll`. |
| `0xF8` | `op_f8` | Subtract literal `ll:hh`. |

`gmseedcalc.py` documents every helper so you can extend or audit them quickly.

### Reverse Engineering Workflow

Use `reverse_engineer_algorithm(seed_hex, target_key_hex)` when you know a seed/key pair. but not the underlying algorithm number. The helper:

1. Converts the seed/key from hex into integers once.
2. Iterates algorithm slots (default 1–255) and runs `get_key` for each.
3. Compares the interpreter output to the provided key.
4. Logs the matching algorithm, prints its opcode triples via `extract_opcode_sequence`, and returns the data so you can run `test_algorithm_step_by_step` for deeper inspection.

`test_algorithm_step_by_step` mirrors `get_key` but prints each `code/hh/ll`, a human-readable description, and the accumulator after the operation—ideal for verifying your port against USB traces or emulator logs.

## Usage

### CLI Helpers

1. **Find an algorithm that matches a known seed/key pair**:
   ```powershell
   py gmseedcalc.py
   # Edit the hard-coded call inside __main__ or import the module elsewhere:
   # from gmseedcalc import reverse_engineer_algorithm
   # reverse_engineer_algorithm("0102", "5B7E")
   ```

2. **Step through an algorithm**:
   ```python
   from gmseedcalc import test_algorithm_step_by_step, table_gmlan
   test_algorithm_step_by_step("0102", 238, table_gmlan)
   ```

### PyQt5 GUI

```
py gmseedcalc_gui.py
```

GUI workflow:

1. Enter a seed in hex (e.g., `0102`).
2. Choose the opcode table (GMLAN/Other/Class2).
3. Either type an algorithm number **or** check **Brute force all** to compute every slot.
4. Click **Calculate**.
5. Copy the resulting key using the **Copy** button or select text from the brute-force pane.

When brute force is checked, the algorithm field disables and the right-hand pane lists `Algo XXX: 0xYYYY` for every valid slot, enabling quick filtering in Excel or other tooling.

## Troubleshooting

- **"Algorithm index is out of range"** — The table you selected does not contain that many algorithms. Switch tables or lower the number.
- **No matching algorithm found** — Verify the seed/key pair, the table (GMLAN vs Class2), and the captured direction (some captures reverse seed/key ordering).
- **GUI does not start** — Ensure PyQt5 is installed in the active environment and that you are running a supported Python build.
- **Clipboard copy fails** — Calculate a key first; the Copy button validates that output is non-empty before touching the clipboard.

## License

This repository is provided for educational and diagnostic purposes. 