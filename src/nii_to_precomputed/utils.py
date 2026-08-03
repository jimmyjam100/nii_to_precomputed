"""
Utility functions: FreeSurfer-style LUT parsing and misc helpers.

Author: Matthieu Chourrout
License: Apache-2.0
"""

import os
from typing import Dict, NamedTuple, Optional


class LUTEntry(NamedTuple):
    name: str
    rgba: tuple  # (r, g, b, a), 0-255


def load_lut(path: str) -> Dict[int, LUTEntry]:
    """
    Parse a FreeSurfer-style label lookup table: lines of
    "<id> <name possibly with spaces> <r> <g> <b> <a>", blank lines and
    lines starting with "#" are ignored.

    Parameters
    ----------
    path : str
        Path to the LUT text file.

    Returns
    -------
    dict[int, LUTEntry]
        Mapping from label id to (name, rgba).
    """
    lut = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            tokens = line.split()
            if len(tokens) < 2:
                continue
            label_id = int(tokens[0])
            if len(tokens) >= 6:
                rgba = tuple(int(t) for t in tokens[-4:])
                name = " ".join(tokens[1:-4])
            else:
                rgba = (255, 255, 255, 255)
                name = " ".join(tokens[1:])
            lut[label_id] = LUTEntry(name=name, rgba=rgba)
    return lut


def find_sibling_lut(nii_file: str, lut_path: Optional[str] = None) -> Optional[str]:
    """
    Locate a LUT text file for a .nii/.nii.gz file.

    If lut_path is not given, looks for a same-basename .txt file next to
    nii_file (BIDS dseg.txt sidecar convention), e.g.
    "sub-01_dseg.nii.gz" -> "sub-01_dseg.txt". Returns None if neither is
    found.
    """
    if lut_path is not None:
        return lut_path
    base = nii_file
    for ext in (".nii.gz", ".nii"):
        if base.endswith(ext):
            base = base[: -len(ext)]
            break
    candidate = base + ".txt"
    if os.path.exists(candidate):
        return candidate
    return None
