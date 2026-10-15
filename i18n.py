"""Small reversible English / Simplified Chinese UI catalog."""
from PySide6 import QtWidgets as W

LANGUAGE = 'en'
ZH = {
 'Suggest marker size for distance':'按测试距离推荐标记大小',
 'AprilTag size mm':'AprilTag 标记边长 mm','Delete background board':'删除背景板',
 'Handle size mm':'操纵器大小 mm',
 'Interaction':'交互','Object interaction':'物体移动与旋转',
 'Roll (X)':'Roll 横滚 (X)','Pitch (Y)':'Pitch 俯仰 (Y)','Yaw (Z)':'Yaw 偏航 (Z)',
 'Click a model to select it. Drag colored arrows to move; drag arcs to rotate. Red: X / Roll, green: Y / Pitch, blue: Z / Yaw. Use the arrow buttons for precise steps. Images and evaluation update only when you press their buttons.':'点击模型进行选择，拖动彩色箭头移动，拖动圆弧旋转。红色：X / Roll，绿色：Y / Pitch，蓝色：Z / Yaw。可用箭头按钮按设定步长精调。出图和评估仅由对应按钮触发。',
 'Metric / Camera pair':'指标 / 相机对','Rate':'比例','Area mm2':'面积 mm²','Joint extent mm':'联合范围 mm',
 'All cameras - undistorted views':'全部相机 - 去畸变画面','All cameras':'全部相机',
 'Waiting for preview':'等待预览','Camera disabled':'相机已禁用',
 'Combined coverage / Target area':'联合覆盖 / 目标总面积',
 'Multi-camera overlap / Combined coverage':'多目重叠 / 联合覆盖',
 'See world bounds below':'详见日志中的世界坐标范围','Combined world bounds mm':'联合覆盖世界坐标范围 mm',
 'housing':'结构','target':'目标','occluder':'遮挡物','Test board':'测试板','Demo curved target':'演示曲面',
 'Multicam 3D - Start':'多相机 3D - 启动',
 '<h2>Multicam 3D Workbench</h2>':'<h2>多相机 3D 工作台</h2>',
 'Multicam 3D Visibility Workbench - mm':'多相机 3D 视场评估 - mm',
 'Multicam 3D Workbench':'多相机 3D 工作台',
 'Enable live camera preview':'开启实时相机预览',
 'Start simulator':'启动模拟器','OK':'确定','Cancel':'取消',
 'Load example':'载入示例','Scene / Test board':'场景 / 测试板',
 'Import model':'导入模型','Delete':'删除',
 'Role: housing / measured target / occluder':'角色：结构 / 评价目标 / 遮挡物',
 'Enabled (visible and occluding)':'启用（显示并参与遮挡）',
 'Unit conversion / Scale':'单位换算 / 缩放','Center in test area':'居中至测试区',
 'Fit scene':'完整场景','Test board (local XY plane)':'测试板（局部 XY 平面）',
 'Tip reference X mm':'尖端参考 X mm','Width mm':'宽 mm','Height mm':'高 mm',
 'Distance from tip -X mm':'距尖端 -X mm','Create / Reset board':'创建 / 重置测试板',
 'Load curved demo':'载入演示曲面',
 'Set imported teeth/head to target; disable the board if needed. All target surfaces count, including the back.':'导入牙齿或头部后设为 target，可禁用测试板。所有目标表面均计入总面积，包括背面。',
 'Cameras':'相机','Place on surface':'表面选点放置','Duplicate':'复制',
 'Include in images and coverage':'参与成像和覆盖计算','Flip optical axis':'反转光轴',
 'View from camera':'进入相机视角','Optical axis offset mm':'沿光轴偏移 mm',
 'Apply offset':'应用偏移','Import calibration':'导入内参','Apply to all':'应用至全部',
 'JSON / YAML / OpenCV YAML / Markdown report. The 3D view is a guide; ray images use full calibration.':'支持 JSON / YAML / OpenCV YAML / Markdown 标定报告。三维视图用于导航，相机图像使用完整内参。',
 'Compute':'计算','Image width px':'成像宽度 px','Area samples':'面积采样点数',
 'Camera guide length mm':'辅助视锥长度 mm','Update images':'更新相机图像',
 'Evaluate coverage':'评估覆盖与重合','Save project':'保存工程',
 'Open project':'打开工程','Export results':'导出结果','Ready':'准备就绪',
 'Camera / Metric':'相机 / 指标','Visible area mm2':'可见面积 mm²',
 'Visible board W x H mm':'测试板可见宽×高 mm','Target image fraction':'目标占图像比例',
 'Valid pixel fraction':'有效成像像素比例','Coverage results':'评估结果','Help / Log':'说明 / 日志',
 'Camera images (distortion / occlusion)':'相机成像（含畸变 / 遮挡）',
 'Import photo / Select region':'导入实拍图 / 圈选区域','Clear camera region':'清除相机观测区域',
 'Live preview / Keyboard':'实时预览 / 键盘控制','Live camera preview':'实时相机预览',
 'Keyboard model control':'键盘控制模型','Move step mm':'移动步长 mm','Rotate step deg':'旋转步长 °',
 'Rotate X deg':'绕 X °','Rotate Y deg':'绕 Y °','Rotate Z deg':'绕 Z °',
 'Operation failed':'操作未完成','Scene changed; update images or evaluate coverage.':'场景已变化，请更新图像或评估覆盖。',
 'Left-click a surface to add a camera pointing along its normal. Adjust its pose or flip its axis afterward.':'左键点击模型表面添加相机，朝向沿表面法向。随后可调整位姿或反转光轴。',
 'The 3D view is approximate; camera images use calibrated rays and distortion.':'三维视图为近似导航，相机图像使用标定射线和畸变。',
 'Import housing / teeth / head':'导入结构 / 牙齿 / 头部',
 'Preparing ray scene...':'准备射线场景…','Computation failed':'计算失败',
 'Scene changed during computation; outdated results discarded.':'计算期间场景已变化，旧结果已丢弃。',
 'Total target area':'目标总面积','Visible to at least one camera':'至少一目可见',
 'Visible to at least two cameras':'至少两目重合','Blind surface':'全盲表面',
 'Done. Images are geometric simulations; areas are sampled estimates.':'完成。图像为几何模拟，面积为采样估计。',
 'Project saved with models, cameras and calibration.':'工程已保存，包含模型、相机和内参。',
 'Export to folder':'导出到目录',
 'Exported images, masks, depth, metrics, coverage cloud and project.':'已导出图像、掩膜、深度、指标、覆盖点云和工程。',
 'Import photo':'导入实拍图',
 'Photo size does not match calibration. Use the original resolution or update calibration.':'实拍图尺寸与内参不匹配，请使用原始分辨率或更新内参。',
 'Reference photo':'实拍参考',
 'Region applied. Align the photo and 3D scene, then evaluate again.':'已应用观测区域。请对齐照片和三维场景，再重新评估。',
 'Computation is stopping; close again when finished.':'计算正在停止，请稍后再次关闭。',
 'Observed region: left-click to add, right-click to undo':'观测区域：左键添加顶点，右键撤回',
 'Align the camera and model with the photo. Scale comes from the 3D scene.':'请将相机和模型与照片对齐，物理尺度来自三维场景。',
 'Incomplete region':'选区未完成','Select at least three vertices.':'至少选择三个顶点。',
 'Rendering: ':'成像：','Calculating coverage, overlap and blind areas...':'计算覆盖、重合和盲区…',
 'Length mm - Angles deg - Area mm2\nCamera: +Z forward, +X right, +Y down':'长度 mm · 角度 ° · 面积 mm²\n相机 +Z 向前，+X 向右，+Y 向下',
 'Inspect calibrated camera views and geometric coverage.\n\nSelect a model, then click the 3D viewport.\nMove: W/S = +/-X, A/D = -/+Y, Q/E = -/+Z\nRotate: I/K = +/-X, J/L = +/-Y, U/O = +/-Z\nHold Shift for 5x steps. F = fit scene.\nKeyboard input is active only in the 3D viewport.':'查看标定相机图像及几何覆盖。\n\n选择模型后点击三维视图。\n移动：W/S = +/-X，A/D = -/+Y，Q/E = -/+Z\n旋转：I/K = +/-X，J/L = +/-Y，U/O = +/-Z\n按住 Shift 使用 5 倍步长，F 显示完整场景。\n键盘控制仅在三维视图内生效。',
 'Click the 3D view to control the selected model.\nMove: W/S X, A/D Y, Q/E Z\nRotate: I/K X, J/L Y, U/O Z\nShift: 5x step | F: fit scene':'点击三维视图控制选中模型。\n移动：W/S X，A/D Y，Q/E Z\n旋转：I/K X，J/L Y，U/O Z\nShift：5 倍步长 | F：完整场景',
 'Area uses visibility sampling on scaled 3D surfaces. Images use the first ray intersection per pixel. Purple pixels indicate invalid distortion inversion and are excluded. Photo regions require aligned cameras and targets. Pick a surface beside an opening, then adjust XYZ to move the optical center into the opening.':'面积基于带尺度三维表面的可见性采样，图像使用每个像素的第一射线交点。紫色像素表示畸变反解无效，不计入有效视野。实拍选区需要相机和目标已对齐。可先选开孔旁的表面，再用 XYZ 将光心移至孔中心。',
}
EN = {v:k for k,v in ZH.items()}

