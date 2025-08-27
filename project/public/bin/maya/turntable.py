#!/usr/autodesk/maya2024/bin/mayapy


"""turntable.py

Maya batch renderer in the background to render turntables.

Key Features:
    - TurnTable class
        - set_preprocess: Create and set up a Maya .mb file.
        - set_render: Execute batch render.

Author: Raeyoon Kim
Created: 2025-08-21
"""


import os, sys
TOOL_NAME = sys.argv[1]         # turn_track
PROCESS = sys.argv[2]           # preprocess or render
PID = sys.argv[3]               # main pid to save log
START_FRAME = int(sys.argv[4])  # 1~100
END_FRAME = int(sys.argv[5])    # 100
os.environ['tool_name'] = TOOL_NAME
os.environ['log_pid'] = f'PID_{PID}'
os.environ['log_file'] = '.'.join([TOOL_NAME, PROCESS, str(START_FRAME)])
from lib.log import LogBus
try:
    LogBus.instance()
except RuntimeError:
    LogBus.init(os.environ['tool_name'], light=True)
LOG = LogBus.instance().get_worker(os.environ['tool_name'])
import maya.standalone
maya.standalone.initialize()
import maya.cmds as cmds


class Turntable:
    """Class to automate turntable rendering in Maya.

    Attributes:
        path_sh (str): Path to the shell script.
        path_batch_render (str): Path to the batch render executable.
        path_maya_template (str): Path to the Maya template file.
        path_maya_target (str): Path to the target Maya file to import.
        path_dest_dir (str): Destination directory for outputs.
        asset_grp (str): Name of the asset group in Maya.
        cam (str): Camera name.
        cam_aperture_inch (tuple[float, float]): Camera film aperture in inches.
    """
    
    def __init__(self):
        LOG.info('start : %s, end : %s', str(START_FRAME), str(END_FRAME))
        
        self.path_sh = os.environ['tt_sh']
        self.path_batch_render = os.path.join(os.environ['m24_render'])
        self.path_maya_template = os.environ['tt_template']
        self.path_maya_target = os.environ['tt_target_maya']
        self.path_dest_dir = os.environ['tt_dest_dir']
        self.asset_grp = os.environ['tt_grp']
        self.cam = os.environ['tt_cam']
        self.cam_aperture_inch = (1.417, 0.945)
        
        LOG.debug('path maya target : %s', self.path_maya_target)
    
    def set_obj_scale(self, max_x: float = 3.6, max_y: float = 2.4, max_z: float = 2.4) -> None:
        """Scale the asset group to fit within max dimensions.

        Args:
            max_x (float): Maximum X size. Defaults to 3.6.
            max_y (float): Maximum Y size. Defaults to 2.4.
            max_z (float): Maximum Z size. Defaults to 2.4.
        """
        box = cmds.exactWorldBoundingBox(self.asset_grp)
        width  = box[3] - box[0]  # X
        height = box[4] - box[1]  # Y
        depth  = box[5] - box[2]  # Z

        scale_x = cmds.getAttr(self.asset_grp + '.scaleX')
        scale_y = cmds.getAttr(self.asset_grp + '.scaleY')
        scale_z = cmds.getAttr(self.asset_grp + '.scaleZ')

        ratio_x = max_x / width
        ratio_y = max_y / height
        ratio_z = max_z / depth
        scale_ratio = min(ratio_x, ratio_y, ratio_z) * 5
        cmds.setAttr(self.asset_grp + '.scaleX', scale_x * scale_ratio)
        cmds.setAttr(self.asset_grp + '.scaleY', scale_y * scale_ratio)
        cmds.setAttr(self.asset_grp + '.scaleZ', scale_z * scale_ratio)

    def set_cam(self) -> None:
        """Create and configure the camera for the turntable.
        """
        self.cam, cam_shape = cmds.camera(name=self.cam)
        cmds.xform(self.cam, centerPivots=1)
        cmds.move(0, 0, 60, self.cam, absolute=1)
        cmds.setAttr(cam_shape+'.displayCameraNearClip', 1)
        cmds.setAttr(cam_shape+'.displayCameraFarClip', 1)
        cmds.setAttr(cam_shape+'.displayCameraFrustum', 1)
        cmds.setAttr(cam_shape+'.nearClipPlane', 0.1)
        cmds.setAttr(cam_shape+'.farClipPlane', 10000)
        cmds.setAttr(cam_shape+'.horizontalFilmAperture', self.cam_aperture_inch[0])
        cmds.setAttr(cam_shape+'.verticalFilmAperture', self.cam_aperture_inch[1])
        cmds.setAttr(cam_shape+'.cameraScale', 1)
        cmds.setAttr(cam_shape+'.focalLength', 35)  
        self.set_cam_name_replace()
        
    def set_cam_name_replace(self) -> None:
        """ Update the shell script with the camera name.
        """
        with open(self.path_sh, encoding="utf-8") as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            if 'export tt_cam=' in lines[i]:
                lines[i] = f'''
export tt_cam={self.cam}
                '''
                break

        try:
            with open(self.path_sh, "w", encoding="utf-8") as f:
                f.writelines(lines)
        except Exception as e:
            LOG.debug('path_sh : %s', self.path_sh)
            LOG.exception('%s', e)

    def set_rotate(self) -> None:
        """Set rotation keyframes for a turntable animation.
        """
        cmds.setAttr(f"{self.asset_grp}.rotateX", 0)
        cmds.setAttr(f"{self.asset_grp}.rotateY", 0)
        cmds.setAttr(f"{self.asset_grp}.rotateZ", 0)
        cmds.setKeyframe(self.asset_grp, time=START_FRAME, attribute=['rotateX','rotateY','rotateZ'])
    
        cmds.setAttr(f"{self.asset_grp}.rotateX", 0)
        cmds.setAttr(f"{self.asset_grp}.rotateY", 360)
        cmds.setAttr(f"{self.asset_grp}.rotateZ", 0)
        cmds.setKeyframe(self.asset_grp, time=START_FRAME + END_FRAME/2, attribute=['rotateX','rotateY','rotateZ'])
        
        cmds.setAttr(f"{self.asset_grp}.rotateX", 360)
        cmds.setAttr(f"{self.asset_grp}.rotateY", 360)
        cmds.setAttr(f"{self.asset_grp}.rotateZ", 0)
        cmds.setKeyframe(self.asset_grp, time=START_FRAME + END_FRAME, attribute=['rotateX','rotateY','rotateZ'])

    def get_open_import(self) -> None:
        """Open template Maya file and import target asset.
        """
        cmds.file(self.path_maya_template, open=1, force=1)
        cmds.file(self.path_maya_target, i=1, gr=1, gn=self.asset_grp)
        cmds.xform(self.asset_grp, centerPivots=1)      
            
    def set_render_settings(self) -> None:
        """Configure render settings for turntable output.
        """
        cmds.setAttr('defaultRenderGlobals.imageFormat', 32)
        cmds.setAttr("defaultRenderGlobals.outFormatExt", "name.#.png", type='string')
        cmds.setAttr("defaultRenderGlobals.startFrame", float(START_FRAME))
        cmds.setAttr("defaultRenderGlobals.endFrame", float(END_FRAME))
        
    def get_path_maya_saved(self) -> str:
        """Get the path where Maya file should be saved.

        Returns:
            str: Path to save Maya file.
        """
        path_dest_dir_target_tmp = os.path.join(self.path_dest_dir, os.environ['tt_type'], os.environ['tt_name'], os.environ['tt_ver'], 'tmp')
        os.makedirs(path_dest_dir_target_tmp, exist_ok=1)
        file_name = 'turntable_' + os.path.basename(self.path_maya_target)
        path_save_as = os.path.join(path_dest_dir_target_tmp, file_name)
        return path_save_as
    
    def set_maya_file_save_as(self) -> str:
        """Save Maya file with a new name.

        Returns:
            str: Path of saved Maya file.
        """
        path_save_as = self.get_path_maya_saved()
        try:
            cmds.file(rename=path_save_as)
            cmds.file(force=1, save=1, type='mayaBinary')
            return path_save_as
        except Exception as e:
            LOG.debug('path_save_as : %s', path_save_as)
            LOG.exception('%s', e)
    
    def set_render(self) -> None:
        """Execute batch render for turntable frame.
        """
        path_saved_as = self.get_path_maya_saved()
        path_dest_dir_target = os.path.dirname(os.path.dirname(path_saved_as))
        cmds.currentTime(START_FRAME)
        cmd = f'{self.path_batch_render} -r hw2 -proj {path_dest_dir_target} -fnc 3 -of png -rd {path_dest_dir_target} -cam {self.cam} -s {START_FRAME} -e {START_FRAME} -b 1 {path_saved_as}'
        try:
            os.system(cmd)
            LOG.info('cmd : %s', cmd)
        except Exception as e:
            LOG.debug('cmd : %s', cmd)
            LOG.exception('%s', e)
    
    def set_preprocess(self) -> str:
        """Preprocess the Maya scene for turntable rendering.

        Returns:
            str: Path to the saved Maya file.
        """
        self.get_open_import()        
        cmds.playbackOptions(e=1, min=START_FRAME, max=END_FRAME)
        self.set_cam()
        self.set_obj_scale()
        self.set_rotate()
        self.set_render_settings()
        path_saved_as = self.set_maya_file_save_as()
        self.set_cam_name_replace()
        LOG.info('path_saved_as : %s', path_saved_as)
        return path_saved_as


if __name__ == '__main__': 
    LOG.info('[ Turntable render start ]')
    turnTable = Turntable()    
    if PROCESS == 'preprocess':
        path_saved_as = turnTable.set_preprocess()
    else:
        turnTable.set_render()
        
    
    
    
