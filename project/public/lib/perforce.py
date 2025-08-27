#!/usr/bin/python


"""perforce.py

Utility API for handling Perforce operations.

Key Features:
    - Perforce class: Manage Peforce connection and operations.
    - UserInfo class: Retrieve user information. 
    - FileInfo class: Query file information and status.
    - Settings class
        - Convert file paths between depot/public/home.
        - Handle the P4 Exceptions.                     

Author: Raeyoon Kim
Created: 2025-08-21
"""


from __future__ import annotations
from typing import Optional, Union, Dict, List
import os
from lib.log import LogBus
from P4 import P4, P4Exception
from functools import lru_cache


class P4Settings:
    """Utils to handle files and p4 exceptions.

    Attributes:
        log (QLogger): Worker logger instance.
    """

    def __init__(self):
        self.log = LogBus.instance().get_worker(__name__)

    def get_p4_exception(self, e: Exception = None, path: str = '') -> str:
        """Extract Perforce error message from exception.

        Args:
            e (Exception, optional): Perforce exception object. Defaults to None.
            path (str, optional): File path associated with the exception. Defaults to ''.

        Returns:
            str: Extracted error message or path.
        """
        # errType = type(e).__name__ 
        err_msg = [l.strip() for l in str(e).splitlines() if "[Error]:" in l or "[Warning]:" in l] or ''
        if err_msg:
            err_msg = str(err_msg[0])
        err_msg = err_msg or path
        return err_msg

    @staticmethod
    @lru_cache(maxsize=4096)
    def get_path_switch(path: str = '', depot: bool = False, public: bool = False, home: bool = False) -> str:
        """Convert path between depot, public, and home directories.

        Notes:
            One of depot, public, home must be True.

        Args:
            path (str): Path to switch. Defaults to ''.
            depot (bool, optional): If True, return depot path. Defaults to False.
            public (bool, optional): If True, return public path. Defaults to False.
            home (bool, optional): If True, return home path. Defaults to False.

        Returns:
            str: Converted path.
        """
        dir_depot = '//depot'
        dir_public = os.environ['base_public']
        dir_home = os.environ['base_home'] 
        if depot:
            if path.startswith(dir_depot):
                return path
            elif path.startswith(dir_public):
                return path.replace(dir_public, dir_depot)
            elif path.startswith(dir_home):
                return path.replace(dir_home, dir_depot)

        elif public:
            if path.startswith(dir_public):
                return path
            elif path.startswith(dir_depot):
                return path.replace(dir_depot, dir_public)
            elif path.startswith(dir_home):
                return path.replace(dir_home, dir_public)

        elif home:
            if path.startswith(dir_home):
                return path
            elif path.startswith(dir_public):
                return path.replace(dir_public, dir_home)
            elif path.startswith(dir_depot):
                return path.replace(dir_depot, dir_home)

        
class UserInfo(P4Settings):
    """Perforce UserInfo.
    
    Base Classes:
        Settings: Utils to handle files and p4 exceptions.
    
    Attributes:
        p4 (P4): Perforce API.
    
    """
    def __init__(self, p4=None):
        super().__init__()
        self.p4 = p4
        
    def get_info(self, key: str = '') -> Union[str, Dict]:
        """Get Perforce client info by key.

        Args:
            key (str, optional): Key to fetch from Perforce info. Defaults to ''.

        Returns:
            Union[str, Dict]: Value for the key if provided, else the full info dictionary.
        """
        try:
            info = self.p4.run_info()[0]
            if key:
                try:
                    return info.get(key, None)
                except Exception as e:
                    self.log.warning('key : %s',key)
            else:
                return info
        
        except P4Exception as e:
            self.log.warning('key : %s',key)

    def get_client_name(self) -> Optional[str]:
        """Return client host name.

        Returns:
            Optional[str]: Perforce client host name.
        """
        return self.get_info(key='clientHost')

    def get_client_root(self) -> Optional[str]:
        """Return client root path.

        Returns:
            Optional[str]: Perforce client root path.
        """
        return self.get_info(key='clientCwd')

    def get_server_root(self) -> Optional[str]:
        """Return server root path.

        Returns:
            Optional[str]: Perforce server root path.
        """
        return self.get_info(key='serverRoot')

    def get_user_name(self) -> Optional[str]:
        """Return Perforce username.

        Returns:
            Optional[str]: Perforce username.
        """
        return self.get_info(key='userName')