def t(text):
 canonical=EN.get(text,text)
 return ZH.get(canonical,canonical) if LANGUAGE=='zh' else canonical

def translate_widgets(root):
 """Translate existing widgets without rebuilding or changing scene state."""
 for widget in [root,*root.findChildren(W.QWidget)]:
  widget.setWindowTitle(t(widget.windowTitle()))
  if isinstance(widget,(W.QLabel,W.QAbstractButton)):widget.setText(t(widget.text()))
  if isinstance(widget,W.QLabel) and len(widget.text())>45:widget.setWordWrap(True)
  if isinstance(widget,W.QComboBox) and widget.objectName()=='roleMenu':
   blocked=widget.blockSignals(True)
   for i in range(widget.count()):widget.setItemText(i,t(widget.itemData(i)))
   widget.blockSignals(blocked)
  if isinstance(widget,W.QGroupBox):widget.setTitle(t(widget.title()))
  if isinstance(widget,W.QTabWidget):
   for i in range(widget.count()):widget.setTabText(i,t(widget.tabText(i)))
  if isinstance(widget,W.QTableWidget):
   for i in range(widget.columnCount()):
    item=widget.horizontalHeaderItem(i)
    if item:item.setText(t(item.text()))
   for i in range(widget.rowCount()):
    item=widget.item(i,0)
    if item:item.setText(t(item.text()))
  if isinstance(widget,W.QTextEdit):
   text=widget.toPlainText()
   widget.setPlainText('\n'.join(t(line) for line in text.split('\n')))

def set_language(language,root):
 global LANGUAGE
 LANGUAGE=language
 translate_widgets(root)

def language_menu(root,layout):
 combo=W.QComboBox();combo.addItem('English','en');combo.addItem('中文','zh');combo.setCurrentIndex(1 if LANGUAGE=='zh' else 0)
 combo.setObjectName('languageMenu');combo.setToolTip('Language / 语言')
 combo.currentIndexChanged.connect(lambda _:set_language(combo.currentData(),root))
 layout.addWidget(combo)
 return combo
