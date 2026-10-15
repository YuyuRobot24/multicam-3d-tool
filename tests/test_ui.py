import os
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).resolve().parents[1] / '.cache' / 'matplotlib'))
from app import MainWindow, W, C, G
import i18n


class UiTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.app=W.QApplication.instance() or W.QApplication([])

 def setUp(self):
  i18n.LANGUAGE='en'
  self.window=MainWindow()
  self.window.res.setCurrentText('160')
  self.window.show()
  self.app.processEvents()

 def test_language_switch_preserves_scene_and_updates_future_messages(self):
  w=self.window
  self.assertEqual(w.preview_button.text(),'Update images')
  positions=[o.position.copy() for o in w.objects]
  revision=w.revision
  w.language.setCurrentIndex(1)
  self.assertEqual(w.preview_button.text(),i18n.ZH['Update images'])
  self.assertEqual(w.revision,revision)
  self.assertTrue(all((o.position==p).all() for o,p in zip(w.objects,positions)))
  w.nudge_model(0,1)
  self.assertEqual(w.status.text(),i18n.ZH['Scene changed; update images or evaluate coverage.'])
  w.language.setCurrentIndex(0)
  self.assertEqual(w.preview_button.text(),'Update images')
  self.assertEqual(w.status.text(),'Scene changed; update images or evaluate coverage.')

 def tearDown(self):
  if self.window.worker:
   self.window.worker.requestInterruption()
   self.window.worker.wait()
  self.window.close()
  self.app.processEvents()

 def test_arrow_buttons_move_and_rotate_only_selected_model(self):
  w=self.window;w.objlist.setCurrentRow(1)
  before=w.objects[1].position.copy();other=w.objects[0].position.copy()
  w.transform_buttons[1].click()
  self.assertAlmostEqual(w.objects[1].position[0],before[0]+w.move_step.value())
  self.assertTrue((w.objects[0].position==other).all())
  w.transform_buttons[9].click()
  self.assertAlmostEqual(w.objects[1].angles[1],w.rotate_step.value())
  before=w.objects[1].position.copy()
  event=G.QKeyEvent(C.QEvent.Type.KeyPress,C.Qt.Key.Key_W,C.Qt.KeyboardModifier.NoModifier)
  W.QApplication.sendEvent(w.viewer.interactor,event)
  self.assertTrue((w.objects[1].position==before).all())

 def test_manual_preview_and_stale_results(self):
  w=self.window
  self.assertIsNone(w.worker)
  w.transform_buttons[1].click();self.app.processEvents()
  self.assertIsNone(w.worker)
  w.preview_button.click()
  deadline=C.QDeadlineTimer(30000)
  while w.last is None and not deadline.hasExpired():
   self.app.processEvents(C.QEventLoop.ProcessEventsFlag.AllEvents,50)
  self.assertIsNotNone(w.last)
  self.assertEqual(len(w.last['images']),4)
  self.assertEqual(w.camera_grid.count(),4)
  self.assertTrue(all(r['display_model']=='undistorted_pinhole' for _,r in w.last['images']))
  old=w.last;w.nudge_model(0,1)
  self.assertIsNone(w.last)
  self.assertFalse(w.export_button.isEnabled())
  w.computed(old)
  self.assertIsNone(w.last)
  if w.worker:w.worker.wait()
  self.app.processEvents()
  self.assertIsNone(w.last)
  self.assertFalse(hasattr(w,'live_timer'))

 def test_gizmo_transform_preserves_pose_scale_and_session(self):
  import tempfile
  import numpy as np
  from engine import Rotation,save_session,load_session
  w=self.window;w.objlist.setCurrentRow(1);obj=w.objects[1]
  self.assertIsNotNone(w.gizmo)
  self.assertEqual(len(w.gizmo._arrows),3)
  self.assertEqual(len(w.gizmo._circles),3)
  before=obj.world_mesh().vertices.copy();position=obj.position.copy();angles=obj.angles.copy()
  matrix=np.eye(4);matrix[:3,:3]=Rotation.from_euler('z',20,degrees=True).as_matrix();matrix[:3,3]=[3,4,5]
  w.finish_transform(1,matrix,position,angles);self.app.processEvents()
  np.testing.assert_allclose(obj.world_mesh().vertices,before@matrix[:3,:3].T+matrix[:3,3],atol=1e-8)
  self.assertIsNone(w.worker)
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'moved.mcv';save_session(path,w.objects,w.cameras);restored,_=load_session(path)
   np.testing.assert_allclose(restored[1].world_mesh().vertices,obj.world_mesh().vertices)

 def test_mouse_picking_selects_model_and_opens_interaction(self):
  from vtkmodules.vtkRenderingCore import vtkCoordinate
  w=self.window;w.objlist.setCurrentRow(0)
  coordinate=vtkCoordinate();coordinate.SetCoordinateSystemToWorld();coordinate.SetValue(-207,18,18)
  x,y=coordinate.GetComputedDoubleDisplayValue(w.viewer.renderer)
  width,height=w.viewer.render_window.GetSize()
  w.pick_object_at(x*w.viewer.interactor.width()/width,(height-1-y)*w.viewer.interactor.height()/height)
  self.assertEqual(w.objlist.currentRow(),1)
  self.assertIs(w.side_tabs.currentWidget(),w.interaction_panel)

 def test_mouse_drags_translation_arrow_and_rotation_arc(self):
  import numpy as np
  from PySide6.QtTest import QTest
  from vtkmodules.vtkRenderingCore import vtkCoordinate
  from engine import Rotation
  w=self.window;view=w.viewer.interactor
  def screen(point):
   c=vtkCoordinate();c.SetCoordinateSystemToWorld();c.SetValue(*point)
   x,y=c.GetComputedDoubleDisplayValue(w.viewer.renderer);width,height=w.viewer.render_window.GetSize()
   return C.QPoint(round(x*view.width()/width),round((height-1-y)*view.height()/height))
  def move(point,buttons=C.Qt.MouseButton.NoButton):
   event=G.QMouseEvent(C.QEvent.Type.MouseMove,C.QPointF(point),C.QPointF(point),C.Qt.MouseButton.NoButton,buttons,C.Qt.KeyboardModifier.NoModifier)
   self.app.sendEvent(view,event);self.app.processEvents()
  def drag(start,end):
   QTest.mousePress(view,C.Qt.MouseButton.LeftButton,pos=start)
   move(end,C.Qt.MouseButton.LeftButton)
   QTest.mouseRelease(view,C.Qt.MouseButton.LeftButton,pos=end);self.app.processEvents()
  start=screen(w.gizmo._arrows[0].center);origin=np.array(w.gizmo.origin)
  delta=screen(origin+np.array([10,0,0]))-screen(origin)
  before=w.objects[1].position.copy();move(start)
  self.assertIs(w.gizmo._selected_actor,w.gizmo._arrows[0])
  drag(start,start+delta)
  self.assertFalse(np.allclose(before,w.objects[1].position))
  arc=w.gizmo._circles[2];points=arc.mapper.dataset.points;matrix=arc.user_matrix
  for candidate in points[::max(1,len(points)//20)]:
   point=matrix[:3,:3]@candidate+matrix[:3,3];start=screen(point);move(start)
   if w.gizmo._selected_actor is arc:break
  self.assertIs(w.gizmo._selected_actor,arc)
  before=w.objects[1].angles.copy();origin=np.array(w.gizmo.origin)
  end=screen(origin+Rotation.from_euler('z',20,degrees=True).apply(point-origin))
  drag(start,end)
  self.assertFalse(np.allclose(before,w.objects[1].angles))
  self.assertIsNone(w.worker)

 def test_evaluation_shows_joint_metrics_and_all_six_pairs(self):
  from engine import evaluate
  w=self.window;metrics,points,counts=evaluate(w.objects,w.cameras,2000)
  w.job_revision=w.revision
  w.computed({'images':[],'metrics':metrics,'points':points,'counts':counts})
  self.assertEqual(w.table.rowCount(),9)
  self.assertEqual(w.table.columnCount(),4)
  self.assertEqual(w.table.item(0,0).text(),'Combined coverage / Target area')
  self.assertTrue(all('(IoU)' in w.table.item(i,0).text() for i in range(3,9)))

if __name__=='__main__':unittest.main()
