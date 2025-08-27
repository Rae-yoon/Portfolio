#!/usr/bin/python


"""shot.py

Utility API for managing server and flow shots.

Key Features:
    - FlowShots class: Connects to flow and manages shots.
    - ShotLib class: General server-side shot management.

Author: Raeyoon Kim
Created: 2025-08-21
"""


from __future__ import annotations
from typing import Union
from lib.log import LogBus
import os, re, bisect
from shotgun_api3 import Shotgun
from functools import lru_cache
from dotenv import load_dotenv


class FlowShots:
    """Provides methods to interact with Flow/Shotgun for sequence and shot management.
    
    Attributes:
        log (QLogger) : Worker to logging.
        sg (Shotgun): Flow API instance. Defaults to None.
        base_filter (list): Flow project's id filter.
    """
    
    def __init__(self, sg=None):
        self.log = LogBus.instance().get_worker(__name__)
        self.sg = sg 
        if not self.sg:
            try:
                config_env = os.path.join(os.environ['base_config'], '.flow.env')
                load_dotenv(config_env)
                self.base_filter = ['project','is',{'type':'Project', 'id': os.getenv('PRJ_ID')}]
                self.sg = Shotgun(os.environ['flow_url'], script_name=os.getenv('SHOT_ID'), api_key=os.getenv('SHOT_PW'))
            except:
                self.sg = None
                self.log.warning('failed flow connect')
            
    def get_seqshots(self, omit: bool = False) -> dict:
        """Retrieve sequence and shots from Flow/Shotgun.

        Args:
            omit (bool): If False, exclude omitted shots. Defaults to False.

        Returns:
            dict: Dictionary of sequences and their shots.
        """
        shot_filters = [self.base_filter]
        if not omit:
            shot_filters.append(['sg_status_list', 'is_not', 'omt'])
        flow_shots = self.sg.find('Shot', shot_filters, ['sg_sequence', 'code', 'sg_status_list'])
        seqshots = {}
        if flow_shots:
            for flow_shot in flow_shots:
                try:
                    seq = flow_shot['sg_sequence']['name']
                    shot = flow_shot['code'].split('_')[-1]
                    if os.path.exists(os.path.join(os.environ['base_shot'], seq, shot)):
                        if seqshots.get(seq, None):
                            bisect.insort(seqshots[seq], shot)
                        else:
                            seqshots[seq] = [shot]
                except Exception as e:
                    self.log.error('%s',e)
                    continue

        seqshots = dict(sorted(seqshots.items(), key=lambda x: x[1]))
        seqshots = dict(sorted(seqshots.items(), key=lambda x: x[0]))
        return seqshots

    def get_shot(self, code: str = '') -> Union[dict, None]:
        """Retrieve a single shot from Flow/Shotgun.

        Args:
            code (str): Shot code to search. Defaults to ''.

        Returns:
            Union[dict, None]: Shot data if found, otherwise None.
        """
        shot_filter = [self.base_filter]
        shot_filter.append(['code','is', code])
        seq_or_shot = self.sg.find_one('Shot', shot_filter, ['code', 'assets'])
        return seq_or_shot

    def set_update_new_assets_on_flow(self, seq: str = '', shot: str = '', flow_assets: dict = {}) -> None:
        """ Update assets for a given shot in Flow/Shotgun.

        Args:
            seq (str): Sequence name. Defaults to ''.
            shot (str): Shot name. Defaults to ''.
            flow_assets (dict): Assets to update. Defaults to {}.
        """
        shot_code = seq + '_' + shot
        flow_shot = self.get_shot(code=shot_code)
        result = self.sg.update('Shot', flow_shot['id'], {'assets': flow_assets})
        self.log.info('\n** %s [assets] field has been Updated.\n', shot_code)
        
    def get_seqshot_page_link(self, seq: str = '', shot: str = '') -> Union[str, None]:
        """Generate a direct page link for a sequence or shot in Flow.

        Args:
            seq (str): Sequence name. Defaults to ''.
            shot (str): Shot name. Defaults to ''.

        Returns:
            Union[str, None]: URL link if available.
        """
        if shot:
            code = seq+'_'+shot
            page = 'Shot'
        else:
            code = seq
            page = 'Sequence'
            
        target_id = self.get_target_id(page=page, code=code)
        if target_id:
            filters = [self.base_filter]
            filters.append(['name', 'is', page+'s'])
            page_data = self.sg.find_one('Page',filters,['name'])
            if page_data:
                return f"{os.environ['flow_url']}/page/{page_data.get('id')}#{page}_{target_id}"
        
    def get_target_id(self, page: Union[str, None] = None, code: Union[str, None] = None) -> Union[int, None]:
        """Retrieve the ID of a target (sequence or shot).

        Args:
            page (Union[str, None]): Page type ('Shot' or 'Sequence').
            code (Union[str, None]): Code of the target.

        Returns:
            Union[int, None]: Target ID if found.
        """

        filters = []
        filters.append(['code','is',code])
        target = self.sg.find_one(page, filters, [])
        if target:
            return target['id']       


class ShotLib:
    """Provides utility methods for handling local shot sequences and shot structures.
    """    
    def __init__(self):
        pass

    @staticmethod
    @lru_cache(maxsize=1024)
    def get_seqshots(standardPublic: bool = True) -> dict:
        """Retrieve sequence and shot list from local storage.

        Args:
            standardPublic (bool): If True, use home path instead of public path. Defaults to True.

        Returns:
            dict: Dictionary of sequences and their shots.
        """
        path_standard = os.environ['base_shot']
        if not standardPublic:
            path_standard = path_standard.replace(os.environ['base_public'], os.environ['base_home'])
        seqshots = {}
        for seq in os.listdir(path_standard):
            if re.fullmatch(r's\d{4}', seq):
                path_seq_dir = os.path.join(path_standard, seq)
                shots = os.listdir(path_seq_dir)
                if shots:
                    for shot in shots:
                        if any([str.isdigit(shot), re.fullmatch(r'\d{4}_p\d{2}', shot)]):
                            if seqshots.get(seq, None):
                                bisect.insort(seqshots[seq], shot)
                            else:
                                seqshots[seq] = [shot]
        seqshots = dict(sorted(seqshots.items(), key=lambda x: x[1]))
        seqshots = dict(sorted(seqshots.items(), key=lambda x: x[0]))
        return seqshots
   
    def get_seqshots_as_txt(self, seqshots: dict = {}) -> str:
        """Convert sequence-shots dictionary into comma-separated text.

        Args:
            seqshots (dict): Dictionary of sequences and their shots. Defaults to {}.

        Returns:
            str: Comma-separated string of sequence_shot codes.
        """
        seqshots_txt = []
        for seq, shots in seqshots.items():
            for shot in shots:
                txt = seq + '_' + shot
                seqshots_txt.append(txt)
                
        return ', '.join(seqshots_txt)
        
    