#!/usr/bin/python


"""ui.py

Utility API for easily creating UIs using PyQt5.

Key Features:
    - Color class: Set colors for UI items.
    - RClickActs class: Display right-click actions.
    - P4Submit class: Display a window with a comment field and submit button.
    - Message class: Display a confirmation dialog.
    - ImgViewer class: Create an image sequence viewer in the current window.
    - Table class: Handle QTable-related UIs.
    - Tree class: Handle QTree-related UIs.
    - Ui: General UI class. (can be inherited or used standalone)
    - UiHbox: Return UI items arranged with a QHBoxLayout.
    - UiVbox: Return UI items arranged with a QVBoxLayout.

Author: Raeyoon Kim
Created: 2025-08-21
"""


from __future__ import annotations
from typing import Optional, Callable
from functools import lru_cache
from typing import Union
import os, glob
from PyQt5.QtWidgets import  QSlider, QComboBox, QDateTimeEdit, QDialog, QLabel, QAction, QLineEdit, QListWidgetItem, QFormLayout, QFileDialog, QHeaderView, QTableWidget, QTableWidgetItem, QMessageBox, QSizePolicy, QTreeWidgetItem, QAbstractItemView, QHBoxLayout, QVBoxLayout, QPushButton, QTreeWidget, QCheckBox
from PyQt5.QtCore import Qt, QSize, QRegExp, QDateTime
from PyQt5.QtGui import QColor, QPixmap, QRegExpValidator
from lib.log import LogBus
from lib.core import Core

    
class Color:
    """Provides color formats and modules to set up an ui item's background color.
    
    Notes:
        Attributes of colors can be added.
    
    Attributes:
        light_gray (str): Light gray color name.
        gray (str): Gray color name.
    """
    def __init__(self):
        self.light_gray = 'lightGray'
        self.gray = 'gray'
    
    @staticmethod
    def get_color(color_key: Union[str, tuple[int, int, int], None]) -> Optional[QColor]:
        """Return a QColor object from a string or RGB tuple.

        Args:
            color_key (str, tuple[int, int, int]): Color string or RGB tuple. If None, returns None. Defaults to None.

        Raises:
            ValueError: If the color_key is invalid.    
    
        Returns:
            QColor | None: Corresponding QColor object or None if color_key is None.
        """
        if not color_key:
            return
        if isinstance(color_key, str):        
            return QColor(color_key)
        elif isinstance(color_key, (tuple, list)) and len(color_key) == 3:
            return QColor(*color_key)
        raise ValueError(f"Invalid color_key: {color_key}")

    def set_bgc(
        self, 
        item: Union[QTableWidgetItem, QTreeWidgetItem, QListWidgetItem, None], 
        color_key: Union[str, tuple[int, int, int], None], 
        column: int = 0
    ) -> None:
        """Set the background color of a UI item.

        Args:
            item: QTableWidgetItem, QTreeWidgetItem, or QListWidgetItem. Defaults to None.
            color_key (str, tuple[int, int, int]): Color as a string or RGB tuple.  If None, no change applied.. Defaults to None.
            column (int): Column index for column-based items (e.g., QTreeWidgetItem). Defaults to 0.
        """
        if not item:
            return 
        
        if all([item, color_key]):
            color = self.get_color(color_key=color_key)
            if isinstance(item, (QTreeWidgetItem, QListWidgetItem)):
                item.setBackground(column, color)
            else:
                item.setBackground(color)


