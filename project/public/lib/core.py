#!/usr/bin/python


"""core.py

Utility API for handling general files and terminals.

Key Features:
    - Core class : Provides class methods for general file and terminal handling

Author: Raeyoon Kim
Created: 2025-08-21
"""


from lib.log import LogBus
import os, subprocess, json
from typing import Union

 
class Core:
    """Provides class methods for reading/writing files, opening, cmd, etc.    
    
    Attributes:
        log (QLogger): Worker logger instance used for logging Core operations.
    """
    log = LogBus.instance().get_worker(__name__)
    
    @classmethod
    def set_cmd(cls, cmd: str = None) -> str:
        """Execute cmd on current terminal.

        Args:
            cmd (str): Commands to execute. Defaults to None.

        Returns:
            str: Result of executed.
        """
        if cmd:
            try:
                result = subprocess.check_output(cmd, shell=1)
                if result:
                    return str(result.decode().strip())
            except Exception as e:
                cls.log.error('%s', e)

    @classmethod
    def get_new_terminal(cls, cmd: str = None) -> None:
        """Execute cmd on a new terminal.

        Args:
            cmd (str): Commands to execute. Defaults to None.
        """
        env = os.environ['XDG_CURRENT_DESKTOP']
        if env == 'GNOME':    
            try:
                subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', f'{cmd}; exec bash'])
            except Exception as e:
                cls.log.error('GNOME cmd : %s', e)
        else:
            try:
                subprocess.Popen(['mate-terminal', '--', 'bash', '-c', f'{cmd}; exec bash'])
            except Exception as e:
                cls.log.error('MATE cmd : %s', e)
                
    @classmethod
    def get_file(cls, path: str = '') -> list:
        """Return the lines of the file as a list of strings.

        Args:
            path (str): Path to open. Defaults to ''.

        Returns:
            list: Lines of the file.
        """
        with open(path, 'r', encoding='utf-8') as f:
            return f.readlines()
     
    @classmethod
    def set_file(cls, path: str = '', content: str = None) -> None:
        """Save a new file and set the permission.

        Args:
            path (str): Path to save. Defaults to ''.
            content (str): Content to save. Defaults to None.
        """
        if path:
            if not content:
                cls.log.warning('empty content')
                
            if not os.path.exists(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path))
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                if os.path.exists(path):
                    os.chmod(path, 0o555)
                    cls.log.info('save : %s', path)
                else:
                    cls.log.error('%s', path)
            except Exception as e:
                cls.log.error('%s', e)

    @classmethod
    def get_json(cls, path: str = '') -> dict:
        """Return the json content.

        Args:
            path (str): Json path to get content. Defaults to ''.

        Returns:
            dict: Json content.
        """
        if path:
            if os.path.exists(path):            
                try:
                    with open(path, 'r') as f:
                        content = json.load(f)
                        return content
                except Exception as e:
                    cls.log.error('%s', e)
            else:
                cls.log.warning('this path does not exists : %s', path)

    @classmethod
    def set_json(cls, content: Union[dict, list], path: str = '') -> None:
        """Save a json file.

        Args:
            content (Union[dict,list]): Content to save as json.
            path (str): Path to save. Defaults to ''.
        """
        if path:
            if not content:
                cls.log.warning('empty data')
                return 
            
            if not os.path.exists(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path), exist_ok=1)
            
            try:
                with open(path, 'w') as f:
                    json.dump(content, f, indent=4)
                
                if os.path.exists(path):
                    cls.log.info('Save : %s', path)
                else:
                    cls.log.warning('this path does not exists : %s', path)
                    
            except Exception as e:
                cls.log.error('%s | %s | %s', path, str(content), e)

    @classmethod
    def get_open(cls, target: str = '') -> None:
        """Open specific target like url.

        Args:
            target (str): Url link to open. Defaults to ''.
        """
        if target:
            try:
                subprocess.Popen(['xdg-open', target])
            except Exception as e:
                cls.log.error('%s', e)    
        else:
            cls.log.warning('no target : %s', target)

    @classmethod
    def get_open_explorer(cls, path: str = '') -> None:
        """Open specific target like path.

        Args:
            path (str): Path to open on the explorer. Defaults to ''.
        """
        if path:
            if os.path.exists(path):
                try:
                    subprocess.check_output(['xdg-open', path])
                except:
                    cls.log.error('failed open : %s', path)
            else:
                cls.log.warning('this path does not exists : %s', path)

    @classmethod
    def get_copy_path(cls, path: str = '') -> None:
        """Copy specific path.

        Args:
            path (str): Path to copy. Defaults to ''.
        """
        if path:
            try:
                from PyQt5.QtWidgets import QDialog, QApplication
                cb = QApplication.clipboard()
                cb.setText(path)
            except Exception as e:
                cls.log.error('%s', e)   