class FileInfo(P4Settings):
    """Perforce FileInfo.

    Base Classes:
        Settings: Utils to handle files and p4 exceptions.

    Attributes:
        p4 (P4): Perforce API.
    
    """
    
    def __init__(self, p4=None):
        super().__init__()
        self.p4 = p4

    def get_editor(self, path: str = '') -> Optional[str]:
        """Get the current editor of the file.

        Args:
            path (str): File path. Defaults to ''.

        Returns:
            Optional[str]: Editor client name if the file is being edited.
        """
        try:
            if os.path.isfile(path):
                depot = self.get_path_switch(path=path, depot=True)
                client = [p['client'] for p in self.p4.run('opened','-a') if p['action'] == 'edit' and p['depotFile'] == depot]
                if client:
                    return client[0]
        except P4Exception as e:
            err_msg = self.get_p4_exception(e=e, path=path)
            self.log.warning('%s', err_msg)
                        
    def get_last_editor(self, path: str = '') -> Optional[str]:
        """Get the last editor of the file.

        Args:
            path (str): File path. Defaults to ''.

        Returns:
            Optional[str]: Last editor client name.
        """
        if not os.path.isdir(path):
            try:
                rev = self.get_filelogs(path=path)
                if rev:
                    return rev.client
            except P4Exception as e:
                err_msg = self.get_p4_exception(e=e, path=path)
                self.log.warning('%s', err_msg)

    def get_last_modified_date(self, path: str = '') -> Optional[int]:
        """Get the last modified date of the file.

        Args:
            path (str): File path. Defaults to ''.

        Returns:
            Optional[int]: Last modified timestamp.
        """
        try:
            rev = self.get_filelogs(path=path)
            if rev:
                return rev.time
        except P4Exception as e:
            err_msg = self.get_p4_exception(e=e, path=path)
            self.log.warning('%s', err_msg)

    def get_opened_or_not(self, path: str = '') -> Optional[int]:
        """Check if the file is opened in Perforce.

        Args:
            path (str): File path. Defaults to ''.

        Returns:
            Optional[int]: 1 if opened, None otherwise.
        """
        try:
            depot = self.get_path_switch(path=path, depot=True)
            if os.path.isdir(path):
                openedDepots = [opened['depotFile'] for opened in self.p4.run_opened()]
                for openedDepot in openedDepots:                 
                    if depot in openedDepot:
                        return 1
            else: 
                return self.p4.run_opened(path)
        except P4Exception as e:
            err_msg = self.get_p4_exception(e=e, path=path)
            self.log.warning('%s', err_msg)

    def get_filelogs(self, path: str = '', all_revs: int = 0) -> Union[Dict, List[Dict]]:
        """Get Perforce file log.

        Args:
            path (str): File path. Defaults to ''.
            all_revs (int): If 1, return all revisions. Defaults to 0.

        Returns:
            Union[Dict, List[Dict]]: File log or revisions.
        """
        try:
            if all_revs:
                path = self.get_path_switch(path=path, depot=True)
                return self.p4.run_filelog(path)[0].revisions
            else:
                return self.p4.run_filelog(path)[0].revisions[0]
        except P4Exception as e:
            err_msg = self.get_p4_exception(e=e, path=path)
            self.log.warning('%s', err_msg)

    def get_not_latest(self, path: str = '') -> bool:
        """Check if the file or folder is not latest in Perforce.

        Args:
            path (str): File or folder path. Defaults to ''.

        Returns:
            bool: True if not latest, False otherwise.
        """
        if os.path.isdir(path):
            dir_depot = self.get_path_switch(path=path, depot=True) + '/...'
            try:
                not_updated_files = self.p4.run('sync','-n',dir_depot)
                if not_updated_files:
                    existsOrNots = [x for x in not_updated_files if os.path.exists(x.get('clientFile',''))] or []
                    if existsOrNots:
                        return True
                    else:
                        return False
                else:
                    return False
            except P4Exception as e:
                err_msg = self.get_p4_exception(e=e, path=path)
                self.log.warning('%s', err_msg)
                return False
            except Exception as e:
                self.log.exception('%s',path)
                return False
        else:
            try:
                revs = self.get_revs(path=path, local=1, depot=True) 
                if revs.get('have',None) != revs.get('head',None):  
                    return True
                else:
                    return False
            except P4Exception as e:
                err_msg = self.get_p4_exception(e=e, path=path)
                self.log.warning('%s', err_msg)
                return False
            except Exception as e:
                self.log.exception('%s',path)
                return False
       
    def get_revs(self, path: str = '', local: bool = False, depot: bool = False) -> Union[Dict[str, Optional[int]], Optional[int]]:
        """Get revision information for a file.

        Args:
            path (str): File path. Defaults to ''.
            local (bool, optional): Include local revision. Defaults to False.
            depot (bool, optional): Include depot revision. Defaults to False.

        Returns:
            Union[Dict[str, Optional[int]], Optional[int]]: Revisions info.
        """
        public = self.get_path_switch(path=path, public=True)
        home = self.get_path_switch(path=path, home=True)
        depot = self.get_path_switch(path=path, depot=True)
        try:
            if os.path.exists(public):
                fstat = self.p4.run_fstat(depot)
                if fstat:
                    headRev = fstat[0].get('headRev',None)
                    
                    if os.path.exists(home):            
                        haveRev = fstat[0].get('haveRev',None)

                    if local==1 and depot==True:
                        return {'have':haveRev, 'head':headRev}
                    elif local==1 and depot==False:
                        return haveRev
                    elif local==False and depot==True:
                        return headRev
                    else:
                        self.log.debug('local=1 or depot=True')
                        
        except P4Exception as e:
            err_msg = self.get_p4_exception(e=e, path=path)
            self.log.warning('%s', err_msg)

        except Exception as e:
            self.log.exception('%s',path)

    def get_file_status(self, path: str = '') -> Optional[str]:
        """Determine the Perforce file status.

        Args:
            path (str): File path. Defaults to ''.

        Returns:
            Optional[str]: Status like 'STALE', 'OPENED', 'LOCAL', 'GLOBAL', 'LOCAL_ONLY', or 'NONE'.
        """
        if path:
            public = self.get_path_switch(path=path, public=True)
            home = self.get_path_switch(path=path, home=True)
            try:
                if os.path.exists(home):
                    if os.path.exists(public):
                        if self.get_not_latest(home):
                            return 'STALE'
                        elif self.get_opened_or_not(home):
                            return 'OPENED'
                        else:
                            return 'LOCAL'                      
                    else:
                        return 'LOCAL_ONLY'
                else:
                    if os.path.exists(public):
                        return 'GLOBAL'
                    else:
                        return 'NONE'
                    
            except P4Exception as e:
                err_msg = self.get_p4_exception(e=e, path=path)
                self.log.warning('%s', err_msg)
                
            except Exception as e:
                self.log.exception('%s',path)