class RClickActs:
    """Provides right-click actions.
    
    Notes:
        P4 modules can decide whether return the action or not by file's status.
    
    Attributes:
        p4 (P4): Perforce API. Defaults to None.
    """
    def __init__(self, p4: P4 = None):
        self.p4 = p4
        if not self.p4:
            import P4
            self.p4 = P4()

    @staticmethod
    def get_act_rclick(
        label: str,
        func: Callable[..., None]
    ) -> QAction:
        """Return an action with label and func. 

        Args:
            label (str): Label for action.
            func (Callable[..., None]): Function/slot to connect.

        Returns:
            QAction: Configured action.
        """
        action = QAction(label)
        action.triggered.connect(func)
        return action

    def get_act_p4_update(self, path: str = '') -> QAction:
        label = 'P4 Update'
        if self.p4.file_info.get_filelogs(path=path, all_revs=1):
            action = self.get_act_rclick(label=label, func=lambda *args: self.p4.get_update(path=path))
            return action

    def get_act_p4_edit(self, path: str = '') -> QAction:
        label = 'P4 Edit'
        opened_data = self.p4.file_info.get_opened_or_not(path=path)
        if opened_data:
            if opened_data.get('action', None) in ['add','edit','delete']:
                action = self.get_act_rclick(label=label, func=lambda *args: self.p4.set_edit(path=path))
                return action
    
    def get_act_p4_revert(self, path: str = '') -> QAction:
        label = 'P4 Revert'
        opened_data = self.p4.file_info.get_opened_or_not(path=path)
        if opened_data:
            if opened_data.get('action', None) in ['add','edit','delete']:
                if opened_data.get('client', None) == self.p4.user_info.get_client_name():
                    action = self.get_act_rclick(label=label, func=lambda *args: self.p4.set_revert(path=path))
                    return action

    def get_act_p4_add(self, path: str = '') -> QAction:
        label = 'P4 Add'
        opened_data = self.p4.file_info.get_opened_or_not(path=path)
        if not opened_data:
            action = self.get_act_rclick(label=label, func=lambda *args: self.p4.set_add(path=path))
            return action

    def get_act_del(self, path: str = '') -> QAction:
        label = 'P4 Delete'
        opened_data = self.p4.file_info.get_opened_or_not(path=path)
        if opened_data:
            if opened_data.get('action', None) in ['add','edit','delete']:
                if opened_data.get('client', None) == self.p4.user_info.get_client_name():
                    action = self.get_act_rclick(label=label, func=lambda *args: self.p4.set_del(path=path))
                    return action

    def get_act_del_local(self, path: str = '') -> QAction:
        label = f'Delete (Local Only)'
        if self.p4.file_info.get_filelogs(path=path, all_revs=1):
            action = self.get_act_rclick(label=label, func=lambda *args: self.p4.get_update(path=path, rev=0))
            return action

    def get_act_p4_submit(self, path: str = '') -> QAction:
        label = 'P4 Submit'
        opened_data = self.p4.file_info.get_opened_or_not(path=path)
        if opened_data:
            if opened_data.get('action', None) in ['add','edit','delete']:
                if opened_data.get('client', None) == self.p4.user_info.get_client_name():
                    action = self.get_act_rclick(label=label, func=lambda p4_submit_window: P4Submit(p4=self.p4, path=path).exec_())
                    return action

    def get_all_p4_acts(self, path: str = '') -> list[QAction]:
        """Return all actions related to p4. 

        Args:
            path (str): Path to link with actions. Defaults to ''.

        Returns:
            list[QAction]: List of QActions. Defaults to [].
        """
        if not path: 
            return []
        update = self.get_act_p4_update(path=path) or None
        edit = self.get_act_p4_edit(path=path) or None
        add = self.get_act_p4_add(path=path) or None
        revert = self.get_act_p4_revert(path=path) or None
        del_local = self.get_act_del_local(path=path) or None
        delete = self.get_act_del(path=path) or None
        submit = self.get_act_p4_submit(path=path) or None
        acts = [update, edit, add, revert, del_local, delete, submit]
        acts = [x for x in acts if x]
        return acts
        
    def get_act_open_explorer(self, path: str = '') -> QAction:
        """Return QAction for opening path.

        Args:
            path (str): Path to open. Defaults to ''.

        Returns:
            QAction: Opening QAction linked with the path.
        """
        if not path: 
            return
        label = 'Open In Explorer'
        if os.path.isfile(path):
            path = os.path.dirname(path)
        action = self.get_act_rclick(label=label, func=lambda *args: Core.get_open_explorer(path=path))
        return action

    def get_act_copy_path(self, path: str = '') -> QAction:
        """Return QAction for copying path.

        Args:
            path (str): Path to copy. Defaults to ''.

        Returns:
            QAction: Copying QAction linked with the path.
        """
        if not path: 
            return
        label = 'Copy Path'
        action = self.get_act_rclick(label=label, func=lambda *args: Core.get_copy_path(path=path))
        return action

    def get_all_acts(self, path: str = '') -> list[QAction]:
        """Return all QActions linked to path.

        Args:
            path (str): Path to copy. Defaults to ''.

        Returns:
            list[QAction]: Copying QAction linked with the path. Defaults to [].
        """
        if not path: 
            return []
        actions = self.get_all_p4_acts(path=path) or []
        act_open_ex = self.get_act_open_explorer(path=path) or None
        act_copy_path = self.get_act_copy_path(path=path) or None
        if act_open_ex:
            actions.append(act_open_ex)
        
        if act_copy_path:
            actions.append(act_copy_path)
        return actions


