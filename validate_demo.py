from engine import *
from pathlib import Path
import time
P=Path(__file__).resolve().parent;p=P/'examples';cfg=json.loads((p/'configs/layout_02.json').read_text());o=[Object3D('Layout02',import_mesh(p/'models/layout_02.npz')),Object3D('Test board',board_mesh(50,50),'target',np.array([-207.,0,0]),np.array([90.,0,90.]))];cams=[Camera(c['id'],np.array(c['center_world_mm']),np.array(c['R_world_from_camera']),validate_calibration(c['intrinsics'])) for c in cfg['cameras']];scene=build_scene(o);start=time.time();images=[]
for i,c in enumerate(cams):
 r=render_camera(o,c,320,scene);cv2.imwrite(str(P/'validation'/f'camera_{i+1}.png'),cv2.cvtColor(r['image'],cv2.COLOR_RGB2BGR));images.append({k:v for k,v in r.items() if not isinstance(v,np.ndarray)});print(c.name,'rendered',flush=True)
m,points,count=evaluate(o,cams,10000,scene);(P/'validation/demo_metrics.json').write_text(json.dumps({'images':images,'surface':m,'elapsed_s':time.time()-start},indent=2));save_session(P/'examples/four_camera_board.mcv',o,cams);print(m,flush=True)