class Perforce(P4Settings):
    """Perforce main utils.

    Base Classes:
        Settings: Utils to handle files and p4 exceptions.

    Attributes:
        p4 (P4): Perforce API.
        log (QLogger): Worker logger instance.
        user_info (UserInfo): Class related to perforce user info.
        file_info (FileInfo): Class related to perforce file Info.
    """
    
    def __init__(self):
        super().__init__()
        self.p4 = P4()        
        try:
            if not self.p4.connected():
                self.p4.connect()
            if self.p4.connected():
                self.log.info('perforce connected')
                self.user_info = UserInfo(p4=self.p4)
                self.file_info = FileInfo(p4=self.p4)
            else:
                self.log.exception('failed perforce connect')
        except P4Exception as e:
            self.log.exception('%s',e)

    def __del__(self):
        try:
            if self.p4.connected():
                self.p4.disconnect()
            if not self.p4.connected():
                self.log.info('perforce disconnected')
            else:
                self.log.exception('failed perforce disconnect')
                
        except P4Exception as e:
            self.log.exception('%s',e)

    def get_update(self, path: str = '', rev: Optional[int] = None):
        """ Update the file to a specific revision from Perforce.

        Args:
            path (str): File path. Defaults to ''.
            rev (Optional[int], optional): Revision number. Defaults to None.

        Returns:
            Any: Result of Perforce sync command.
        """
        public = self.get_path_switch(path=path, public=True)
        home = self.get_path_switch(path=path, home=True)
        if os.path.exists(home):
            if os.path.exists(public):
                try:
                    if rev:
                        if rev == 0:
                            self.log.info('del : %s', home)
                            os.system(f'p4 sync -f {home}#0')
                            return
                        home = home+'#'+str(rev)
                    return self.p4.run(['sync','-f', home])
                except P4Exception as e:
                    self.log.warning('%s, rev : %s', path, rev)
        else:
            if os.path.exists(public):
                try:
                    if not os.path.exists(os.path.dirname(home)):
                        os.makedirs(os.path.dirname(home))
                    if rev:
                        home = home+'#'+str(rev)
                    return self.p4.run(['sync','-f', home])
                except P4Exception as e:
                    err_msg = self.get_p4_exception(e=e, path=path)
                    self.log.warning('%s', err_msg)

    def set_add(self, path: str = ''):
        """Add a file to Perforce.

        Args:
            path (str): File path. Defaults to ''.

        Returns:
            Any: Result of Perforce add command.
        """
        home = self.get_path_switch(path=path, home=True)
        try:
            return self.p4.run(['add', '-t', '+l', home])
        except P4Exception as e:
            err_msg = self.get_p4_exception(e=e, path=path)
            self.log.warning('%s', err_msg)

    def set_edit(self, path: str = ''):
        """Open a file for edit in Perforce.

        Args:
            path (str): File path. Defaults to ''.

        Returns:
            Any: Result of Perforce edit command.
        """
        home = self.get_path_switch(path=path, home=True)
        try:
            self.get_update(path)
            return self.p4.run_edit(home)
        except P4Exception as e:
            err_msg = self.get_p4_exception(e=e, path=path)
            self.log.warning('%s', err_msg)

    def set_revert(self, path: str = ''):
        """Revert a file in Perforce.

        Args:
            path (str): File path. Defaults to ''.

        Returns:
            Any: Result of Perforce revert command.
        """
        home = self.get_path_switch(path=path, home=True)
        try:
            return self.p4.run_revert(home)
        except P4Exception as e:
            err_msg = self.get_p4_exception(e=e, path=path)
            self.log.warning('%s', err_msg)

    def set_del(self, path: str = ''):
        """ Delete a file in Perforce.

        Args:
            path (str, optional): File path. Defaults to ''.

        Returns:
            Any: Result of Perforce delete command.
        """
        home = self.get_path_switch(path=path, home=True)
        try:
            return self.p4.run_delete(home)
        except P4Exception as e:
            err_msg = self.get_p4_exception(e=e, path=path)
            self.log.warning('%s', err_msg)

    def set_submit(self, path: str = '', description: str = ''):
        """Submit a file to Perforce with description.

        Args:
            path (str, optional): File path. Defaults to ''.
            description (str, optional): Description of the change. Defaults to ''.

        Returns:
            Any: Result of Perforce submit command.
        """
        if description:
            depot = self.get_path_switch(path=path, depot=True)
            public = self.get_path_switch(path=path, public=True)
            home = self.get_path_switch(path=path, home=True)

            # general submit
            if any([os.path.exists(home) == 1 and os.path.exists(public) == 1, os.path.exists(home) == 1 and os.path.exists(public) == 0]):
                if not os.path.exists(os.path.dirname(public)):
                    os.makedirs(os.path.dirname(public))
            
                try:
                    change = self.p4.fetch_change()
                    change['Description'] = description
                    change['Files'] = [depot]
                    return self.p4.run_submit(change)
                    
                except P4Exception as e:
                    err_msg = self.get_p4_exception(e=e, path=path)
                    self.log.warning('%s', err_msg)

            # deleted file submit
            elif os.path.exists(home) == 0 and os.path.exists(public) == 1:
                if not os.path.exists(home):
                    try:
                        change = self.p4.fetch_change()
                        change['Description'] = description
                        change['Files'] = [depot]
                        return self.p4.run_submit(change)
                    except P4Exception as e:
                        err_msg = self.get_p4_exception(e=e, path=path)
                        self.log.warning('%s', err_msg)
        else:
            self.log.debug('no desc')
            
            