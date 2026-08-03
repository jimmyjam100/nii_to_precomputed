"""
Build a Neuroglancer precomputed CloudVolume (image or segmentation) from
an in-memory volume array and write the data into it.

Author: Matthieu Chourrout
License: Apache-2.0
"""

import logging
from typing import List, Optional

import numpy as np
from cloudvolume import CloudVolume

NM_PER_MM = 1_000_000


def make_cloudvolume(
    output_dir: str,
    data: np.ndarray,
    voxel_sizes_mm: np.ndarray,
    layer_type: str,
    chunk_size: List[int] = [64, 64, 64],
    encoding: str = "raw",
    with_mesh: bool = False,
    with_segment_properties: bool = False,
) -> CloudVolume:
    """
    Create (and commit the info for) a Neuroglancer precomputed
    CloudVolume matching the given array.

    Parameters
    ----------
    output_dir : str
        Destination directory (or "gs://"/"s3://" URL) for the precomputed
        layer.
    data : np.ndarray
        3D volume array; its shape and dtype drive volume_size/data_type.
    voxel_sizes_mm : np.ndarray
        Per-axis voxel size in mm; converted to nm for CloudVolume's
        "resolution" field.
    layer_type : str
        "segmentation" or "image".
    chunk_size : list[int]
        Precomputed chunk size (x, y, z), in voxels.
    encoding : str
        CloudVolume encoding (e.g. "raw", "jpeg", "compresso",
        "compressed_segmentation").
    with_mesh : bool
        Whether to register a "mesh" subdirectory in the info (only
        meaningful for layer_type="segmentation"; mesh generation itself
        happens separately via meshing.build_meshes).
    with_segment_properties : bool
        Whether to reference a "segment_properties" subdirectory in the
        info (only meaningful for layer_type="segmentation"; the
        directory itself is written separately via
        segment_properties.write_segment_properties).

    Returns
    -------
    CloudVolume
        The opened volume, with info already committed (data not yet
        written -- see write_volume).
    """
    resolution_nm = (np.asarray(voxel_sizes_mm) * NM_PER_MM).tolist()

    info = CloudVolume.create_new_info(
        num_channels=1,
        layer_type=layer_type,
        data_type=str(data.dtype),
        encoding=encoding,
        resolution=resolution_nm,
        voxel_offset=[0, 0, 0],
        chunk_size=chunk_size,
        volume_size=data.shape[:3],
        mesh="mesh" if (with_mesh and layer_type == "segmentation") else None,
    )

    vol = CloudVolume(output_dir, info=info, progress=False, compress=False)
    if with_segment_properties and layer_type == "segmentation":
        vol.info["segment_properties"] = "segment_properties"
    vol.commit_info()
    logging.info("Committed CloudVolume info at %s", output_dir)
    return vol


def write_volume(vol: CloudVolume, data: np.ndarray) -> None:
    """Write a full 3D array into a CloudVolume (adds the channel axis)."""
    logging.info("Writing %s voxels...", data.shape)
    vol[:, :, :] = data[..., np.newaxis]
    logging.info("Done writing volume data.")
