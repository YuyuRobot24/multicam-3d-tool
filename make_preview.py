from pathlib import Path
import numpy as np,json,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from PIL import Image
P=Path(__file__).resolve().parent
fig=plt.figure(figsize=(16,8),facecolor='#f4f7fa');gs=fig.add_gridspec(2,4,height_ratios=[1.5,1],hspace=.12)
ax=fig.add_subplot(gs[0,:2],projection='3d');d=np.load(P/'examples/models/layout_02.npz');v=d['vertices'];f=d['faces'];f=f[np.all(v[f,0]<-105,axis=1)]
ax.add_collection3d(Poly3DCollection(v[f],facecolors='#7d929e',edgecolors='none',alpha=.5))
board=np.array([[-207,-25,-25],[-207,25,-25],[-207,25,25],[-207,-25,25]]);ax.add_collection3d(Poly3DCollection([board],facecolors='#e9b75b',alpha=.3))
cfg=json.loads((P/'examples/configs/layout_02.json').read_text())
for c in cfg['cameras']:
 o=np.array(c['center_world_mm']);ax.scatter(*o,color='#028c88');ax.quiver(*o,-6,0,0,color='#028c88')
 for e in board:ax.plot(*np.array([o,e]).T,color='#028c88',alpha=.25,lw=.7)
ax.set(xlim=(-215,-105),ylim=(-32,32),zlim=(-32,32));ax.set_box_aspect((110,64,64));ax.view_init(20,135);ax.set_axis_off();ax.set_title('Example geometry | Layout 02 + 50 x 50 mm board',fontsize=12)
ax=fig.add_subplot(gs[0,2:]);ax.axis('off');ax.text(.02,.9,'MULTI-CAMERA 3D WORKBENCH',fontsize=20,weight='bold',color='#0f766e');ax.text(.02,.72,'Local desktop tool · Python / Qt / VTK\n\nImport CAD or meshes · Pick a surface · Adjust poses\nLoad calibration · Move board / target · Render each camera\nMeasure visible area, overlap and blind surfaces\nOptional observed-image polygon masks\n\nBelow: ray-rendered views using your supplied calibration.\nPurple corners: calibration inversion is not reliable.\nThis is a geometry/rendering example, not a GUI screenshot.',fontsize=12,linespacing=1.5,va='top')
for i in range(4):
 ax=fig.add_subplot(gs[1,i]);ax.imshow(Image.open(P/'validation'/f'camera_{i+1}.png'));ax.set_axis_off();ax.set_title(f'Camera {i+1} | distorted ray image',fontsize=11)
fig.savefig(P/'tool_preview.png',dpi=150,bbox_inches='tight')
