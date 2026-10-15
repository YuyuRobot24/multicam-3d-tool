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
  self.window.live_preview.setChecked(False)
  if self.window.worker:
   self.window.worker.requestInterruption()
   self.window.worker.wait()
  self.window.close()
  self.app.processEvents()

 def test_keyboard_moves_selected_model_and_respects_toggle(self):
  w=self.window;w.objlist.setCurrentRow(1)
  before=w.objects[1].position.copy();other=w.objects[0].position.copy()
  event=G.QKeyEvent(C.QEvent.Type.KeyPress,C.Qt.Key.Key_W,C.Qt.KeyboardModifier.ShiftModifier)
  W.QApplication.sendEvent(w.viewer.interactor,event)
  self.assertAlmostEqual(w.objects[1].position[0],before[0]+5*w.move_step.value())
  self.assertTrue((w.objects[0].position==other).all())
  w.nudge_model(4,1)
  self.assertAlmostEqual(w.objects[1].angles[1],w.rotate_step.value())
  w.keyboard_enabled.setChecked(False)
  before=w.objects[1].position.copy()
  W.QApplication.sendEvent(w.viewer.interactor,event)
  self.assertTrue((w.objects[1].position==before).all())

 def test_live_preview_and_stale_results(self):
  w=self.window;w.live_preview.setChecked(True)
  deadline=C.QDeadlineTimer(30000)
  while w.last is None and not deadline.hasExpired():
   self.app.processEvents(C.QEventLoop.ProcessEventsFlag.AllEvents,50)
  self.assertIsNotNone(w.last)
  self.assertEqual(len(w.last['images']),3)
  old=w.last;w.nudge_model(0,1)
  self.assertIsNone(w.last)
  self.assertFalse(w.export_button.isEnabled())
  w.computed(old)
  self.assertIsNone(w.last)
  w.live_preview.setChecked(False)
  self.assertFalse(w.live_timer.isActive())

if __name__=='__main__':unittest.main()
