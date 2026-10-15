"""Local Qt / VTK multi-camera visibility workbench."""
import os,sys,json,copy,csv,traceback
from pathlib import Path
os.environ.setdefault('QT_API','pyside6')
import numpy as np,cv2,trimesh
from scipy.spatial.transform import Rotation
from PySide6 import QtWidgets as W,QtCore as C,QtGui as G
import pyvista as pv
from pyvistaqt import QtInteractor
if sys.platform == 'win32':
 # Avoid recursive PyVista log callbacks during native VTK window events.
 from vtkmodules.vtkCommonCore import vtkOutputWindow
 vtkOutputWindow.SetInstance(vtkOutputWindow())
from engine import *
from i18n import t, language_menu, translate_widgets
ROOT=Path(__file__).resolve().parent

class LaunchDialog(W.QDialog):
 def __init__(self):
  super().__init__();self.setWindowTitle(t('Multicam 3D - Start'));self.resize(520,300)
  layout=W.QVBoxLayout(self);self.language=language_menu(self,layout);layout.addWidget(W.QLabel(t('<h2>Multicam 3D Workbench</h2>')))
  help=W.QLabel(t('Inspect calibrated camera views and geometric coverage.\n\nSelect a model, then click the 3D viewport.\nMove: W/S = +/-X, A/D = -/+Y, Q/E = -/+Z\nRotate: I/K = +/-X, J/L = +/-Y, U/O = +/-Z\nHold Shift for 5x steps. F = fit scene.\nKeyboard input is active only in the 3D viewport.'))
  help.setWordWrap(True);layout.addWidget(help)
  self.live=W.QCheckBox(t('Enable live camera preview'));self.live.setChecked(True);layout.addWidget(self.live)
  buttons=W.QDialogButtonBox(W.QDialogButtonBox.StandardButton.Ok|W.QDialogButtonBox.StandardButton.Cancel);buttons.button(W.QDialogButtonBox.StandardButton.Ok).setText(t('Start simulator'));buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);layout.addWidget(buttons);translate_widgets(self)

class RoiView(W.QGraphicsView):
 def __init__(self,image):
  super().__init__();self.image=image;self.points=[];self.scene_=W.QGraphicsScene(self);self.setScene(self.scene_);h,w=image.shape[:2];q=G.QImage(np.ascontiguousarray(image).data,w,h,w*3,G.QImage.Format.Format_RGB888).copy();self.scene_.addPixmap(G.QPixmap.fromImage(q));self.poly=None;self.setRenderHint(G.QPainter.RenderHint.Antialiasing)
 def mousePressEvent(self,event):
  p=self.mapToScene(event.position().toPoint());h,w=self.image.shape[:2]
  if event.button()==C.Qt.MouseButton.LeftButton and 0<=p.x()<w and 0<=p.y()<h:self.points.append((p.x(),p.y()))
  elif event.button()==C.Qt.MouseButton.RightButton and self.points:self.points.pop()
  self.redraw()
 def redraw(self):
  if self.poly:self.scene_.removeItem(self.poly);self.poly=None
  if self.points:self.poly=self.scene_.addPolygon(G.QPolygonF([C.QPointF(*p) for p in self.points]),G.QPen(G.QColor('#ffca28'),2),G.QBrush(G.QColor(255,202,40,50)))
 def resizeEvent(self,e):super().resizeEvent(e);self.fitInView(self.scene_.sceneRect(),C.Qt.AspectRatioMode.KeepAspectRatio)

class RoiDialog(W.QDialog):
 def __init__(self,image,parent):
  super().__init__(parent);self.setWindowTitle(t('Observed region: left-click to add, right-click to undo'));self.resize(950,700);l=W.QVBoxLayout(self);l.addWidget(W.QLabel(t('Align the camera and model with the photo. Scale comes from the 3D scene.')));self.view=RoiView(image);l.addWidget(self.view);b=W.QDialogButtonBox(W.QDialogButtonBox.StandardButton.Ok|W.QDialogButtonBox.StandardButton.Cancel);b.accepted.connect(self.finish);b.rejected.connect(self.reject);l.addWidget(b)
 def finish(self):
  if len(self.view.points)<3:W.QMessageBox.warning(self,t('Incomplete region'),t('Select at least three vertices.'));return
  self.accept()
 def mask(self):
  mask=np.zeros(self.view.image.shape[:2],np.uint8);cv2.fillPoly(mask,[np.rint(self.view.points).astype('int32')],255);return mask