class P4Submit(QDialog):
    """Set the popup window with a comment field and a submit button.

    Base classes:
        QDialog: QDialog for popup.
        
    Attributes:
        log (QLogger): Worker logger instance.
        p4 (P4): Perforce API.
        path (str): Path to submit.
    """
    def __init__(self, p4: P4 = None, path: str = ''):
        super().__init__()
        self.log = LogBus.instance().get_worker(__name__)
        self.p4 = p4
        self.path = path
        if not self.p4:
            import P4
            self.p4 = P4()
            
        self.setWindowTitle("Submit (Perforce)")
        self.setGeometry(600, 500, 600, 70)

        main = UiHbox()
        self.form = QFormLayout()        
        self.comment = self.get_form_field(label='comment : ')
        self.btn_submit = self.get_form_button(label='submit')
        
        self.form.setLabelAlignment(Qt.AlignRight)
        main.addLayout(self.form)        
        self.setLayout(main)

    def get_form_field(self, label: str = '') -> QLineEdit:
        """Return a textfield linked with its parent-form.

        Args:
            label (str): Label displayed beside the input field. Defaults to ''.

        Returns:
            QLineEdit: Field to enter comments.
        """
        label = QLabel(label)
        textField = QLineEdit()
        self.form.addRow(label, textField)
        return textField

    def get_form_button(self, label: str = '') -> QPushButton:
        """Return a button linked with its parent-form.

        Args:
            label (str): Label on the button. Defaults to ''.

        Returns:
            QPushButton: Button to submit.
        """
        button = QPushButton(label)
        button.clicked.connect(lambda *args: self.set_submit())
        self.form.addRow(button)
        return button

    def set_submit(self) -> None:
        """Submit the file with comments.
        
        Notes:
            Submission is currently disabled for safety/testing.
        """
        comment = self.comment.text()
        self.log.info('cmd : %d', comment)
        #self.p4.submit(comment, self.path)
        self.accept()


class Message:
    """Set the popup dialog.
    
    Attributes:
        msg (QMessageBox): Pop-up dialog.
        answer (bool): If msg has yes/no option, the user's selection will be saved in this variable. Defaults to False.
    """
    def __init__(self, title: str = '', txt: str = '', no_option: bool = False):
        self.msg = QMessageBox()
        self.answer = self.get_msg_box(title=title, txt=txt, no_option=no_option)

    def get_msg_box(self, title: str = '', txt: str = '', no_option: bool = False) -> bool:
        """Show up a msg box with yes/no option or not. 

        Args:
            title (str): Msgbox's title. Defaults to ''.
            txt (str): Msgbox's text. Defaults to ''.
            no_option (bool): If 1, include Yes/No buttons. Defaults to False.

        Returns:
            bool: User's choice of yes/no. Defaults to False.
        """
        self.msg.setWindowTitle(title)
        self.msg.setText(txt)
        self.msg.setIcon(QMessageBox.Warning)
        
        if no_option:
            self.msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            self.msg.setDefaultButton(QMessageBox.No)
            
        result = self.msg.exec_()
        if result == QMessageBox.Yes:
            return 1
        else:
            return 0
    
                
