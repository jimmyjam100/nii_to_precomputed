"""
Load a .nii/.nii.gz volume and determine its target Neuroglancer
precomputed layer type.

Author: Matthieu Chourrout
License: Apache-2.0
"""

import logging
import os
from typing import Tuple

import nibabel as nib
import numpy as np
from nibabel.affines import voxel_sizes as _voxel_sizes

SEGMENTATION_DTYPE_KINDS = ("u", "i")  # unsigned/signed integer
SEGMENTATION_MAX_UNIQUE_RATIO = 0.01  # unique-values / voxel-count threshold
SEGMENTATION_FILENAME_HINTS = ("dseg", "seg", "label", "parcellation", "aseg", "aparc")


def load_nifti(nii_file: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Load a NIfTI volume.

    Parameters
    ----------
    nii_file : str
        Path to the .nii/.nii.gz file.

    Returns
    -------
    data : np.ndarray
        3D (or 4D with a trailing channel axis) array, in its native dtype.
    affine : np.ndarray
        4x4 voxel-to-world (RAS mm) affine.
    voxel_sizes_mm : np.ndarray
        Per-axis voxel size in mm, derived from the affine.
    """
    logging.info("Loading %s", nii_file)
    img = nib.load(nii_file)
    data = np.asarray(img.dataobj)
    affine = img.affine
    voxel_sizes_mm = _voxel_sizes(affine)
    logging.info("Shape: %s, dtype: %s, voxel sizes (mm): %s",
                  data.shape, data.dtype, voxel_sizes_mm)
    return data, affine, voxel_sizes_mm


def detect_layer_type(nii_file: str, data: np.ndarray) -> str:
    """
    Heuristically decide whether a volume should become a Neuroglancer
    "segmentation" or "image" layer.

    A volume is treated as a segmentation if its dtype is integral AND
    either the filename hints at a parcellation/segmentation (dseg, seg,
    label, ...) or the number of distinct values is small relative to the
    number of voxels (typical of discrete label maps vs. continuous
    intensity data).

    Parameters
    ----------
    nii_file : str
        Path to the source file (used for filename-based hints).
    data : np.ndarray
        The loaded volume.

    Returns
    -------
    str
        "segmentation" or "image".
    """
    basename = os.path.basename(nii_file).lower()
    if any(hint in basename for hint in SEGMENTATION_FILENAME_HINTS):
        return "segmentation"

    if data.dtype.kind not in SEGMENTATION_DTYPE_KINDS:
        return "image"

    n_unique = len(np.unique(data))
    if n_unique / data.size <= SEGMENTATION_MAX_UNIQUE_RATIO:
        return "segmentation"

    return "image"
