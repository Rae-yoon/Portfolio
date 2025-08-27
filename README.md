# Animation / VFX Pipiline TD Portfolio

This repository showcases a collection of **pipeline tools** 
developed for animation and VFX production envrionments.
All tools and modules were designed for real production use.

- All credentials and values are dummy placeholders for demo purpose.
---

## Main tool
- **turn_track**
    - Developed Turn Track, a studio render tool that automates turntable workflows through Tractor integration, USD/Flow(ShotGrid) sync, and modular UI design. 

## Key Features

- **Usd Utilities**
    - Cached access to Pixar USD Stage and Layer
    - Optimized repeated loading

- **Flow(ShotGrid) Integration**
    - Query, update, and sync shot/asset data
    - Generate direct links to sequence/shot pages

- **Perforce Utilities**
    - Path conversion across depot/public/home
    - Error handling and path utilities

- **Rendering Tools**
    - Automated turntable rendering pipeline
    - Tractor job log and submission scripts

- **UI Modules (PyQt5)**
    - Artist-friendly tool interfaces
    - Utility classes for colors and widgets

- **Logging Infrastructure**
    - Colorized console logs and rotating file logs
    - Single and Multiprocess(Queue-based) logging support

- **Core Utilities**
    - Command execution and file I/O
    - Terminal/environment management


## Tech Stack

- **Environment Management**:
    - Rocky Linux 9.2 (Blue Onyx)
    - Desktop Manager (GNOME)

- **Language**: Python 3.9.16

- **DCC & Pipeline**:
    - Maya (2024.2)
    - Pixar USD
    - Flow/ShotGrid (Shotgun API3)
    - Perforce (P4Python)
    - Tractor 2.3/2.4

- **UI**:
    - PyQt5


## Project Structure
```text
/project
├── config
│   ├── public.sh        # Public environment
│   └── .flow.env        # Flow/ShotGrid environment
├── home                 # Perforce user home
│   └── rae              # User workspace (where the user can sync and edit files from the public area)
├── logs
│   └── turn_track       # Logs for turn_track
│       └── rae
│           ├── PID_9952        # PID 9952 rendering logs
│           │   ├── turn_track.preprocess.1.log
│           │   ├── turn_track.render.1.log
│           │   ├── ...
│           │   └── turn_track.render.100.log
│           └── turn_track.log   # Main turn_track log, organized by date
├── personal
│   └── .personal.sh     # Personal environment
├── public               # Perforce public space
│   ├── bin              # Executables
│   │   ├── maya
│   │   │   └── turntable.py
│   │   └── turn_track   # **Main exe for Turn Track**
│   ├── data
│   │   ├── asset        # USD assets
│   │   │   ├── char
│   │   │   │   ├── boy
│   │   │   │   │   ├── latest -> v002
│   │   │   │   │   ├── stable -> v002
│   │   │   │   │   ├── v001
│   │   │   │   │   │   └── boy.usd
│   │   │   │   │   └── v002
│   │   │   │   │       └── boy.usd
│   │   │   │   └── girl
│   │   │   │       └── ...
│   │   │   └── prop
│   │   │       └── ...
│   │   ├── asset_origin # Source Maya assets
│   │   │   ├── char
│   │   │   │   ├── boy
│   │   │   │   │   ├── v001
│   │   │   │   │   │   └── boy_v001.mb
│   │   │   │   │   └── v002
│   │   │   │   │       └── boy_v002.mb
│   │   │   │   └── ...
│   │   │   └── ...
│   │   ├── model        # Shot-specific asset models
│   │   │   ├── s0010
│   │   │   │   ├── 0010
│   │   │   │   │   ├── boy
│   │   │   │   │   │   ├── current -> v002
│   │   │   │   │   │   ├── v001
│   │   │   │   │   │   │   └── boy.usd
│   │   │   │   │   │   └── v002
│   │   │   │   │   │       └── boy.usd
│   │   │   │   │   └── ...
│   │   │   │   └── ...
│   │   │   └── ...
│   │   └── shot         # USD shots
│   │       ├── s0010
│   │       │   ├── 0010
│   │       │   │   └── shot.usd
│   │       │   └── 0020
│   │       │       └── shot.usd
│   │       └── s0020
│   │           └── 0010
│   │               └── shot.usd
│   ├── lib              # Public API
│   │   ├── asset.py
│   │   ├── core.py
│   │   ├── log.py
│   │   ├── perforce.py
│   │   ├── shot.py
│   │   ├── ui.py
│   │   ├── usd_utils.py
│   │   ├── render       # Rendering APIs
│   │   │   ├── render_core.py
│   │   │   └── render_turntable.py
│   │   └── templates    # Templates
│   │       └── maya
│   │           └── template_turntable.mb
│   └── render           # Rendered results
│       ├── asset        # Asset renders
│       │   ├── logs     # Asset render logs
│       │   │   ├── char_boy_v002_td_rae_2025_08_21_12_40_39.alf
│       │   │   └── char_boy_v002_td_rae_2025_08_21_12_40_39.sh
│       │   └── turntable
│       │       └── char
│       │           └── boy
│       │               └── v002        # Asset turntable results
│       │                   ├── tmp    # Temp Maya files for batch rendering
│       │                   │   └── turntable_boy_v002.mb
│       │                   ├── turntable_boy_v002.0001.png
│       │                   ├── ...
│       │                   └── turntable_boy_v002.0100.png
│       └── shot         # Shot renders
│           └── logs     # Shot render logs
└── readme.md
```

## Environment Setup

### 1) Modify ./personal/.personal.sh file properly by your name and department.
```bash
export user='user_name'
export dept='user_department'
export base_home=$base_root/home/$user # do not modify this line
``` 

### 2) Run the environment files.

```bash
export project='Replace with your root path'
# in public.sh : export base_root="{$project}/project"
cd $project
source ./config/public.sh && source ./personal/.personal.sh     
```

## Run
You can run the main turn_track tool by entering the following command in the terminal.  
Make sure that the `PYTHONPATH` has been set correctly via `public.sh`:
```bash
turn_track
```


