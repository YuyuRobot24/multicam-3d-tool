# Multicam 3D Visibility Workbench

A local Python desktop simulator for calibrated multi-camera images, visible surface area, overlap and blind regions. Built with PySide6, PyVista/VTK, OpenCV, Trimesh and CadQuery. Geometry uses millimeters; areas use mm².

## Windows quick start

Python 3.12 and a desktop with working OpenGL are required. On the configured workstation, double-click `start_windows.bat`. It uses the isolated project environment `.conda-env` created with Anaconda and opens the main window directly.

For a fresh checkout with Anaconda:

```powershell
conda create --prefix .\.conda-env python=3.12 pip -y
conda activate .\.conda-env
python -m pip install -r requirements.txt
python app.py
```

Alternatively, install Python 3.12 with the Python Launcher and double-click `start_windows.bat`; it creates `.venv` and installs dependencies on first run. If installation is interrupted, rerun `python -m pip install -r requirements.txt` in that environment.

## Language, camera images and evaluation

The default four-camera layout is shown in a 2×2 overview, so all cameras can be compared at once. Other layouts display their available cameras in the same grid. Displayed and exported simulated images are undistorted pinhole views using the original focal length; unsupported borders remain black. Depth, target masks and object IDs use the same corrected pixel coordinates. Exports include the corrected display calibration. Original calibration and photo-region masks remain unchanged for geometric visibility evaluation.

The evaluation panel reports **joint coverage**, not separate camera footprints: union area / target area, union width × height on a single test board, multi-camera overlap area / union area, blind area, and every camera pair's IoU (intersection / union). Undefined overlap for two empty views is shown as a dash. Width × height is a sampled bounding extent, not filled area; general curved targets use world-coordinate bounds in the log. Exported `camera_overlap.csv` and `combined_coverage.json` contain these joint metrics.

English is the default at each launch. Select **English / 中文** from the main-window dropdown. Switching languages preserves the current scene, poses, calibration and results.

Press **Update images** to render camera images or **Evaluate coverage** to render images and calculate joint metrics. Computation runs on a background thread. Scene edits invalidate previous results and exports; an in-flight outdated result is discarded. Further computation requires another button press. Set **Image width px** for image detail.

## Mouse model controls

Click a model in the 3D viewport to select it and open the **Interaction** tab. Selection shows a colored transform manipulator on the model. Drag a straight arrow to translate along its world axis; drag a curved arc to rotate about that axis around the model center. Red represents X / Roll, green Y / Pitch, and blue Z / Yaw.

The **Interaction** tab also provides negative/positive arrow buttons for X, Y, Z, Roll, Pitch and Yaw. Set **Move step mm** and **Rotate step deg** for precise increments. Numeric pose fields show XYZ position and XYZ Euler angles as Roll/Pitch/Yaw; rotations use the existing right-handed extrinsic XYZ convention. Manipulator changes are committed to the scene when the mouse is released and are saved in `.mcv` projects.

Cameras are independent objects and do not follow a moved housing automatically. Mouse drag away from the handles and the wheel retain orbit/zoom navigation. Use **Fit scene** to reset the navigation view. To place a camera, press **Place on surface** and click a model surface.

## Workflow

1. Load one of five supplied layouts, or import STEP/STP, STL, OBJ, PLY, GLB/GLTF or NPZ meshes.
2. Assign roles: `housing` and `occluder` block rays; `target` also contributes to measured area. Disable objects to exclude them from display and computation.
3. Set model scale and pose. Position cameras using surface picking and pose fields; import JSON, YAML, OpenCV YAML/XML or Markdown calibration.
4. Create a test board or import a scaled target. Align real photos and the scene before using observed-region masks.
5. Press **Update images**. Choose **Evaluate coverage** for sampled visible area, overlap and blind surface.
6. Save a self-contained `.mcv` project or export images, masks, ray distances, metrics and coverage point clouds.

Images are simplified geometric simulations. Area is estimated by surface sampling, includes all target surfaces (including backs), and does not measure reconstruction accuracy. Increase sampling to assess convergence. Imported mesh units must be checked against known physical dimensions. The camera convention is +Z forward, +X right, +Y down.

## Development

```powershell
python -m unittest discover -s tests -v
```

Tests include core geometry, mouse picking and transforms, precision buttons, runtime language switching, manual preview and stale-result rejection. GUI tests need a desktop/OpenGL session. Linux startup is available through `bash start_linux.sh`.

The project environment, caches and local secrets are excluded from Git. No system-wide Python or PATH change is required. The Windows application uses native VTK diagnostic output to avoid recursive PyVista log callbacks during window events.

See [the Chinese workflow guide](README.zh-CN.md) for detailed calibration, geometry and export notes.
