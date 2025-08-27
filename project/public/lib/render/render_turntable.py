#!/usr/bin/python


"""render_turntable.py

Utilities for setting up and rendering turntables via Tractor.

Key Features:
    - TurntableRender class: Prepare the environment and submit a turntable render job to Tractor.
        - TurntableSh class: Generate a shell script to set up and execute turntable.py.
        - TurntableAlf class: Generate a ALF file to submit a job to Tractor. 

Author: Raeyoon Kim
Created: 2025-08-21
"""


import os
from lib.core import Core
from lib.render.render_core import *
from datetime import datetime


class TurntableSh(ShellLib):
    """Provides shell content and paths for turntable rendering.
   
    Base Classes:
        ShellLib: Common shell library in render_core API.
    """    
    def __init__(self):
        super().__init__()

    def get_content(self) -> str:
        """Return shell content for turntable render.
    
        Returns:
            str: fixed and unfixed shell content added.
        """ 
        fixed = self.get_fixed_sh()
        unfixed = self.get_unfixed_sh()
        content = fixed + unfixed
        return content

    def get_path_sh(self) -> str:
        """Return shell path for turntable render.
    
        Returns:
            str: Shell path. 
        """ 
        time = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        type = os.getenv('tt_type','')
        name = os.getenv('tt_name','')
        ver = os.getenv('tt_ver','')
        dept = os.getenv('dept','')
        user = os.getenv('user','')
        file = '_'.join([type, name, ver, dept, user, time]) + '.sh'
        path_sh = os.path.join(os.getenv('base_render_asset_logs',''), file)
        os.environ['tt_sh'] = path_sh
        return path_sh

    def get_unfixed_sh(self) -> str:
        """Return unfixed shell contents for turntable render.
        
        Notes:
            'export tt_cam=' line can be changed properly on the process of turntable render.

        Returns:
            str: Unfixed shell contents with common contents plus turntable-specific variables.
        """ 
        unfixed_base = super().get_unfixed_sh()
        unfixed = f'''


export tt_cam={os.getenv('tt_cam','')}


export tt_grp={os.getenv('tt_grp','')}
export tt_sh={os.getenv('tt_sh','')}        
export tt_alf={os.getenv('tt_alf','')}
export tt_template={os.getenv('tt_template','')}
export tt_type={os.getenv('tt_type','')}
export tt_name={os.getenv('tt_name','')}
export tt_ver={os.getenv('tt_ver','')}
export tt_target_maya={os.getenv('tt_target_maya','')}
export tt_dest_dir={os.getenv('tt_dest_dir','')}

export PYTHONPATH="$base_bin:$base_lib:$base_public:$base_home"

        '''
        return unfixed_base + unfixed

    def get_mayapy_exe(self) -> str:
        """Return an executable line with args. 
    
        Returns:
            str: A line to execute turntable.py.
        """ 
        mayapy_exe = f'''        
{os.getenv('tt_exe','')} $1 $2 $3 $4 $5
        '''
        return mayapy_exe
    

class TurntableAlf(AlfLib):
    """Provides ALF content and paths for turntable rendering.
   
    Base Classes:
        AlfLib: Common ALF library in render_core api.
    """
    def __init__(self):
        super().__init__()

    def get_frame_tasks_inner(self, path_sh: str = '', start_frame: int = 1, end_frame: int = 100) -> str:
        """Return multi-frame tasks for ALF contents.

        Args:
            path_sh (str): Shell path to execute rendering. Defaults to ''.
            start_frame (int): Start frame. Defaults to 1.
            end_frame (int): End frame. Defaults to 100.

        Returns:
            str: multi-frame tasks for ALF contents.
        """
        start_frame = int(start_frame)
        end_frame = int(end_frame)
        frame_tasks_inner = ''
        for frame in range(start_frame, end_frame+1):
            frame_task = self.get_task(title=f'Frame:{frame}', path_or_cmd=path_sh + f' turn_track render {os.getpid()} {frame} {end_frame}')
            frame_tasks_inner += frame_task
        return frame_tasks_inner
    
    def get_content(self, path_sh: str = '') -> str:
        """Return entire ALF content.

        Args:
            path_sh (str): Shell path to execute rendering. Defaults to ''.

        Returns:
            str: Entire content of ALF.
        """
        header = self.get_header()
        start_frame = os.getenv('start_frame','')
        end_frame = os.getenv('end_frame','')       
        pre_task = self.get_task(title='Set a turntable', path_or_cmd=path_sh + f' turn_track preprocess {os.getpid()} {start_frame} {end_frame}')
        frame_tasks_inner = self.get_frame_tasks_inner(path_sh=path_sh, start_frame=start_frame, end_frame=end_frame)
        frame_tasks = f'''
        Task -title {{{'Turntable Frames'}}} -subtasks {{
            {frame_tasks_inner}
        }}    
        '''
        content = header + pre_task + frame_tasks + self.get_tail()
        return content
    
    def get_path_alf(self) -> str:
        """Return ALF path for turntable render.
    
        Returns:
            str: Path of ALF. 
        """ 
        time = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        type = os.getenv('tt_type','')
        name = os.getenv('tt_name','')
        ver = os.getenv('tt_ver','')
        dept = os.getenv('dept','')
        user = os.getenv('user','')
        file = '_'.join([type, name, ver, dept, user, time]) + '.alf'
        path_alf = os.path.join(os.getenv('base_render_asset_logs',''), file)
        os.environ['tt_alf'] = path_alf
        return path_alf


