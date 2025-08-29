#!/bin/bash

# base
export base_root="{$project}/project"
export base_logs="$base_root/logs"
export base_config="$base_root/config"
export base_public="$base_root/public"

export base_bin="$base_public/bin"
export base_lib="$base_public/lib"
export base_render="$base_public/render"
export base_render_asset="$base_render/asset"
export base_render_asset_logs="$base_render_asset/logs"
export base_render_shot="$base_render/shot"
export base_data="$base_public/data"
export base_asset="$base_data/asset"
export base_asset_origin="$base_data/asset_origin"
export base_model="$base_data/model"
export base_shot="$base_data/shot"

# exe
export exe_sh="/bin/bash"
export exe_py="/usr/bin/python"
# export P4PORT="192.000.00.000:1666"
export m24_py="/usr/autodesk/maya2024/bin/mayapy"
export m24_render="/usr/autodesk/maya2024/bin/Render"

# Tractor
export tractor_root="/opt/pixar/Tractor-2.3"
export tractor_spool="/opt/pixar/Tractor-2.3/bin/tractor-tractor_spool"
# export TRACTOR_ENGINE="192.000.000.000"

# PYTHONPATH, USD
export PATH="$base_bin:$PATH"
export PYTHONPATH="$base_bin:$base_lib:$base_public:$base_home:$PYTHONPATH"
export PXR_AR_DEFAULT_SEARCH_PATH="$base_shot:$base_lib:$base_data"
