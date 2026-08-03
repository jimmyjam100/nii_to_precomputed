"""
Write a Neuroglancer precomputed "segment_properties" sidecar (label
names) and a companion segment-color JSON snippet, from a FreeSurfer-style
LUT.

Author: Matthieu Chourrout
License: Apache-2.0
"""

import json
import logging
import os
from typing import Dict

import numpy as np

from nii_to_precomputed.utils import LUTEntry


def write_segment_properties(
    output_dir: str,
    lut: Dict[int, LUTEntry],
    present_ids: np.ndarray,
) -> None:
    """
    Write ./segment_properties/info under output_dir, containing the names
    (as the "label" property) for every label id present in the volume
    that has a LUT entry. IDs without a LUT entry fall back to their
    numeric string. Also writes segment_colors.json, a plain
    {id: "#rrggbb"} map (for pasting into a Neuroglancer layer's
    "segmentColors") since segment_properties itself has no color type.

    Parameters
    ----------
    output_dir : str
        The precomputed layer's root directory.
    lut : dict[int, LUTEntry]
        Label id -> (name, rgba) mapping.
    present_ids : np.ndarray
        The label ids actually present in the volume (background/0
        excluded by the caller if desired).
    """
    ids = [int(i) for i in present_ids]
    labels = [lut[i].name if i in lut else str(i) for i in ids]

    info = {
        "@type": "neuroglancer_segment_properties",
        "inline": {
            "ids": [str(i) for i in ids],
            "properties": [
                {"id": "label", "type": "label", "values": labels}
            ],
        },
    }

    prop_dir = os.path.join(output_dir, "segment_properties")
    os.makedirs(prop_dir, exist_ok=True)
    with open(os.path.join(prop_dir, "info"), "w") as f:
        json.dump(info, f)
    logging.info("Wrote segment_properties for %d labels", len(ids))

    colors = {
        str(i): "#{:02x}{:02x}{:02x}".format(*lut[i].rgba[:3])
        for i in ids if i in lut
    }
    with open(os.path.join(output_dir, "segment_colors.json"), "w") as f:
        json.dump(colors, f, indent=2)
    logging.info("Wrote segment_colors.json (paste into a layer's "
                 "\"segmentColors\" to restore LUT colors)")
