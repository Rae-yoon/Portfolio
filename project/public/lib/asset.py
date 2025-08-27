#!/usr/bin/python


"""asset.py

Utility API for managing server and flow assets, including USD assets.

Key Features:
    - FlowAssets class: Connects to flow and manages assets.
    - AssetLib class: Provides server-side asset management.
    - UsdAssets class: Manages USD assets. (Inherits from AssetLib)

Author: Raeyoon Kim
Created: 2025-08-21
"""


from __future__ import annotations
from typing import Union
from lib.log import LogBus
import os, re, bisect
from shotgun_api3 import Shotgun
from usd_utils import UsdUtils
from functools import lru_cache
from dotenv import load_dotenv


class FlowAssets:    
    """Provides methods to fetch asset information from Flow/Shotgun.
    
    Attributes:
        log (QLogger) : Worker to logging.
        sg (Shotgun): Flow API instance. Defaults to None.
        base_filter (list): Flow project's id filter.
    """
    
    def __init__(self, sg: Shotgun = None):
        self.log = LogBus.instance().get_worker(__name__)
        self.sg = sg
        if not sg:
            try:
                configEnv = os.path.join(os.environ['base_config'], '.flow.env')
                load_dotenv(configEnv)
                self.base_filter = ['project','is',{'type':'Project', 'id': os.getenv('PRJ_ID')}]
                self.sg = Shotgun(os.getenv('flow_url'), script_name=os.getenv('ASSET_ID'), api_key=os.getenv('ASSET_PW'))
            except:
                self.sg = None
                self.log.warning('failed flow connect')

    def get_asset_data_by_asset_names(self, asset_names: list = [], asset_type_names: dict = {}) -> list[dict]:
        """Retrieve asset data from Flow by asset names or asset type mapping.

        Args:
            asset_names (list[str], optional): List of asset names to query.
            asset_type_names (dict[str, str], optional): Mapping of asset type names by asset name.

        Returns:
            list[dict]: Asset data records from Flow.
        """
        asset_filters = [self.base_filter]
        if all([not asset_names, asset_type_names]):
            asset_names = list(asset_type_names.keys())
        asset_filters.append(['code','in', asset_names])
        asset_data = self.sg.find('Asset', asset_filters, ['code','sg_asset_type'])
        return asset_data

    def get_asset_type_names_from_flow(self, asset_names: list[str] = [], names_by_types: bool = False) -> dict:
        """Get asset type names from Flow for given assets.

        Args:
            asset_names (list[str], optional): List of asset names. Defaults to [].
            names_by_types (bool): If True, group names by asset type. Defaults to False.

        Returns:
            dict: Mapping of asset name to type, or type to asset names.
        """
        asset_type_names = {}
        if asset_names:
            asset_data = self.get_asset_data_by_asset_names(asset_names=asset_names)
            if asset_data:
                for asset in asset_data:
                    asset_name = asset['code']
                    asset_type = asset['sg_asset_type']
                    if names_by_types:
                        if asset_type_names.get(asset_type, None):
                            bisect.insort(asset_type_names[asset_type], asset_name)
                        else:
                            asset_type_names[asset_type] = [asset_name]
                    else:
                        asset_type_names[asset_name] = asset_type
        return asset_type_names

    def get_asset_page_link(self, code: str = '') -> Union[str, None]:
        """Build Flow asset page link by code.

        Args:
            code (str): Asset code. Defaults to ''.

        Returns:
            Union[str, None]: Page link if found, else None.
        """
        page='Asset'
        target_id = self.get_target_id(page=page, code=code)
        if target_id:
            filters = [self.base_filter]
            filters.append(['name', 'is', page+'s'])
            page_data = self.sg.find_one('Page',filters,['name'])
            if page_data:
                return f"{os.getenv('flow_url')}/page/{page_data.get('id')}#{page}_{target_id}"
        

    def get_target_id(self, page: Union[str, None], code: Union[str, None]) -> Union[int, None]:
        """Get target entity ID from Flow.

        Args:
            page (Union[str, None]): Page name (e.g., 'Asset').
            code (Union[str, None]): Asset code.

        Returns:
            Union[int, None]: Target entity ID if found. else None.
        """
        filters = []
        filters.append(['code','is',code])
        target = self.sg.find_one(page, filters, [])
        if target:
            return target['id']       


