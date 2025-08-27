#!/usr/bin/python


"""render_core.py

Utility API for general rendering.

Key Features:
    - ShellLib class: Generates a shell script to set up to submit a job to Tractor.
    - AlfLib class: Generates a ALF file to set up to submit a job to Tractor.

Notes:
    Both ShellLib, AlfLib are recommended to be inherited and reused 
    with new class for specific rendering.

Author: Raeyoon Kim
Created: 2025-08-21
"""


from typing import Optional
from lib.log import LogBus
import os


class ShellLib:
    """Provides shell content to set up the environment before rendering.
    
    Attributes:
        log (QLogger): Worker logger instance used for logging shell operations.
    """
    
    def __init__(self):
        self.log = LogBus.instance().get_worker(__name__)
    
    def get_fixed_sh(self) -> str:
        """Return a fixed shell script to set up the environment.

        Returns:
            str: Shell script content to source common environment settings.
        """
        fixed = f'''
#!/bin/sh


set -a
source {os.environ['base_config']}/public.sh
set +a
        '''
        return fixed

    def get_unfixed_sh(self) -> str:      
        """Return a shell script defining custom environment variables.

        Returns:
            str: Shell script content exporting user-specific environment variables.
        """
        unfixed = f'''
export r_title="{os.getenv('r_title','')}"
export r_priority={os.getenv('r_priority','')}
export r_projects={os.getenv('r_projects','')}
export r_cmt="{os.getenv('r_cmt','')}"
export r_envkey={os.getenv('r_envkey','')}
export r_tags={os.getenv('r_tags','')}
export r_servicekey={os.getenv('r_servicekey','')}
        '''
        return unfixed

        
class AlfLib:
    """Provides an ALF content to rendering.
    
    Attributes:
        log (QLogger): Worker logger instance used for logging ALF operations.
    """
    
    def __init__(self):
        self.log = LogBus.instance().get_worker(__name__)
        
    def get_title(self, 
                  dcc: str = 'Maya', 
                  type: str = 'Render', 
                  target: str = 'Assets', 
                  detail: str = 'turntable', 
                  tail: Optional[str] = ''
                  ) -> str:   
        """Return a title for the job.

        Args:
            dcc (str): Name of the DCC tool. Defaults to 'Maya'.
            type (str): Type of the job. Defaults to 'Render'.
            target (str): Target entity. Defaults to 'Assets'.
            detail (str): Detail keyword for the job. Defaults to 'turntable'.
            tail (str): Additional info like 'rae_v001'. Defaults to ''.

        Returns:
            str: Complete job title that will appear on Tractor web page.
        """
             
        title = f'{dcc} {type} {target}'
        if tail:
            title = f'{title} | {detail} | {tail}'
        else:
            title = f'{title} | {detail}'
        
        return title
        
    def get_header(self) -> str:   
        """Return the header section of the ALF contents.
        
        Returns:
            str: ALF script header with environment and job metadata.       
        """
        title = os.getenv('r_title','')
        priority = os.getenv('r_priority','')
        after = os.getenv('r_after','')
        projects = os.getenv('r_projects','')
        cmt = os.getenv('r_cmt','')
        env_key = os.getenv('r_envkey','')
        tags = os.getenv('r_tags','')
        service_key = os.getenv('r_servicekey','')
        exeSh = os.getenv('exe_sh','')
        header = f'''
##AlfredToDo 3.0

    Job -title {{{title}}} -priority {{{priority}}} -after {{{after}}} -afterjids {{}} -projects {{{projects}}} -maxactive {{0}} -comment {{{cmt}}} -metadata {{}} -dirmaps {{
        }} -envkey {{{env_key}}} -pbias 0 -tags {{{tags}}} -service {{{service_key}}} -serialsubtasks 1 -init {{
                Assign exeSh {{"%D({exeSh})"}}
            }} -subtasks {{
        '''
        return header
        
    def get_task(self, title:str, path_or_cmd:str) -> str:
        """Return a single task section for the ALF contents.
        
        Returns:
            str: ALF task block for a specific command.       
        """
        task = f'''
        Task -title {{{title}}} -subtasks {{}} -cmds {{
            RemoteCmd {{$exeSh -c '{path_or_cmd}'}}            
        }}    
        '''
        return task

    def get_tail(self):
        """Return closing brace for the ALF script.
        
        Returns:
            str: Closing brace '}'.
        """
        return '}'

    def set_exe(self):
        """Spool the job using the ALF file.
        
        Logs the command executed.
        
        Returns:
            int: 1 if the job spool command is succesfully executed. (Currently not active).       
        """
        exec = f'{os.environ["tractor_spool"]} --alfescape --user={os.environ["user"]} {os.environ["tt_alf"]}'
        self.log.info('%s', exec)
        # if exec:
        #     try:
        #         result = subprocess.check_output(exec, shell=1)    
        #         self.log.info('%s', result)
        #         return 1
        #     except Exception as e:
        #         self.log.error('%s', e)     