"""
Build meshes for a Neuroglancer precomputed segmentation layer using
igneous, run locally (no distributed task queue required).

Author: Matthieu Chourrout
License: Apache-2.0
"""

import logging
from typing import List, Optional

import igneous.task_creation as tc
from taskqueue import LocalTaskQueue


def build_meshes(
    output_dir: str,
    mip: int = 0,
    shape: List[int] = [448, 448, 448],
    simplification: bool = True,
    max_simplification_error: float = 40.0,
    dust_threshold: Optional[int] = None,
    parallel: int = 1,
) -> None:
    """
    Generate per-label meshes (and the unsharded mesh manifest) for a
    segmentation layer that has already had its volume data written.

    Parameters
    ----------
    output_dir : str
        The precomputed segmentation layer's root directory (must already
        declare a "mesh" key in its info, see layer.make_cloudvolume).
    mip : int
        Mip level of the volume to mesh (0 = full resolution).
    shape : list[int]
        Task chunk shape in voxels; should be a multiple of the volume's
        chunk_size. The default covers small/medium volumes in one task.
    simplification : bool
        Whether to simplify mesh geometry.
    max_simplification_error : float
        Maximum simplification error, in nm.
    dust_threshold : int, optional
        Skip meshing objects with fewer than this many voxels.
    parallel : int
        Number of local worker processes.
    """
    logging.info("Building meshing tasks...")
    tq = LocalTaskQueue(parallel=parallel)

    meshing_tasks = tc.create_meshing_tasks(
        output_dir,
        mip=mip,
        shape=tuple(shape),
        simplification=simplification,
        max_simplification_error=max_simplification_error,
        dust_threshold=dust_threshold,
        progress=False,
    )
    tq.insert(meshing_tasks)
    tq.execute()
    logging.info("Meshing tasks complete.")

    logging.info("Building mesh manifest...")
    manifest_tasks = tc.create_mesh_manifest_tasks(output_dir)
    tq.insert(manifest_tasks)
    tq.execute()
    logging.info("Mesh manifest complete.")