class AssetLib:
    """Provides utility methods for asset versioning and asset type management.

    Attributes:
        log (QLogger): Worker logger instance.
    """    
    def __init__(self):
        self.log = LogBus.instance().get_worker(__name__)

    def get_version(self, path: str = '') -> Union[str, None]:
        try:
            if os.path.exists(path):
                return os.readlink(path)
        except Exception as e:
            self.log.debug('%s',e)

    @staticmethod
    @lru_cache(maxsize=1024)
    def get_max_version(path_dir: str = '') -> Union[str, dict[str, str]]:
        """Find maximum version from directory filenames.

        Args:
            path_dir (str, optional): Directory path.

        Returns:
            str: Max version string.
            dict[str, str]: Error information if exception occurs.
        """
        try:
            max_version = 'v' + str(max([int(m.group(1)) for m in [re.search(r'v(\d+)', x) for x in os.listdir(path_dir)] if m])).zfill(3)
            return max_version
        except Exception as e:
            return {'error':str(e)}

    @staticmethod
    @lru_cache(maxsize=2048)
    def get_asset_type_names(asset_names: tuple = (), names_by_types: bool = False) -> dict[str, Union[str, list[str]]]:
        """Resolve asset type names from directory structure.

        Args:
            asset_names (tuple[str, ...], optional): Asset names. It must be a tuple cause it's using cache.
            names_by_types (bool, optional): If True, group names by type.

        Returns:
            dict[str, Union[str, list[str]]]: Mapping of asset name to type, or type to asset names.
        """
        asset_type_names = {}
        
        for asset_name in asset_names:        
            path_asset_char = os.path.join(os.environ['base_asset'], 'char', asset_name)
            path_asset_prop = os.path.join(os.environ['base_asset'], 'prop', asset_name)
            path_asset_dirs = [path_asset_char, path_asset_prop]
            for path_asset_dir in path_asset_dirs:
                if os.path.exists(path_asset_dir):
                    asset_type = os.path.basename(os.path.dirname(path_asset_dir))
                    if names_by_types:
                        if asset_type_names.get(asset_type, None):
                            bisect.insort(asset_type_names[asset_type], asset_name)
                        else:
                            asset_type_names[asset_type] = [asset_name]
                    else:
                        asset_type_names[asset_name] = asset_type
                    break
        return asset_type_names
            
    def get_asset_info(
        self,
        asset_type: str = '',
        asset_name: str = '',
        seq: str = '',
        shot: str = ''
    ) -> dict[str, str]:
        """Collect asset version info from model and asset directories.

        Args:
            asset_type (str): Asset type. Defaults to ''.
            asset_name (str): Asset name. Defaults to ''.
            seq (str): Sequence name. Defaults to ''.
            shot (str): Shot name. Defaults to ''.

        Returns:
            dict[str, str]: Asset information including versions.
        """
        path_model = os.path.join(os.environ['base_model'], seq, shot, asset_name, 'current')
        path_stable = os.path.join(os.environ['base_asset'], asset_type, asset_name, 'stable')
        path_latest = os.path.join(os.environ['base_asset'], asset_type, asset_name, 'latest')
        asset_info = {}
        
        model_ver = self.get_version(path=path_model)
        model_ver_max = self.get_max_version(path_dir=os.path.dirname(path_model))
        stable = self.get_version(path=path_stable)
        latest = self.get_version(path=path_latest)

        if model_ver:
            asset_info['model_current'] = model_ver

        if type(model_ver_max) == dict:
            self.log.exception('%s', model_ver_max.get('error','can not catch error logs'))
        else:
            asset_info['model_max'] = model_ver_max

        if stable:
            asset_info['asset_stable'] = stable
            
        if latest:
            asset_info['asset_latest'] = latest
        
        return asset_info
    
    
