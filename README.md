# Multicam 3D Visibility Workbench

A local Python desktop simulator for calibrated multi-camera images, visible surface area, overlap and blind regions. Built with PySide6, PyVista/VTK, OpenCV, Trimesh and CadQuery. Geometry uses millimeters; areas use mm².

## Windows quick start

Python 3.12 and a desktop with working OpenGL are required. On the configured workstation, double-click `start_windows.bat`. It uses the isolated project environment `.conda-env` created with Anaconda. The startup dialog lets you choose the interface language and enable live preview.

For a fresh checkout with Anaconda:

```powershell
conda create --prefix .\.conda-env python=3.12 pip -y
conda activate .\.conda-env
python -m pip install -r requirements.txt
python app.py
```

Alternatively, install Python 3.12 with the Python Launcher and double-click `start_windows.bat`; it creates `.venv` and installs dependencies on first run. If installation is interrupted, rerun `python -m pip install -r requirements.txt` in that environment.

## Language and live preview

English is the default at each launch. Select **English / 中文** from the dropdown on the startup dialog or main window. Switching languages preserves the current scene, poses, calibration and results.

Enable **Live camera preview** to automatically update ray images after scene changes. Changes are debounced and computed on a background thread. Only one computation runs at a time; outdated results are discarded and the latest scene is refreshed afterward. Rendering speed depends on scene complexity and image resolution; this is not a fixed video frame rate. Live mode starts at 160 px for responsiveness. Increase **Image width px** for detail. Coverage evaluation remains an explicit action.

## Keyboard model controls

Select a model in **Scene / Test board**, enable **Keyboard model control**, then click the 3D viewport. Shortcuts apply only inside that viewport, so editing numeric fields does not move models.

| Action | Keys | Axis / Direction |
| --- | --- | --- |
| Translate | W / S | +X / -X |
| Translate | A / D | -Y / +Y |
| Translate | Q / E | -Z / +Z |
| Rotate | I / K | +X / -X |
| Rotate | J / L | +Y / -Y |
| Rotate | U / O | +Z / -Z |
| Faster steps | Hold Shift | 5× configured step |
| Fit scene | F | Reset navigation view |

Set **Move step mm** and **Rotate step deg** to control precision. Rotation adjusts the model's XYZ Euler angles. Cameras are independent objects and do not follow a moved housing automatically. Mouse drag and wheel retain the normal orbit/zoom controls.

## Workflow

1. Load one of five supplied layouts, or import STEP/STP, STL, OBJ, PLY, GLB/GLTF or NPZ meshes.
2. Assign roles: `housing` and `occluder` block rays; `target` also contributes to measured area. Disable objects to exclude them from display and computation.
3. Set model scale and pose. Position cameras using surface picking and pose fields; import JSON, YAML, OpenCV YAML/XML or Markdown calibration.
4. Create a test board or import a scaled target. Align real photos and the scene before using observed-region masks.
5. Use live preview or **Update images**. Choose **Evaluate coverage** for sampled visible area, overlap and blind surface.
6. Save a self-contained `.mcv` project or export images, masks, ray distances, metrics and coverage point clouds.

Images are simplified geometric simulations. Area is estimated by surface sampling, includes all target surfaces (including backs), and does not measure reconstruction accuracy. Increase sampling to assess convergence. Imported mesh units must be checked against known physical dimensions. The camera convention is +Z forward, +X right, +Y down.

## Development

```powershell
python -m unittest discover -s tests -v
```

Tests include core geometry, keyboard manipulation, runtime language switching, live preview and stale-result rejection. GUI tests need a desktop/OpenGL session. Linux startup is available through `bash start_linux.sh`.

The project environment, caches and local secrets are excluded from Git. No system-wide Python or PATH change is required. The Windows application uses native VTK diagnostic output to avoid recursive PyVista log callbacks during window events.

See [the Chinese workflow guide](README.zh-CN.md) for detailed calibration, geometry and export notes.