class ImgViewer:
    """Provides image viewer with slider.
    
    Attributes:
        log (QLogger) : Worker to logging.
    """
    def __init__(self):
        self.log = LogBus.instance().get_worker(__name__)
    
    def get_img_seq_viewer(self, q_widget: QWidget) -> tuple[QLabel, QSlider]:
        """Create and return an image sequence viewer.

        Notes:
            Creates a QLabel (for displaying images) and a horizontal QSlider 
            (for navigating frames) within the given QWidget.

        Args:
            q_widget (QWidget): Parent widget to host the viewer and slider.

        Returns:
            tuple[QLabel, QSlider]: A tuple containing the image viewer (QLabel) and the frame slider (QSlider).
        """
        viewer = QLabel('No Images', q_widget)
        slider = QSlider(Qt.Horizontal)
        viewer.setAlignment(Qt.AlignCenter)
        return (viewer, slider)
    
    def set_img_seq_viewer(
        self, 
        viewer: QLabel, 
        slider: QSlider, 
        path_dir: str = ''
    ) -> QSlider:
        """Initialize the image sequence viewer with images from a directory.

        Notes:
            Connects the slider to the viewer so that sliding updates the displayed image.
            If the directory contains no images, the viewer shows "No Images".
            Supports .png, .jpg, .jpeg, .exr.

        Args:
            viewer (QLabel): Label widget to display images.
            slider (QSlider): Slider widget to control frame index.
            path_dir (str): Directory path containing image sequence files. Defaults to ''.

        Returns:
            QSlider: The slider, configured and connected to the image viewer.
        """
        exts = ['*.png', '*.jpg', '*.jpeg', '*.exr']
        images = []
        for ext in exts:
            images.extend(glob.glob(os.path.join(path_dir, ext)))

        frame_count = len(images)
        slider.setMinimum(0)
        slider.setMaximum(frame_count - 1)
        slider.valueChanged.connect(lambda index, fc=frame_count, imgs=images, vw=viewer: self.get_show_img_seq_frame(index, fc, imgs, vw))
        self.get_show_img_seq_frame(index=0, frame_count=frame_count, images=images, viewer=viewer)    
        slider.setEnabled(True)
        return slider
        
    def get_show_img_seq_frame(
        self, 
        index: int = 0, 
        frame_count: int = 0, 
        images: list = [], 
        viewer: QLabel = None
    ) -> None:
        """Display frames in the image sequence.

        Notes:
            Loads and scales the image at the given index, then sets it on the viewer.
            If the index is out of range or the image cannot be loaded, a fallback message is shown.

        Args:
            index (int): Frame index to display. Defaults to 0.
            frame_count (int): Total number of frames in the sequence. Defaults to 0.
            images (list[str]): List of image file paths in sequence order.
            viewer (QLabel): Label widget that displays the image.
        """
        if frame_count == 0:
            viewer.setText('No Images')
            return
        if 0 <= index < frame_count:
            pixmap = QPixmap(images[index])
            
            if pixmap.isNull():
                self.log.warning('Failed to load image: %s', images[index])
                viewer.setText('Failed to load')
                return

            viewer.setPixmap(pixmap.scaled(
                viewer.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
    def set_clean_seq_viewer(self, viewer: QLabel, slider: QSlider) -> None:
        """Reset the image sequence viewer.

        Notes:
            Clears the displayed image, sets the text to 'No Images', 
            and disables the slider.

        Args:
            viewer (QLabel): Image viewer to clear.
            slider (QSlider): Slider to disable.
        """
        if viewer:
            viewer.clear()
            viewer.setText('No Images')

        if slider:
            slider.setEnabled(False)


class Table:
    """Utility class for creating and configuring QTableWidget instances."""
    
    def __init__(self):
        pass
    
    def set_table_data(
        self,
        table: QTableWidget, 
        data: list = [], 
        header_h: list = [], header_v: list = [], 
        enable: bool = True, 
        color_keywords: str = 'stable', 
        no_edit: bool = True, 
        col_sel: bool = True
    ) -> QTableWidget:
        """Populate and configure a QTableWidget.

        Args:
            table (QTableWidget): Table widget to configure.
            data (list, optional): 2D list representing table contents.
                Each inner list corresponds to a row.
            header_h (list, optional): Horizontal header labels. Defaults to [].
            header_v (list, optional): Vertical header labels. Defaults to [].
            enable (bool, optional): Whether the table is enabled. Defaults to True.
            color_keywords (str, optional): Keyword to determine background coloring
                rule for rows/columns. Defaults to 'stable'.
            no_edit (bool, optional): If True, disables cell editing. Defaults to True.
            col_sel (bool, optional): If True, enables column-based selection. Defaults to True.

        Returns:
            QTableWidget: Configured table widget with data and headers set.
        """
        table.clear()
        rows = len(header_v)
        cols = len(header_h) if header_h else max((len(r) for r in data), default=0)

        table.setRowCount(rows)
        table.setColumnCount(cols)

        if header_v:
            table.setVerticalHeaderLabels(header_v)
        if header_h:
            table.setHorizontalHeaderLabels(header_h)

        if color_keywords:
            color = Color()
        
        for rn, row in enumerate(data):
            for cn, content in enumerate(row):
                table_item = QTableWidgetItem(str(content))
                table.setItem(rn, cn, table_item)
                if color_keywords and color_keywords in str(header_v[cn]):
                    color.set_bgc(item=table_item, color_key=color.light_gray, column=1)

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for col in range(1, table.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.Stretch)
        
        if no_edit:
            table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        if col_sel:
            table.setSelectionBehavior(QAbstractItemView.SelectColumns)
        
        table.resizeColumnsToContents()
        table.setEnabled(enable)
        return table

    def get_table(
        self, 
        data: list = [], 
        header_h: list = [], 
        header_v: list = [], 
        enable: bool = True
    ) -> QTableWidget:
        """Create a QTableWidget with the given data and headers.

        Args:
            data (list, optional): 2D list representing table contents. Defaults to [].
            header_h (list, optional): Horizontal header labels. Defaults to [].
            header_v (list, optional): Vertical header labels. Defaults to [].
            enable (bool, optional): Whether the table is enabled. Defaults to True.

        Returns:
            QTableWidget: New QTableWidget instance populated with provided data.
        """
        table = QTableWidget(len(header_v), len(header_h))
        if data:
            table = self.set_table_data(table=table, data=data, header_h=header_h, header_v=header_v, enable=enable)
        table.setEnabled(enable)
        return table
        

class Tree:
    """Utility class for creating and configuring QTreeWidget instances."""
    
    def __init__(self):
        pass    

    def set_tree_data(self, 
        tree: QTableWidget = None, 
        data: dict = {}, 
        expand_all: bool = False, color_or_not: bool = False
    ) -> QTreeWidget:
        """Populate a QTreeWidget with hierarchical data.

        Args:
            tree (QTreeWidget): The tree widget to populate.
            data (dict): Nested dictionary representing tree structure.
                Keys are parent labels, values can be lists, dicts, or strings.
            expand_all (bool, optional): If True, expands all tree nodes. Defaults to False.
            color_or_not (bool, optional): If True, applies background colors to tree items. Defaults to False.

        Returns:
            QTreeWidget: The populated tree widget.
        """
        ...
        tree.clear()
        color = None
        if color_or_not:
            color = Color()
        root = tree.invisibleRootItem()
        for txt_parent, txt_children in data.items():
            parent_item = QTreeWidgetItem(root, [str(txt_parent)])
            if color:
                color.set_bgc(item=parent_item, color_key=color.gray)
            for txt_child in txt_children:
                self.get_tree_data_widget(parent_item=parent_item, children=txt_child, color=color)
        if expand_all:
            tree.expandAll()
            
        return tree
    
    def get_tree_data_widget(
        self, 
        parent_item: QTreeWidgetItem, 
        children: Union[list, dict, str], 
        color: QColor = None
    ) -> None:     
        """Recursively create tree items from hierarchical data.

        Args:
            parent_item (QTreeWidgetItem): The parent item to attach new children to.
            children (Union[list, dict, str]): Child nodes to add. Can be:
                - list: Creates multiple child items under parent.
                - dict: Creates nested parent-child relationships.
                - str: Creates a single child item.
            color (Color, optional): Optional Color helper for setting background colors.
        """  
        if type(children) == list:
            for child in children:
                child_item = QTreeWidgetItem(parent_item, [str(child)])
                if type(child) == dict:
                    self.get_tree_data_widget(parent_item=child_item, children=child)
                
        elif type(children) == dict:           
            for parent, child in children.items():
                child_item = QTreeWidgetItem(parent_item, [str(parent)])
                if color:
                    color.set_bgc(item=child_item, color_key=color.light_gray)
                self.get_tree_data_widget(parent_item=child_item, children=child)
                
        elif type(children) == str:
            child_item = QTreeWidgetItem(parent_item, [str(children)])
                            
    def get_tree(self, data: dict = {}, enable: bool = True, multi: bool = True) -> QTreeWidget:
        """Create and configure a QTreeWidget.

        Args:
            data (dict, optional): Nested dictionary representing tree structure. Defaults to {}.
            enable (bool, optional): Whether the tree is enabled. Defaults to True.
            multi (int, optional): If non-zero, allows multiple item selection.
                Otherwise, only single selection is allowed. Defaults to 1.

        Returns:
            QTreeWidget: Configured tree widget with optional data populated.
        """
        tree = QTreeWidget()
        tree.setContextMenuPolicy(Qt.CustomContextMenu)
        tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tree.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        tree.setIndentation(10)
        tree.headerItem().setText(0, "1")
        tree.header().setVisible(0)       
        tree.setEnabled(enable)
        if data:
            tree = self.set_tree_data(tree=tree, data=data)

        if multi:
            tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        else:
            tree.setSelectionMode(QAbstractItemView.SingleSelection)

        return tree

        
class Ui:
    """Factory class to create and configure common Qt widgets.
    
    Notes:
        This factory class can be used alone,
        but it has ususally inherited to classes named UiVBox, UiHBox.
    
    Attributes:
        img_viewer (ImgViewer): Class to create a viewer.
        table (Table): Class to create table.
        tree (Tree): Class to create table.
    """
    
    def __init__(self):
        self.img_viewer = ImgViewer()
        self.table = Table()
        self.tree = Tree()

    def get_directory_sel(self, q_widget: QWidget = None)->str:
        """Open a directory selection dialog.

        Args:
            q_widget (QWidget|None, optional): Parent widget. Defaults to None.

        Returns:
            str: Selected directory path, or empty string if canceled.
        """
        return QFileDialog.getExistingDirectory(q_widget, 'Select a directory to save', f'{os.getenv("base_root")}/personal')

    def set_size(
        self,
        ui: QWidget = '',
        ui_label: Optional[QLabel]='',
        minWidth: int = 0
    ) -> None:
        """Set sizing policies and minimum widths for widgets.
        """
        
        if ui_label:
            ui_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            ui_label.setMinimumSize(QSize(80, 0))
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(ui.sizePolicy().hasHeightForWidth())
        ui.setSizePolicy(size_policy)
        if minWidth:
            ui.setMinimumSize(QSize(minWidth, 0))

    def get_combobox(
        self,
        label: str = '',
        default: list[str] = [],
        enable: bool = True
    ) -> tuple[QLabel, QComboBox]:
        """Create a labeled QComboBox.
        """
        ui_label = self.get_label(label=label)
        combobox = QComboBox()
        combobox.addItems(default)
        combobox.setCurrentIndex(1)
        self.set_size(ui=combobox, ui_label=ui_label)
        combobox.setEnabled(enable)
        return ui_label, combobox

    def get_chkbox(
        self,
        label: str = '',
        default: int = 0,
        enable: bool = True,
        fontsize: int = 12,
        height: int = 20
    ) -> QCheckBox:
        """Create a QCheckBox with label and styling.
        """
        chkbox = QCheckBox(label)
        if default:
            chkbox.setChecked(True)
        else:
            chkbox.setChecked(False)
        chkbox.setStyleSheet(f"""
            QCheckBox {{
                font-size: {str(fontsize)}px;
            }}
        """)
        chkbox.setFixedHeight(height)
        chkbox.setEnabled(enable)
        return chkbox

    def get_button(
        self,
        label: str = '',
        enable: bool = True,
        width: int = 100
    ) -> QPushButton:
        """Create a QPushButton with minimum width.
        """
        btn = QPushButton(label)
        btn.setMinimumWidth(width)
        btn.setEnabled(enable)
        return btn

    def get_label(self, label: str = '') -> QLabel:
        """Create a QLabel.
        """
        return QLabel(label)

    def get_field(
        self,
        label: str = '',
        default: str = '',
        enable: bool = True,
        limit_exp: str = ''
    ) -> tuple[QLabel, QLineEdit]:
        """Create a labeled QLineEdit with optional input validation.
        """
        ui_label = self.get_label(label=label)
        field = QLineEdit()
        if default:
            field.setText(default)
        self.set_size(ui=field, ui_label=ui_label)
        field.setEnabled(enable)
        if limit_exp:
            regex1 = QRegExp(limit_exp)
            validator1 = QRegExpValidator(regex1)
            field.setValidator(validator1)
        return ui_label, field

    def get_date(self, label: str = 'Date :', enable: bool = True):
        """Create a labeled date-time field.
        """
        if label:
            ui_label = self.get_label(label=label)
        date_field = QDateTimeEdit()
        current_datetime = QDateTime.currentDateTime()
        date_field.setDateTime(current_datetime)
        date_field.setDisplayFormat("yy-MM-dd hh:mm AP")
        date_field.setCalendarPopup(1)
        self.set_size(ui=date_field, ui_label=ui_label)
        date_field.setEnabled(enable)
        return ui_label, date_field


class UiHbox(QHBoxLayout):
    """Horizontal layout helper with UI widget builders.
    
    Base Classes:
        QHBoxLayout: Use as one QHBoxLayout, but including custom ui items.
        
    Notes:
        This can be used a BoxLayout including ui items with its own parent constraints.
    
    Attributes:
        parent (Optional[QWidget, QVBoxLayout, QHBoxLayout]): Parent layout to be added.
        ui (Ui): Class of ui factory to create ui items.
    """
    
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.ui = Ui()
        if parent is not None:
            parent.addLayout(self)

    def get_h_combobox(
        self,
        label: str = '',
        default: list[str] = [],
        enable: bool = True
    ) -> QComboBox:
        """Add a horizontal labeled QComboBox to the layout.
        """
        ui_label, combobox = self.ui.get_combobox(label=label, default=default, enable=enable)
        self.addWidget(ui_label)
        self.setAlignment(ui_label, Qt.AlignRight)
        self.addWidget(combobox)
        return combobox

    def get_v_field(
        self,
        label: str = '',
        default: str = '',
        enable: bool = True,
        limit_exp: str = ''
    ) -> QLineEdit:
        """Add a labeled QLineEdit vertically aligned inside the layout.
        """
        ui_label, field = self.ui.get_field(label=label, default=default, enable=enable, limit_exp=limit_exp)
        self.addWidget(ui_label)
        self.setAlignment(ui_label, Qt.AlignRight)
        self.addWidget(field)
        return field

    def get_h_img_viewer(
        self,
        q_widget: Optional[QWidget] = None,
        path_dir: str = '',
        size: tuple[int, int] = (300, 150)
    ) -> tuple[QWidget, QSlider]:
        """Add an image viewer with slider in horizontal layout.
        """
        viewer, slider = self.ui.img_viewer.get_img_seq_viewer(q_widget=q_widget)
        if size:
            viewer.setFixedSize(size[0], size[1])
            viewer.setStyleSheet("background: gray")
        if path_dir:
            slider = self.ui.img_viewer.set_img_seq_viewer(viewer=viewer, slider=slider, path_dir=path_dir)        
        # self.ui.img_viewer.get_show_img_seq_frame(index=0, frame_count=frame_count, viewer=viewer)
        self.addWidget(viewer)
        self.addWidget(slider)
        return viewer, slider

    def get_h_date(
        self,
        label: str = '',
        enable: bool = True
    ) -> QDateTimeEdit:
        """Add a labeled QDateTimeEdit in horizontal layout.
        """
        ui_label, date_field = self.ui.get_date(label=label, enable=enable)
        if ui_label:
            self.addWidget(ui_label)
        self.addWidget(date_field)
        return date_field

    def get_h_chkbox(
        self,
        label: str = '',
        default: int = 0,
        enable: bool = True,
        fontsize: int = 12,
        height: int = 20
    ) -> QCheckBox:
        """Add a QCheckBox in horizontal layout.
        """
        chkbox = self.ui.get_chkbox(label=label, default=default, enable=enable, fontsize=fontsize, height=height)
        self.addWidget(chkbox)
        return chkbox

    def get_h_button(
        self,
        label: str = '',
        enable: bool = True
    ) -> QPushButton:
        """Add a QPushButton in horizontal layout.
        """
        btn = self.ui.get_button(label=label, enable=enable)
        self.addWidget(btn)
        return btn

    def get_h_tree(
        self,
        data: dict = {},
        enable: bool = True,
        multi: bool = True
    ) -> QTreeWidget:
        """Add a QTreeWidget in horizontal layout.
        """
        tree = self.ui.tree.get_tree(data=data, enable=enable, multi=multi)
        self.addWidget(tree)
        return tree

    def get_h_table(
        self,
        data: list = [],
        header_h: list = [],
        header_v: list = [],
        enable: bool = True
    ) -> QTableWidget:
        """Add a QTableWidget in horizontal layout.
        """
        table = self.ui.table.get_table(data=data, header_h=header_h, header_v=header_v, enable=enable)
        self.addWidget(table)
        return table


class UiVbox(QVBoxLayout):
    """Vertical layout helper with UI widget builders.
    
    Base Classes:
        QHBoxLayout: Use as one QHBoxLayout, but including custom ui items.
        
    Notes:
        This can be used a BoxLayout including ui items with its own parent constraints.
    
    Attributes:
        parent (Optional[QWidget, QVBoxLayout, QHBoxLayout]): Parent layout to be added.
        ui (Ui): Class of ui factory to create ui items. 
    """
    
    def __init__(self, parent=None):
        super().__init__()
        self.ui = Ui()
        if parent is not None:
            parent.addLayout(self)

    def get_v_combobox(
        self,
        label: str = '',
        default: list[str] = [],
        enable: bool = True
    ) -> QComboBox:
        """Add a labeled QComboBox in vertical layout.
        """
        ui_label, combobox = self.ui.get_combobox(label=label, default=default, enable=enable)
        self.addWidget(ui_label)
        self.addWidget(combobox)
        return combobox

    def get_v_date(
        self,
        label: str = '',
        enable: bool = True
    ) -> QDateTimeEdit:
        """Add a labeled QDateTimeEdit in vertical layout.
        """
        ui_label, date_field = self.ui.get_date(label=label, enable=enable)
        if ui_label:
            self.addWidget(ui_label)
        self.addWidget(date_field)
        return date_field

    def get_v_field(
        self,
        label: str = '',
        default: str = '',
        enable: bool = True,
        limit_exp: str = ''
    ) -> QLineEdit:
        """Add a labeled QLineEdit in vertical layout.
        """
        ui_label, field = self.ui.get_field(label=label, default=default, enable=enable,limit_exp=limit_exp)
        self.addWidget(ui_label)
        self.addWidget(field)
        return field

    def get_v_img_viewer(
        self,
        q_widget: Optional[QWidget] = None,
        path_dir: str = '',
        size: tuple[int, int] = (300, 150),
        bgc: str = 'gray'
    ) -> tuple[QWidget, QSlider]:
        """Add an image viewer with slider in vertical layout.
        """
        viewer, slider = self.ui.img_viewer.get_img_seq_viewer(q_widget=q_widget)
        if size:
            viewer.setFixedSize(size[0], size[1])
            viewer.setStyleSheet(f"background: {bgc}")
        if path_dir:
            slider = self.ui.img_viewer.set_img_seq_viewer(viewer=viewer, slider=slider, path_dir=path_dir)        
        self.addWidget(viewer)
        self.addWidget(slider)
        return viewer, slider

    def get_v_table(
        self,
        data: list = [],
        header_h: list = [],
        header_v: list = [],
        enable: bool = True
    ) -> QTableWidget:
        """Add a QTableWidget in vertical layout.
        """
        table = self.ui.table.get_table(data=data, header_h=header_h, header_v=header_v, enable=enable)
        self.addWidget(table)
        return table

    def get_v_chkbox(
        self,
        label: str = '',
        default: int = 0,
        enable: bool = True,
        fontsize: int = 12,
        height: int = 20
    ) -> QCheckBox:
        """Add a QCheckBox in vertical layout.
        """
        chkbox = self.ui.get_chkbox(label=label, default=default, enable=enable, fontsize=fontsize, height=height)
        self.addWidget(chkbox)
        return chkbox
      
    def get_v_button(
        self,
        label: str = '',
        enable: bool = True
    ) -> QPushButton:
        """Add a QPushButton in vertical layout.
        """
        btn = self.ui.get_button(label=label, enable=enable)
        self.addWidget(btn)
        return btn

    def get_v_tree(
        self,
        data: dict = {},
        enable: bool = True,
        multi: bool = True
    ) -> QTreeWidget:
        """Add a QTreeWidget in vertical layout.
        """
        tree = self.ui.tree.get_tree(data=data, enable=enable, multi=multi)
        self.addWidget(tree)
        return tree
