import unittest,tempfile,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import *
class EngineTests(unittest.TestCase):
 def cam(self):return Camera('test',np.array([0.,0,10.]),camera_rotation([0,0,-1],up=[0,1,0]),{'model':'opencv','image_size':[100,100],'K':[[100,0,49.5],[0,100,49.5],[0,0,1]],'D':[0,0,0,0,0]})
 def test_planar_area(self):
  objects=[Object3D('plane',board_mesh(10,10),'target')];m,pts,count=evaluate(objects,[self.cam()],4000)
  self.assertAlmostEqual(m['target_area_mm2'],100,5);self.assertAlmostEqual(m['covered_mm2'],100,5)
 def test_blocker(self):
  box=trimesh.creation.box([20,20,1]);box.apply_translation([0,0,5]);objects=[Object3D('plane',board_mesh(10,10),'target'),Object3D('block',box,'occluder')];m,_,_=evaluate(objects,[self.cam()],1000);self.assertEqual(m['covered_mm2'],0)
  r=render_camera(objects,self.cam(),100);self.assertEqual(r['target_image_fraction'],0)
 def test_first_hit_render(self):
  r=render_camera([Object3D('plane',board_mesh(10,10),'target')],self.cam(),100);self.assertEqual(r['mask'].shape,(100,100));self.assertGreater(r['target_image_fraction'],.99)
 def test_session_roundtrip(self):
  o=Object3D('plane',board_mesh(10,10),'target',np.array([1,2,3]),np.array([0,30,0]),2)
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'s.mcv';save_session(p,[o],[self.cam()]);oo,cc=load_session(p);np.testing.assert_allclose(oo[0].world_mesh().vertices,o.world_mesh().vertices);np.testing.assert_allclose(cc[0].rotation,self.cam().rotation)
 def test_calibration_alias(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'k.json';p.write_text(json.dumps({'model':'pinhole','image_size':[100,100],'camera_matrix':[[100,0,50],[0,100,50],[0,0,1]],'distortion_coefficients':[[0,0,0,0,0]]}));self.assertEqual(load_calibration(p)['model'],'opencv')
 def test_model_scale_area(self):
  o=Object3D('plane',board_mesh(1,1),'target',scale=2);_,w,_=sample_targets([o],100);self.assertAlmostEqual(w.sum(),4)
 def test_pair_overlap(self):
  c=self.cam();c2=Camera('two',c.center.copy(),c.rotation.copy(),c.intrinsics.copy());m,_,_=evaluate([Object3D('plane',board_mesh(10,10),'target')],[c,c2],1000);self.assertAlmostEqual(m['overlap2_mm2'],100,5);self.assertEqual(m['pairs'][0]['IoU'],1)
 def test_observed_mask_limits_area(self):
  c=self.cam();c.image_mask=np.zeros((100,100),np.uint8);c.image_mask[:,:50]=255;objects=[Object3D('plane',board_mesh(10,10),'target')];m,_,_=evaluate(objects,[c],10000);self.assertAlmostEqual(m['covered_mm2'],50,delta=1.5)
  r=render_camera(objects,c,100);self.assertAlmostEqual(r['target_image_fraction'],.5,places=2)
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'s.mcv';save_session(p,objects,[c]);_,cc=load_session(p);np.testing.assert_equal(cc[0].image_mask,c.image_mask)
 def test_pointing_frame(self):
  R=camera_rotation([-1,0,0]);np.testing.assert_allclose(R.T@R,np.eye(3));self.assertAlmostEqual(np.linalg.det(R),1)
if __name__=='__main__':unittest.main()