class ComputeWorker(C.QThread):
 done=C.Signal(object);failed=C.Signal(str);progress=C.Signal(str)
 def __init__(self,objects,cameras,width,samples,area):
  super().__init__();self.objects=copy.deepcopy(objects);self.cameras=copy.deepcopy(cameras);self.width=width;self.samples=samples;self.area=area
 def run(self):
  try:
   scene=build_scene(self.objects);images=[]
   for c in self.cameras:
    if self.isInterruptionRequested():return
    if c.active:self.progress.emit(t('Rendering: ')+c.name);images.append((c.name,render_camera(self.objects,c,self.width,scene)))
   result={'images':images,'metrics':None}
   if self.area:
    self.progress.emit(t('Calculating coverage, overlap and blind areas...'));result['metrics'],result['points'],result['counts']=evaluate(self.objects,self.cameras,self.samples,scene)
   self.done.emit(result)
  except Exception:self.failed.emit(traceback.format_exc())

class MainWindow(W.QMainWindow):
 def __init__(self):
  super().__init__();self.setWindowTitle(t('Multicam 3D Visibility Workbench - mm'));self.resize(1550,940)
  self.objects=[];self.cameras=[];self.last=None;self.worker=None;self.revision=0;self.picking=False;self.updating=False
  split=W.QSplitter();self.setCentralWidget(split);left=W.QWidget();lv=W.QVBoxLayout(left);left.setMinimumWidth(300);left.setMaximumWidth(390);split.addWidget(left)
  title=W.QLabel(t('Multicam 3D Workbench'));title.setStyleSheet('font-size:21px;font-weight:600;color:#0f766e');lv.addWidget(title)
  note=W.QLabel(t('Length mm - Angles deg - Area mm2\nCamera: +Z forward, +X right, +Y down'));lv.addWidget(note)
  self.language=language_menu(self,lv)
  bar=W.QHBoxLayout();self.preset=W.QComboBox();self.preset.addItems([f'Layout {i:02}' for i in range(1,6)]);bar.addWidget(self.preset);self.button(bar,t('Load example'),self.load_example);lv.addLayout(bar)
  tabs=W.QTabWidget();lv.addWidget(tabs)
  models=W.QWidget();ml=W.QVBoxLayout(models);mscroll=W.QScrollArea();mscroll.setWidgetResizable(True);mscroll.setWidget(models);tabs.addTab(mscroll,t('Scene / Test board'))
  self.objlist=W.QListWidget();self.objlist.currentRowChanged.connect(self.object_selected);ml.addWidget(self.objlist)
  row=W.QHBoxLayout();self.button(row,t('Import model'),self.import_object);self.button(row,t('Delete'),self.remove_object);ml.addLayout(row)
  self.role=W.QComboBox();self.role.setObjectName('roleMenu')
  for role in ['housing','target','occluder']:self.role.addItem(t(role),role)
  self.role.currentIndexChanged.connect(self.object_changed);ml.addWidget(W.QLabel(t('Role: housing / measured target / occluder')));ml.addWidget(self.role)
  self.enabled=W.QCheckBox(t('Enabled (visible and occluding)'));self.enabled.stateChanged.connect(self.object_changed);ml.addWidget(self.enabled)
  self.objfields=self.pose_fields(ml,self.object_changed)
  self.scale=self.number(1,.000001,100000,6);self.scale.valueChanged.connect(self.object_changed);f=W.QFormLayout();f.addRow(t('Unit conversion / Scale'),self.scale);ml.addLayout(f)
  row=W.QHBoxLayout();self.button(row,t('Center in test area'),self.center_target);self.button(row,t('Fit scene'),lambda:self.draw(True));ml.addLayout(row)
  ml.addWidget(W.QLabel(t('Test board (local XY plane)')))
  f=W.QFormLayout();self.bw=self.number(50,1,2000);self.bh=self.number(50,1,2000);self.bd=self.number(50,.1,2000);self.tipx=self.number(-157);f.addRow(t('Tip reference X mm'),self.tipx);f.addRow(t('Width mm'),self.bw);f.addRow(t('Height mm'),self.bh);f.addRow(t('Distance from tip -X mm'),self.bd);ml.addLayout(f)
  self.button(ml,t('Create / Reset board'),self.make_board)
  self.button(ml,t('Load curved demo'),self.demo_surface)
  ml.addWidget(W.QLabel(t('Set imported teeth/head to target; disable the board if needed. All target surfaces count, including the back.')))
  ml.addStretch()
  cams=W.QWidget();cl=W.QVBoxLayout(cams);cscroll=W.QScrollArea();cscroll.setWidgetResizable(True);cscroll.setWidget(cams);tabs.addTab(cscroll,t('Cameras'))
  self.camlist=W.QListWidget();self.camlist.currentRowChanged.connect(self.camera_selected);cl.addWidget(self.camlist)
  row=W.QHBoxLayout();self.button(row,t('Place on surface'),self.start_pick);self.button(row,t('Duplicate'),self.clone_camera);self.button(row,t('Delete'),self.remove_camera);cl.addLayout(row)
  self.camactive=W.QCheckBox(t('Include in images and coverage'));self.camactive.stateChanged.connect(self.camera_changed);cl.addWidget(self.camactive)
  self.camfields=self.pose_fields(cl,self.camera_changed)
  row=W.QHBoxLayout();self.button(row,t('Flip optical axis'),self.flip_camera);self.button(row,t('View from camera'),self.look_camera);cl.addLayout(row)
  f=W.QFormLayout();self.offset=self.number(0,-100,100,2);f.addRow(t('Optical axis offset mm'),self.offset);cl.addLayout(f);self.button(cl,t('Apply offset'),self.offset_camera)
  self.klabel=W.QLabel();self.klabel.setWordWrap(True);cl.addWidget(self.klabel)
  row=W.QHBoxLayout();self.button(row,t('Import calibration'),lambda:self.import_intrinsics(False));self.button(row,t('Apply to all'),lambda:self.import_intrinsics(True));cl.addLayout(row)
  cl.addWidget(W.QLabel(t('JSON / YAML / OpenCV YAML / Markdown report. The 3D view is a guide; ray images use full calibration.')));cl.addStretch()
  run=W.QGroupBox(t('Compute'));rl=W.QVBoxLayout(run);lv.addWidget(run)
  f=W.QFormLayout();self.res=W.QComboBox();self.res.addItems(['160','320','640','1280']);self.res.setCurrentText('320');self.samples=W.QComboBox();self.samples.addItems(['2000','10000','50000']);self.samples.setCurrentText('10000');f.addRow(t('Image width px'),self.res);f.addRow(t('Area samples'),self.samples);self.frustum_length=self.number(50,1,2000);self.frustum_length.valueChanged.connect(lambda _:self.draw());f.addRow(t('Camera guide length mm'),self.frustum_length);rl.addLayout(f)
  row=W.QHBoxLayout();self.preview_button=self.button(row,t('Update images'),lambda:self.compute(False));self.eval_button=self.button(row,t('Evaluate coverage'),lambda:self.compute(True));rl.addLayout(row)
  row=W.QHBoxLayout();self.button(row,t('Save project'),self.save_project);self.button(row,t('Open project'),self.open_project);self.export_button=self.button(row,t('Export results'),self.export_results);rl.addLayout(row);self.export_button.setEnabled(False)
  self.status=W.QLabel(t('Ready'));self.status.setWordWrap(True);lv.addWidget(self.status)
  center=W.QSplitter(C.Qt.Orientation.Vertical);split.addWidget(center)
  self.viewer=QtInteractor(self,off_screen=os.environ.get('MCV_OFFSCREEN')=='1');center.addWidget(self.viewer.interactor);self.viewer.set_background('#edf2f6');self.viewer.add_axes();
  if os.environ.get('MCV_OFFSCREEN')!='1':self.viewer.enable_surface_point_picking(callback=self.picked,use_picker=True,picker='cell',left_clicking=True,show_point=False,show_message=False)
  self.viewer.add_text('Mouse: orbit / zoom | Surface picking: enable on the left',font_size=10,color='#233c4d',position='upper_left',name='hint')
  self.bottom=W.QTabWidget();center.addWidget(self.bottom)
  self.table=W.QTableWidget(0,5);self.table.setHorizontalHeaderLabels([t('Camera / Metric'),t('Visible area mm2'),t('Visible board W x H mm'),t('Target image fraction'),t('Valid pixel fraction')]);self.table.horizontalHeader().setSectionResizeMode(W.QHeaderView.ResizeMode.Stretch);self.bottom.addTab(self.table,t('Coverage results'))
  self.log=W.QTextEdit();self.log.setReadOnly(True);self.bottom.addTab(self.log,t('Help / Log'));self.log.setPlainText(t('Area uses visibility sampling on scaled 3D surfaces. Images use the first ray intersection per pixel. Purple pixels indicate invalid distortion inversion and are excluded. Photo regions require aligned cameras and targets. Pick a surface beside an opening, then adjust XYZ to move the optical center into the opening.'))
  right=W.QWidget();rv=W.QVBoxLayout(right);split.addWidget(right);rv.addWidget(W.QLabel(t('Camera images (distortion / occlusion)')));self.image_tabs=W.QTabWidget();rv.addWidget(self.image_tabs);self.button(rv,t('Import photo / Select region'),self.reference_image);self.button(rv,t('Clear camera region'),self.clear_roi);right.setMinimumWidth(330)
  controls=W.QGroupBox(t('Live preview / Keyboard'));control_layout=W.QVBoxLayout(controls);lv.insertWidget(3,controls)
  self.live_preview=W.QCheckBox(t('Live camera preview'));control_layout.addWidget(self.live_preview)
  self.keyboard_enabled=W.QCheckBox(t('Keyboard model control'));self.keyboard_enabled.setChecked(True);control_layout.addWidget(self.keyboard_enabled)
  steps=W.QFormLayout();self.move_step=self.number(1,.001,1000);self.rotate_step=self.number(2,.01,180);steps.addRow(t('Move step mm'),self.move_step);steps.addRow(t('Rotate step deg'),self.rotate_step);control_layout.addLayout(steps)
  hint=W.QLabel(t('Click the 3D view to control the selected model.\nMove: W/S X, A/D Y, Q/E Z\nRotate: I/K X, J/L Y, U/O Z\nShift: 5x step | F: fit scene'));hint.setWordWrap(True);control_layout.addWidget(hint)
  self.live_timer=C.QTimer(self);self.live_timer.setSingleShot(True);self.live_timer.setInterval(180);self.live_timer.timeout.connect(self.refresh_live)
  self.live_pending=False;self.live_preview.toggled.connect(self.live_toggled);self.res.currentTextChanged.connect(self.schedule_live)
  self.viewer.interactor.setFocusPolicy(C.Qt.FocusPolicy.StrongFocus);self.viewer.interactor.installEventFilter(self)
  split.setSizes([340,810,400]);center.setSizes([670,220]);self.load_example();translate_widgets(self)
 def live_toggled(self,enabled):
  if enabled:self.schedule_live()
  else:self.live_pending=False;self.live_timer.stop()
 def schedule_live(self,*_):
  if self.live_preview.isChecked():self.live_pending=True;self.live_timer.start()
 def refresh_live(self):
  if not self.live_preview.isChecked():return
  if self.worker and self.worker.isRunning():return
  if self.live_pending:self.live_pending=False;self.compute(False)
 def eventFilter(self,watched,event):
  if watched is self.viewer.interactor and event.type()==C.QEvent.Type.KeyPress and self.keyboard_enabled.isChecked():
   if event.modifiers() & (C.Qt.KeyboardModifier.ControlModifier|C.Qt.KeyboardModifier.AltModifier|C.Qt.KeyboardModifier.MetaModifier):return False
   key=event.key()
   if key==C.Qt.Key.Key_F:self.draw(True);return True
   keys={C.Qt.Key.Key_W:(0,1),C.Qt.Key.Key_S:(0,-1),C.Qt.Key.Key_A:(1,-1),C.Qt.Key.Key_D:(1,1),C.Qt.Key.Key_Q:(2,-1),C.Qt.Key.Key_E:(2,1),C.Qt.Key.Key_I:(3,1),C.Qt.Key.Key_K:(3,-1),C.Qt.Key.Key_J:(4,1),C.Qt.Key.Key_L:(4,-1),C.Qt.Key.Key_U:(5,1),C.Qt.Key.Key_O:(5,-1)}
   if key in keys:
    axis,direction=keys[key];self.nudge_model(axis,direction,5 if event.modifiers() & C.Qt.KeyboardModifier.ShiftModifier else 1);return True
  return super().eventFilter(watched,event)
 def nudge_model(self,axis,direction,multiplier=1):
  i=self.objlist.currentRow()
  if i<0:return
  field=self.objfields[axis];step=self.move_step.value() if axis<3 else self.rotate_step.value();field.setValue(field.value()+direction*step*multiplier)
 def button(self,layout,text,fn):
  b=W.QPushButton(text);b.clicked.connect(lambda _=False:fn());layout.addWidget(b);return b
 def number(self,value,lo=-10000,hi=10000,dec=3):
  s=W.QDoubleSpinBox();s.setRange(lo,hi);s.setDecimals(dec);s.setValue(value);s.setSingleStep(.1);s.setKeyboardTracking(False);return s
 def pose_fields(self,layout,fn):
  f=W.QFormLayout();a=[]
  for label in ['X mm','Y mm','Z mm',t('Rotate X deg'),t('Rotate Y deg'),t('Rotate Z deg')]:
   s=self.number(0);s.valueChanged.connect(fn);f.addRow(label,s);a.append(s)
  layout.addLayout(f);return a
 def error(self,e):self.log.append(str(e));W.QMessageBox.warning(self,t('Operation failed'),str(e))
 def changed(self):
  if self.updating:return
  self.revision+=1;self.last=None;self.export_button.setEnabled(False);self.status.setText(t('Scene changed; update images or evaluate coverage.'));self.draw();self.schedule_live()
 def refresh_lists(self):
  oi=self.objlist.currentRow();ci=self.camlist.currentRow();self.updating=True;self.objlist.clear();self.objlist.addItems([o.name for o in self.objects]);self.camlist.clear();self.camlist.addItems([c.name for c in self.cameras]);self.updating=False
  self.objlist.setCurrentRow(max(0,min(oi,len(self.objects)-1)));self.camlist.setCurrentRow(max(0,min(ci,len(self.cameras)-1)))
 def load_example(self):
  try:
   i=self.preset.currentIndex()+1;p=ROOT/'examples';cfg=json.loads((p/'configs'/f'layout_{i:02}.json').read_text());self.objects=[Object3D(f'Layout {i:02}',import_mesh(p/'models'/f'layout_{i:02}.npz'))];self.cameras=[Camera(c['id'],np.array(c['center_world_mm']),np.array(c['R_world_from_camera']),validate_calibration(c.get('intrinsics') or DEFAULT_K)) for c in cfg['cameras']];self.make_board();self.refresh_lists();self.changed();self.draw(True)
  except Exception as e:self.error(e)
 def draw(self,reset=False):
  old=self.viewer.camera_position;self.viewer.clear();self.viewer.add_axes();self.viewer.add_text(f'mm | Camera guides: {self.frustum_length.value():g} mm',font_size=10,color='#233c4d',name='hint')
  for i,o in enumerate(self.objects):
   if not o.enabled:continue
   m=o.world_mesh();poly=pv.PolyData(m.vertices,np.column_stack([np.full(len(m.faces),3),m.faces]).ravel());col={'housing':'#9cabb9','target':'#e3b05d','occluder':'#796f87'}[o.role];self.viewer.add_mesh(poly,color=col,smooth_shading=False,pickable=True,name=f'obj{i}')
  for i,c in enumerate(self.cameras):
   col='#0e938d' if i==self.camlist.currentRow() else '#dd633e';col=col if c.active else '#777777'
   self.viewer.add_mesh(pv.Sphere(radius=.8,center=c.center),color=col,pickable=False)
   self.viewer.add_arrows(c.center.reshape(1,3),c.rotation[:,2].reshape(1,3),mag=6,color=col,pickable=False)
   try:
    rays,valid,shape=pixel_rays(c.intrinsics,48);mask=valid.reshape(shape).astype('uint8');boundary=mask-cv2.erode(mask,np.ones((3,3),np.uint8),borderType=cv2.BORDER_CONSTANT,borderValue=0);ids=np.flatnonzero(boundary.ravel());rr=rays[ids];order=np.argsort(np.arctan2(rr[:,1],rr[:,0]));rr=rr[order][::max(1,len(rr)//32)];end=c.center+(rr@c.rotation.T)*self.frustum_length.value()/np.maximum(rr[:,2:3],.05)
    if len(end)>2:
     self.viewer.add_lines(np.vstack([end,end[:1]]),connected=True,color=col,width=1).SetPickable(False)
     for e in end[::max(1,len(end)//4)]:self.viewer.add_lines(np.array([c.center,e]),color=col,width=1).SetPickable(False)
   except Exception:pass
  if reset:self.viewer.view_isometric();self.viewer.reset_camera()
  else:self.viewer.camera_position=old
  self.viewer.render()
 def object_selected(self,*_):
  i=self.objlist.currentRow()
  if self.updating or not 0<=i<len(self.objects):return
  self.updating=True;o=self.objects[i];self.role.setCurrentIndex(self.role.findData(o.role));self.enabled.setChecked(o.enabled);self.scale.setValue(o.scale)
  for s,v in zip(self.objfields,np.r_[o.position,o.angles]):s.setValue(float(v))
  self.updating=False
 def object_changed(self,*_):
  i=self.objlist.currentRow()
  if self.updating or not 0<=i<len(self.objects):return
  o=self.objects[i];a=np.array([s.value() for s in self.objfields]);o.position=a[:3];o.angles=a[3:];o.scale=self.scale.value();o.role=self.role.currentData();o.enabled=self.enabled.isChecked();self.changed()
 def camera_selected(self,*_):
  i=self.camlist.currentRow()
  if self.updating or not 0<=i<len(self.cameras):return
  c=self.cameras[i];self.updating=True;angles=Rotation.from_matrix(c.rotation).as_euler('xyz',degrees=True)
  for s,v in zip(self.camfields,np.r_[c.center,angles]):s.setValue(float(v))
  self.camactive.setChecked(c.active);k=c.intrinsics;self.klabel.setText(f"{k['model']} · {k['image_size'][0]} × {k['image_size'][1]}\nfx={k['K'][0][0]:.2f}, fy={k['K'][1][1]:.2f}");self.updating=False;self.draw()
 def camera_changed(self,*_):
  i=self.camlist.currentRow()
  if self.updating or not 0<=i<len(self.cameras):return
  c=self.cameras[i];a=np.array([s.value() for s in self.camfields]);c.center=a[:3];c.rotation=Rotation.from_euler('xyz',a[3:],degrees=True).as_matrix();c.active=self.camactive.isChecked();self.changed()
 def start_pick(self):self.picking=True;self.status.setText(t('Left-click a surface to add a camera pointing along its normal. Adjust its pose or flip its axis afterward.'))
 def picked(self,point,picker):
  if not self.picking:return
  try:
   n=np.array(picker.GetPickNormal());self.cameras.append(Camera(f'camera_{len(self.cameras)+1}',np.array(point),camera_rotation(n)));self.picking=False;self.refresh_lists();self.camlist.setCurrentRow(len(self.cameras)-1);self.changed()
  except Exception as e:self.error(e)
 def clone_camera(self):
  i=self.camlist.currentRow()
  if i<0:return
  c=copy.deepcopy(self.cameras[i]);c.name=f'camera_{len(self.cameras)+1}';self.cameras.append(c);self.refresh_lists();self.camlist.setCurrentRow(len(self.cameras)-1);self.changed()
 def remove_camera(self):
  i=self.camlist.currentRow()
  if i>=0:self.cameras.pop(i);self.refresh_lists();self.changed()
 def flip_camera(self):
  i=self.camlist.currentRow()
  if i>=0:self.cameras[i].rotation=self.cameras[i].rotation@np.diag([-1,1,-1]);self.camera_selected();self.changed()
 def offset_camera(self):
  i=self.camlist.currentRow()
  if i>=0:self.cameras[i].center+=self.cameras[i].rotation[:,2]*self.offset.value();self.camera_selected();self.changed()
 def look_camera(self):
  i=self.camlist.currentRow()
  if i<0:return
  c=self.cameras[i];self.viewer.camera_position=[c.center,c.center+c.rotation[:,2]*50,-c.rotation[:,1]];k=c.intrinsics;self.viewer.camera.view_angle=float(np.degrees(2*np.arctan(k['image_size'][1]/(2*k['K'][1][1]))));self.viewer.render();self.status.setText(t('The 3D view is approximate; camera images use calibrated rays and distortion.'))
 def import_intrinsics(self,all_cameras):
  p,_=W.QFileDialog.getOpenFileName(self,t('Import calibration'),'','Calibration (*.json *.yaml *.yml *.xml *.md *.txt)')
  if not p:return
  try:
   k=load_calibration(p);i=self.camlist.currentRow()
   if all_cameras:
    for c in self.cameras:
     if c.intrinsics['image_size']!=k['image_size']:c.image_mask=None
     c.intrinsics=copy.deepcopy(k)
   elif i>=0:
    if self.cameras[i].intrinsics['image_size']!=k['image_size']:self.cameras[i].image_mask=None
    self.cameras[i].intrinsics=k
   self.camera_selected();self.changed()
  except Exception as e:self.error(e)
 def import_object(self):
  p,_=W.QFileDialog.getOpenFileName(self,t('Import housing / teeth / head'),'','3D (*.step *.stp *.stl *.obj *.ply *.glb *.gltf *.npz)')
  if not p:return
  try:
   W.QApplication.setOverrideCursor(C.Qt.CursorShape.WaitCursor);m=import_mesh(p);self.objects.append(Object3D(Path(p).stem,m,'target'));self.refresh_lists();self.objlist.setCurrentRow(len(self.objects)-1);self.changed();self.draw(True);self.log.append(f'Imported {Path(p).name}: {len(m.faces)} triangles; original bounds {m.extents}. Check unit scaling.')
  except Exception as e:self.error(e)
  finally:W.QApplication.restoreOverrideCursor()
 def remove_object(self):
  i=self.objlist.currentRow()
  if i>=0:self.objects.pop(i);self.refresh_lists();self.changed()
 def center_target(self):
  i=self.objlist.currentRow()
  if i<0:return
  o=self.objects[i];R=Rotation.from_euler('xyz',o.angles,degrees=True).as_matrix();o.position=np.array([self.tipx.value()-self.bd.value(),0,0])-R@(o.mesh.centroid*o.scale);self.object_selected();self.changed();self.draw(True)
 def make_board(self):
  self.objects=[o for o in self.objects if o.name!='Test board'];self.objects.append(Object3D('Test board',board_mesh(self.bw.value(),self.bh.value()),'target',np.array([self.tipx.value()-self.bd.value(),0.,0.]),np.array([90.,0.,90.])));self.refresh_lists();self.objlist.setCurrentRow(len(self.objects)-1);self.changed()
 def demo_surface(self):
  for o in self.objects:
   if o.name=='Test board':o.enabled=False
  m=trimesh.creation.icosphere(subdivisions=3,radius=15);m.vertices[:,1]*=.65;self.objects.append(Object3D('Demo curved target',m,'target',np.array([-207.,0,0])));self.refresh_lists();self.objlist.setCurrentRow(len(self.objects)-1);self.changed();self.draw(True)
 def compute(self,area):
  if self.worker and self.worker.isRunning():return
  self.job_revision=self.revision;self.preview_button.setEnabled(False);self.eval_button.setEnabled(False);self.status.setText(t('Preparing ray scene...'));self.worker=ComputeWorker(self.objects,self.cameras,int(self.res.currentText()),int(self.samples.currentText()),area);self.worker.done.connect(self.computed);self.worker.failed.connect(self.compute_failed);self.worker.progress.connect(self.status.setText);self.worker.finished.connect(self.job_finished);self.worker.start()
 def job_finished(self):
  self.preview_button.setEnabled(True);self.eval_button.setEnabled(True)
  if self.live_pending:self.live_timer.start()
 def compute_failed(self,msg):self.status.setText(t('Computation failed'));self.error(msg)
 def image_widget(self,array):
  h,w=array.shape[:2];q=G.QImage(np.ascontiguousarray(array).data,w,h,w*3,G.QImage.Format.Format_RGB888).copy();label=W.QLabel();label.setPixmap(G.QPixmap.fromImage(q));label.setAlignment(C.Qt.AlignmentFlag.AlignCenter);scroll=W.QScrollArea();scroll.setWidget(label);scroll.setWidgetResizable(True);return scroll
 def computed(self,result):
  if self.job_revision!=self.revision:self.status.setText(t('Scene changed during computation; outdated results discarded.'));return
  self.last=result;self.image_tabs.clear();self.table.setRowCount(0);m=result['metrics']
  for name,r in result['images']:
   self.image_tabs.addTab(self.image_widget(r['image']),name);area='—'
   if m:
    area=next((f"{v['visible_area_mm2']:.1f}" for v in m['per_camera'] if v['name']==name),'—')
   wh='—'
   if m:
    item=next((v for v in m['per_camera'] if v['name']==name),{})
    if item.get('board_visible_width_mm') is not None:wh=f"{item['board_visible_width_mm']:.1f} × {item['board_visible_height_mm']:.1f}"
   self.add_row([name,area,wh,f"{r['target_image_fraction']:.1%}",f"{r['valid_pixels_fraction']:.1%}"])
  if m:
   for label,key in [(t('Total target area'),'target_area_mm2'),(t('Visible to at least one camera'),'covered_mm2'),(t('Visible to at least two cameras'),'overlap2_mm2'),(t('Blind surface'),'blind_mm2')]:self.add_row([label,f'{m[key]:.1f}','—','—','—'])
   cloud=pv.PolyData(result['points']);cloud['camera_count']=result['counts'];self.viewer.add_mesh(cloud,scalars='camera_count',clim=[0,max(1,len([c for c in self.cameras if c.active]))],cmap='viridis',point_size=4,render_points_as_spheres=False,name='coverage',pickable=False,scalar_bar_args={'title':'Visible cameras'});self.log.append(json.dumps(m,ensure_ascii=False,indent=2))
  self.export_button.setEnabled(True);self.status.setText(t('Done. Images are geometric simulations; areas are sampled estimates.'))
 def add_row(self,values):
  i=self.table.rowCount();self.table.insertRow(i)
  for j,v in enumerate(values):self.table.setItem(i,j,W.QTableWidgetItem(str(v)))
 def save_project(self):
  p,_=W.QFileDialog.getSaveFileName(self,t('Save project'),'','Multicam (*.mcv)')
  if p:
   try:save_session(p,self.objects,self.cameras);self.status.setText(t('Project saved with models, cameras and calibration.'))
   except Exception as e:self.error(e)
 def open_project(self):
  p,_=W.QFileDialog.getOpenFileName(self,t('Open project'),'','Multicam (*.mcv)')
  if p:
   try:self.objects,self.cameras=load_session(p);self.refresh_lists();self.changed();self.draw(True)
   except Exception as e:self.error(e)
 def export_results(self):
  if not self.last:return
  p=W.QFileDialog.getExistingDirectory(self,t('Export to folder'))
  if not p:return
  try:self.export_to(Path(p));self.status.setText(t('Exported images, masks, depth, metrics, coverage cloud and project.'))
  except Exception as e:self.error(e)
 def export_to(self,p):
  p.mkdir(parents=True,exist_ok=True);save_session(p/'scene.mcv',self.objects,self.cameras);summary=[]
  for i,(name,r) in enumerate(self.last['images']):
   cv2.imwrite(str(p/f'camera_{i+1}.png'),cv2.cvtColor(r['image'],cv2.COLOR_RGB2BGR));cv2.imwrite(str(p/f'camera_{i+1}_target_mask.png'),r['mask'].astype('uint8')*255);np.save(p/f'camera_{i+1}_depth_mm.npy',r['depth_mm']);summary.append({'name':name,**{k:v for k,v in r.items() if not isinstance(v,np.ndarray)}})
  data={'camera_images':summary,'surface_metrics':self.last['metrics'],'units':'mm, mm2','method':'First-hit ray image; equal-area stratified surface samples. Approximate geometric result.'};(p/'metrics.json').write_text(json.dumps(data,indent=2,ensure_ascii=False))
  if self.last['metrics']:
   with (p/'camera_areas.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=['name','visible_area_mm2','world_bbox_extent_mm','board_visible_width_mm','board_visible_height_mm']);w.writeheader();w.writerows(self.last['metrics']['per_camera'])
   np.savez_compressed(p/'coverage.npz',points=self.last['points'],visible_camera_count=self.last['counts']);col=np.array([[50,50,50],[60,145,210],[47,177,140],[236,197,66],[224,100,57]]);trimesh.points.PointCloud(self.last['points'],colors=col[np.minimum(self.last['counts'],4)]).export(p/'coverage.ply')
 def clear_roi(self):
  i=self.camlist.currentRow()
  if i>=0:self.cameras[i].image_mask=None;self.changed()
 def reference_image(self):
  i=self.camlist.currentRow()
  if i<0:return
  p,_=W.QFileDialog.getOpenFileName(self,t('Import photo'),'','Images (*.png *.jpg *.jpeg *.bmp)')
  if not p:return
  image=cv2.imread(p)
  if image is None:return
  image=cv2.cvtColor(image,cv2.COLOR_BGR2RGB);h,w=image.shape[:2]
  if [w,h]!=self.cameras[i].intrinsics['image_size']:self.error(t('Photo size does not match calibration. Use the original resolution or update calibration.'));return
  self.image_tabs.addTab(self.image_widget(image),t('Reference photo'));dlg=RoiDialog(image,self)
  if dlg.exec()==W.QDialog.DialogCode.Accepted:self.cameras[i].image_mask=dlg.mask();self.changed();self.status.setText(t('Region applied. Align the photo and 3D scene, then evaluate again.'))
 def closeEvent(self,event):
  self.live_preview.setChecked(False);self.live_timer.stop()
  if self.worker and self.worker.isRunning():self.worker.requestInterruption();self.status.setText(t('Computation is stopping; close again when finished.'));event.ignore();return
  self.viewer.close();event.accept()

if __name__=='__main__':
 app=W.QApplication(sys.argv);app.setStyle('Fusion');launch=LaunchDialog()
 if launch.exec()!=W.QDialog.DialogCode.Accepted:sys.exit(0)
 w=MainWindow();w.res.setCurrentText('160' if launch.live.isChecked() else '320');w.show();w.live_preview.setChecked(launch.live.isChecked());sys.exit(app.exec())
