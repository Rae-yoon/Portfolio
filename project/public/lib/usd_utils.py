#!/usr/bin/python


"""usd_utils.py

Utility API for working with USD files.

Key Features:
    - UsdUtils class: Provides static methods for opening and caching USD stages and Sdf layers.
        - _get_usd_stage: Lazily open and cache a USD stage from a given file path.
        - _get_usd_sdf_layer: Lazily open and cache a USD Sdf layer from a given file path.

Notes:
    Both methods use LRU caching to avoid repeated expensive loads of USD data.

Author: Raeyoon Kim
Created: 2025-08-21
"""


from __future__ import annotations
from functools import lru_cache


class UsdUtils:
    '''Provides static methods for working with USD.
    
    Notes:
        Provides cached access to USD to avoid repeated expensive loads.
    '''
    @staticmethod
    @lru_cache(maxsize=64)
    def _get_usd_stage(path: str) -> pxr.Usd.Stage:
        """Return a cached USD stage.

        Notes:
            Lazily opens and caches a USD stage from the given file path.

        Args:
            path (str): Path to a USD file.

        Returns:
            pxr.Usd.Stage: The opened USD stage
        """
        from pxr import Usd
        stage = Usd.Stage.Open(path)
        return stage

    @staticmethod
    @lru_cache(maxsize=64)
    def _get_usd_sdf_layer(path: str) -> pxr.Sdf.Layer:
        """Return a cached USD Sdf layer.

        Notes:
            Lazily opens and caches an Sdf layer from the given file path.

        Args:
            path (str): Path to a USD file.

        Returns:
            pxr.Sdf.Layer: The opened Sdf layer.
        """
        from pxr import Sdf
        layer = Sdf.Layer.FindOrOpen(path)
        return layer