class UsdAssets(AssetLib):
    """Extends AssetLib with USD-specific utilities.

    Base Classes:
        AssetLib: Class to handle general assets.
    """
    
    def __init__(self):
        super().__init__()
    
    def get_dependencies(self, path_usd: str = '') -> list[str]:
        """Collect dependencies (layer file paths) from a USD stage.

        Args:
            path_usd (str): USD file path. Defaults to ''.

        Returns:
            list[str]: List of dependency file paths.
        """
        path_usd = os.path.abspath(path_usd)
        self.log.info('path_usd : %s', path_usd)
        stage = UsdUtils._get_usd_stage(path=path_usd)
        if not stage:
            self.log.exception('failed to open stage: %s', path_usd)
            return []

        layers = stage.GetUsedLayers()
        dependencies = set()

        for layer in layers:
            path_real = layer.realPath
            if path_real and os.path.exists(path_real):
                dependencies.add(os.path.abspath(path_real))
        return sorted(dependencies)

    def get_prim_data(self, path: str = '') -> list[dict[str, str]]:
        """Extract prim data from USD stage.

        Args:
            path (str): USD file path. Defaults to ''.

        Returns:
            list[dict[str, str]]: List of prim metadata.
        """
        prim_data = []
        if path:
            stage = UsdUtils._get_usd_stage(path=path)
            if not stage:
                self.log.exception('failed to open stage: %s', path)
                return

            for prim in stage.Traverse():
                if prim.IsActive():
                    try:
                        asset_data = {}         
                        pathRefers = prim.GetMetadata("references").GetAddedOrExplicitItems()
                        if pathRefers:
                            for pathRefer in pathRefers:
                                originName = pathRefer.assetPath.split('/')[3]
                                asset_data['origin_name'] = originName
                        else:
                            asset_data['origin_name'] = prim.GetName()

                        if asset_data:
                            prim_data.append(asset_data)
                    except:
                        # self.log.debug('prim does not active : %s', prim)
                        continue
        
        return prim_data

    def get_assets_from_usds(self, seq: str = '', shot: str = '') -> list[dict[str, str]]:
        """Collect asset data from USD shot file.

        Args:
            seq (str): Sequence name. Defaults to ''.
            shot (str): Shot name. Defaults to ''.

        Returns:
            list[dict[str, str]]: Asset data collected from USDs.
        """
        assets = []   
        path_usdShot = os.path.join(os.environ['base_shot'], seq, shot, 'shot.usd')      
        if os.path.exists(path_usdShot):
            self.log.info('Get assets from USD : %s', path_usdShot)
            dependencies = self.get_dependencies(path_usdShot)
            if dependencies:
                for path in dependencies:
                    prim_data = self.get_prim_data(path=path)
                    if prim_data: 
                        assets.extend(prim_data)
        else:
            self.log.warning('this path does not exists : %s', path_usdShot)
        return assets
    
    def get_custom_layer_data(
        self,
        path_usd: str = '',
        asset_info: dict = {},
        key: str = 'post_process'
    ) -> dict:
        """Extract custom layer data from USD file.

        Args:
            path_usd (str): USD file path. Defaults to ''.
            asset_info (dict): Asset info to update. Defaults to {}.
            key (str): Key to fetch from customLayerData. Defaults to 'post_process'.

        Returns:
            dict: Updated asset info with custom layer data.
        """
        if path_usd:
            if os.path.exists(path_usd):
                layer = UsdUtils._get_usd_sdf_layer(path_usd)
                if layer and layer.customLayerData:
                    data = layer.customLayerData.get(key,None)
                    if data:
                        asset_info[key] = data
            else:
                self.log.warning('this path does not exists : %s', path_usd)
                self.log.debug('key : %s | asset_info : %s', key, asset_info)
        return asset_info

    def get_asset_data_with_type(
        self,
        seq: str = '',
        shot: str = '',
        assets: list[dict[str, str]] = [],
        asset_type_names: dict[str, str] = {}
    ) -> dict[str, list[dict[str, dict[str, str]]]]:
        """Collect asset data grouped by type, enriched with version and USD info.

        Args:
            seq (str): Sequence name. Defaults to ''.
            shot (str): Shot name. Defaults to ''.
            assets (list[dict[str, str]]): Asset metadata list. Defaults to [].
            asset_type_names (dict[str, str]): Mapping of asset names to types. Defaults to {}.

        Returns:
            dict[str, list[dict[str, dict[str, str]]]]: Asset data grouped by type.
        """
        asset_data = {}
        asset_name_done = []
        
        if assets:            
            for asset in assets:
                asset_name = asset.get('origin_name',None)  
                asset_type = asset_type_names.get(asset_name,None)
                if all([asset_name, asset_type]):
                    asset_info = {}                       
                    asset_info = self.get_asset_info(seq=seq, shot=shot, asset_name=asset_name, asset_type=asset_type) 
                    if asset_info:
                        path_modelUsd = os.path.join(os.environ['base_model'], seq, shot, asset_name, 'current', asset_name+'.usd')
                        asset_info = self.get_custom_layer_data(path_usd=path_modelUsd, asset_info=asset_info)
                        if asset_data.get(asset_type, None):       
                            if asset_name not in asset_name_done:    
                                asset_data[asset_type].append({asset_name:asset_info}) 
                        else:
                            asset_data[asset_type]= [{asset_name:asset_info}]
                        asset_name_done.append(asset_name)
                    else:
                        self.log.debug('no asset_info : %s|%s|%s|%s', seq, shot, asset_name, asset_type)
        return asset_data