class TurntableRender:
    """Gerates Shell and ALF files for turntable rendering.
   
    Attributes:
        sh: TurntableSh with render_core's ShellLib.
        alf: TurntableAlf with render_core's AlfLib.
    """
    def __init__(self):
        self.sh = TurntableSh()
        self.alf = TurntableAlf()

    def set_env(self, render_data: dict = None) -> None:
        """Set up the environment variables to render.

        Args:
            render_data (dict): Custom data for rendering. Defaults to {}.
        """
        if not render_data:
            render_data = {}
            
        os.environ['tt_type'] = render_data['tt_type']
        os.environ['tt_name'] = render_data['tt_name']
        os.environ['tt_ver'] = render_data['tt_ver']
        os.environ['tt_target_maya'] = render_data['tt_target_maya']
    
        tail = f'{render_data["tt_type"]} - {render_data["tt_name"]}_{render_data["tt_ver"]}'
        os.environ['r_title'] = self.alf.get_title(dcc='Maya', type='Render', target='Assets', detail='turntable', tail=tail)
        os.environ['r_priority'] = render_data['priority']
        os.environ['r_after'] = render_data['after']
        os.environ['r_projects'] = 'CUSTOM_PROJECT'
        os.environ['r_cmt'] = render_data['cmt']
        os.environ['r_envkey'] = 'maya'
        os.environ['r_tags'] = render_data['dept']
        os.environ['r_servicekey'] = render_data['service_key']
        os.environ['start_frame'] = render_data['start_frame']
        os.environ['end_frame'] = render_data['end_frame']
        os.environ['tt_template'] = f'{os.getenv("base_lib")}/templates/maya/template_turntable.mb'
        os.environ['tt_dest_dir'] = os.path.join(os.environ['base_render_asset'],'turntable')
        os.environ['tt_exe'] = render_data['tt_exe']
        os.environ['tt_cam'] = 'turntable_cam'
        os.environ['tt_grp'] = 'turntable_asset_grp'
    
    def get_sh_path_content(self) -> tuple[str, str]:
        """Return shell path and content.

        Returns:
            tuple[str, str]: (path_sh, sh_content)
        """
        path_sh = self.sh.get_path_sh()
        sh_content = self.sh.get_content()
        mayapy_exe = self.sh.get_mayapy_exe()
        sh_content = sh_content + mayapy_exe
        self.set_file(path=path_sh, content=sh_content)
        return (path_sh, sh_content)
    
    def get_alf_path_content(self, path_sh: str = '') -> tuple[str, str]:
        """Return ALF path and content.

        Args:
            path_sh (str): Shell path to put it into ALF content. Defaults to ''.

        Returns:
            tuple[str, str]: (path_alf, alf_content)
        """
        path_alf = self.alf.get_path_alf()
        alf_content = self.alf.get_content(path_sh=path_sh)
        self.set_file(path=path_alf, content=alf_content)
        return (path_alf, alf_content)
    
    def set_file(self, path: str = None, content: str = None) -> None:
        """Set up the file and its permission.

        Args:
            path (str): Path of file to save and set up the permission. Defaults to None.
            content (str): Content of file to save. Defaults to None.
        """
        if os.path.exists(path):
            os.remove(path)
        Core.set_file(path=path, content=content)
        os.chmod(path,0o755)
    
    def set_render(self, render_data: dict = None) -> bool:
        """Main render module.

        Args:
            render_data (dict): Custom data for rendering. Defaults to {}.
            
        Returns:
            bool: True if it has been successfully executed, False if it has no environment variable named 'base_lib'.
        
        """
        if not render_data:
            render_data = {}
            
        if os.getenv('base_lib',None):
            self.set_env(render_data=render_data)
            (path_sh, sh_content) = self.get_sh_path_content()
            (path_alf, alf_content) = self.get_alf_path_content(path_sh=path_sh)
            self.alf.set_exe()
            return 1
        else:
            return 0 