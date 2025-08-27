
#!/bin/sh


set -a
source /home/user_rae/Documents/project/config/public.sh
set +a
        
export r_title="Maya Render Assets | turntable | char - boy_v002"
export r_priority=120
export r_projects=CUSTOM_PROJECT
export r_cmt="turntable test 1"
export r_envkey=maya
export r_tags=td
export r_servicekey=RENDER
        


export tt_cam=turntable_cam


export tt_grp=turntable_asset_grp
export tt_sh=/home/user_rae/Documents/project/public/render/asset/logs/char_boy_v002_td_rae_2025_08_21_18_11_56.sh        
export tt_alf=
export tt_template=/home/user_rae/Documents/project/public/lib/templates/maya/template_turntable.mb
export tt_type=char
export tt_name=boy
export tt_ver=v002
export tt_target_maya=/home/user_rae/Documents/project/public/data/asset_origin/char/boy/v002/boy_v002.mb
export tt_dest_dir=/home/user_rae/Documents/project/public/render/asset/turntable

export PYTHONPATH="$base_bin:$base_lib:$base_public:$base_home"

                
/home/user_rae/Documents/project/public/bin/maya/turntable.py $1 $2 $3 $4 $5
        