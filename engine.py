"""Millimetre-based geometric cameras, ray images and surface coverage."""
from dataclasses import dataclass,field
from pathlib import Path
import io,json,zipfile,re
import numpy as np
import cv2,trimesh,yaml
from scipy.spatial.transform import Rotation
from trimesh.ray.ray_triangle import RayMeshIntersector

def undistort(p,K,D):
 criteria=(cv2.TERM_CRITERIA_COUNT|cv2.TERM_CRITERIA_EPS,60,1e-10)
 if hasattr(cv2,'undistortPointsIter'):return cv2.undistortPointsIter(p,K,D if D.size else None,None,None,criteria)
 return cv2.undistortPoints(p,K,D if D.size else None,criteria=criteria)

DEFAULT_K={'model':'opencv','image_size':[1280,720],'K':[[669.2158698562481,0,645.1734423597007],[0,666.8886843050188,365.79785450569784],[0,0,1]],'D':[-.12640186015194008,.023595665378689623,.004526243693052268,-.004680181702598942,-.020890876265018954]}
def normalise(v):
 v=np.asarray(v,float);return v/max(np.linalg.norm(v),1e-15)
def camera_rotation(forward,up=(0,0,1)):
 z=normalise(forward);up=np.asarray(up,float)
 if abs(np.dot(z,normalise(up)))>.98:up=np.array([0,1,0.])
 x=normalise(np.cross(z,up));y=np.cross(z,x);return np.column_stack([x,y,z])

def validate_calibration(d):
 d=dict(d);d['model']={'pinhole':'opencv','plumb_bob':'opencv','equidistant':'fisheye'}.get(d.get('model','opencv'),d.get('model','opencv'))
 K=np.asarray(d['K'],float);D=np.asarray(d.get('D',[]),float).ravel();size=np.asarray(d['image_size'],int)
 if K.shape!=(3,3) or not np.isfinite(K).all() or K[0,0]<=0 or K[1,1]<=0 or abs(K[0,1])>1e-8 or not np.allclose(K[2],[0,0,1]):raise ValueError('Invalid camera matrix / nonzero skew unsupported')
 if size.shape!=(2,) or min(size)<=0:raise ValueError('image_size must be [width,height]')
 if d['model']=='fisheye' and len(D)!=4:raise ValueError('Fisheye requires four coefficients')
 if d['model']=='opencv' and len(D) not in (0,4,5,8,12,14):raise ValueError('Unsupported OpenCV coefficient count')
 if d['model'] not in ('opencv','fisheye') or not np.isfinite(D).all():raise ValueError('Invalid distortion model')
 d.update(K=K.tolist(),D=D.tolist(),image_size=size.tolist());return d

def load_calibration(path):
 text=Path(path).read_text(encoding='utf-8-sig');d=None
 if '## camera_matrix' in text:
  d={}
  for heading,key in [('camera_matrix','K'),('distortion_coefficients','D'),('image_size','image_size')]:
   m=re.search(r'##\s+'+heading+r'\s+```(?:yaml|json)?\s*(.*?)```',text,re.S)
   if not m:raise ValueError('Missing report section: '+heading)
   d[key]=yaml.safe_load(m.group(1))
  m=re.search(r'##\s+model\s+([^\n]+)',text);d['model']=m.group(1).strip() if m else 'opencv'
 else:
  try:d=json.loads(text) if Path(path).suffix.lower()=='.json' else yaml.safe_load(text)
  except Exception:pass
  if not isinstance(d,dict):
   fs=cv2.FileStorage(str(path),cv2.FILE_STORAGE_READ)
   if not fs.isOpened():raise ValueError('Cannot read calibration')
   def mat(keys):
    for k in keys:
     n=fs.getNode(k)
     if not n.empty():return n.mat().tolist()
    return None
   def scalar(keys):
    for k in keys:
     n=fs.getNode(k)
     if not n.empty():return int(n.real())
    return 0
   d={'K':mat(['K','camera_matrix','cameraMatrix']),'D':mat(['D','distortion_coefficients','distCoeffs']),'image_size':[scalar(['image_width','width']),scalar(['image_height','height'])],'model':'opencv'};fs.release()
  if 'intrinsics' in d:d=d['intrinsics']
  d['K']=d.get('K',d.get('camera_matrix'));d['D']=d.get('D',d.get('distortion_coefficients',[]))
  for k in ('K','D'):
   if isinstance(d[k],dict):
    a=d[k];d[k]=np.asarray(a['data']).reshape(a.get('rows',1),a.get('cols',len(a['data']))).tolist()
  if 'image_size' not in d:d['image_size']=[d.get('image_width'),d.get('image_height')]
  if 'distortion_model' in d and 'model' not in d:d['model']=d['distortion_model']
 return validate_calibration(d)

@dataclass
class Camera:
 name:str
 center:np.ndarray
 rotation:np.ndarray
 intrinsics:dict=field(default_factory=lambda:json.loads(json.dumps(DEFAULT_K)))
 active:bool=True
 image_mask:np.ndarray|None=None
 def to_dict(self):return dict(name=self.name,center=self.center.tolist(),rotation=self.rotation.tolist(),intrinsics=self.intrinsics,active=self.active)
 @classmethod
 def from_dict(cls,d):return cls(d['name'],np.array(d['center'],float),np.array(d['rotation'],float),validate_calibration(d['intrinsics']),d.get('active',True))

@dataclass
class Object3D:
 name:str
 mesh:trimesh.Trimesh
 role:str='housing'
 position:np.ndarray=field(default_factory=lambda:np.zeros(3))
 angles:np.ndarray=field(default_factory=lambda:np.zeros(3))
 scale:float=1.
 enabled:bool=True
 def world_mesh(self):
  m=self.mesh.copy();m.apply_scale(self.scale);T=np.eye(4);T[:3,:3]=Rotation.from_euler('xyz',self.angles,degrees=True).as_matrix();T[:3,3]=self.position;m.apply_transform(T);return m

def import_mesh(path):
 path=Path(path)
 if path.suffix.lower() in ('.step','.stp'):
  import cadquery as cq
  s=cq.importers.importStep(str(path)).val();v,f=s.tessellate(.05,.1);m=trimesh.Trimesh(np.array([p.toTuple() for p in v]),np.array(f),process=False)
 elif path.suffix.lower()=='.npz':
  d=np.load(path);m=trimesh.Trimesh(d['vertices'],d['faces'],process=False)
 else:
  m=trimesh.load(str(path),force='mesh',process=False)
 if not isinstance(m,trimesh.Trimesh) or not len(m.faces):raise ValueError('No triangle mesh found')
 if not np.isfinite(m.vertices).all():raise ValueError('Invalid mesh coordinates')
 # Convert material/texture to face colours once. Texture detail is approximated.
 try:
  if m.visual.kind=='texture':m.visual=m.visual.to_color()
  colours=np.asarray(m.visual.face_colors)
  if len(colours)!=len(m.faces):raise ValueError()
 except Exception:m.visual.face_colors=np.tile([170,184,193,255],(len(m.faces),1))
 return m

def board_mesh(width,height):
 # Local XY plane, normal +Z; role=target. Native dimensions in mm.
 return trimesh.Trimesh([[-width/2,-height/2,0],[width/2,-height/2,0],[width/2,height/2,0],[-width/2,height/2,0]],[[0,1,2],[0,2,3]],process=False)

def build_scene(objects):
 meshes=[];owner=[];offset=0
 for i,obj in enumerate(objects):
  if not obj.enabled:continue
  m=obj.world_mesh();meshes.append(m);owner.extend([i]*len(m.faces))
 if not meshes:raise ValueError('Scene has no enabled objects')
 return trimesh.util.concatenate(meshes),np.asarray(owner)

def ray_hits(mesh,origins,directions,batch=512):
 inter=RayMeshIntersector(mesh);dist=np.full(len(directions),np.inf);fi=np.full(len(directions),-1,int)
 for a in range(0,len(directions),batch):
  loc,ri,ti=inter.intersects_location(origins[a:a+batch],directions[a:a+batch],multiple_hits=False)
  if len(ri):dist[a+ri]=np.linalg.norm(loc-origins[a+ri],axis=1);fi[a+ri]=ti
 return dist,fi

def pixel_rays(intr,width):
 intr=validate_calibration(intr);iw,ih=intr['image_size'];width=int(width);height=max(1,round(width*ih/iw))
 u=(np.arange(width)+.5)*iw/width-.5;v=(np.arange(height)+.5)*ih/height-.5;U,V=np.meshgrid(u,v);pixels=np.column_stack([U.ravel(),V.ravel()]).reshape(-1,1,2)
 K=np.array(intr['K'],float);D=np.array(intr['D'],float);model=intr['model']
 if model=='fisheye':n=cv2.fisheye.undistortPoints(pixels,K,D)
 else:n=undistort(pixels,K,D)
 xy=n.reshape(-1,2);r=np.column_stack([xy,np.ones(len(xy))]);valid=np.isfinite(r).all(1)
 safe=np.nan_to_num(r,nan=0,posinf=0,neginf=0)
 if model=='fisheye':p,_=cv2.fisheye.projectPoints(safe.reshape(-1,1,3),np.zeros(3),np.zeros(3),K,D)
 else:p,_=cv2.projectPoints(safe,np.zeros(3),np.zeros(3),K,D if D.size else None)
 residual=np.linalg.norm(p.reshape(-1,2)-pixels.reshape(-1,2),axis=1);valid&=residual<.15
 if model=='opencv' and D.size==5:
  k1,k2,_,_,k3=D;roots=np.roots(np.trim_zeros([7*k3,5*k2,3*k1,1],'f'));pos=[x.real for x in roots if abs(x.imag)<1e-8 and x.real>0]
  if pos:valid&=(xy*xy).sum(1)<min(pos)*(1-1e-6)
 safe/=np.maximum(np.linalg.norm(safe,axis=1,keepdims=True),1e-15)
 return safe,valid,(height,width)

def project_visible(points,camera):
 q=(points-camera.center)@camera.rotation;intr=camera.intrinsics;K=np.array(intr['K'],float);D=np.array(intr['D'],float);w,h=intr['image_size'];v=q[:,2]>1e-6;uv=np.full((len(q),2),np.nan)
 if v.any():
  if intr['model']=='fisheye':r,_=cv2.fisheye.projectPoints(q[v].reshape(-1,1,3),np.zeros(3),np.zeros(3),K,D)
  else:r,_=cv2.projectPoints(q[v],np.zeros(3),np.zeros(3),K,D if D.size else None)
  uv[v]=r.reshape(-1,2)
 v&=np.isfinite(uv).all(1)&(uv[:,0]>=-.5)&(uv[:,0]<w-.5)&(uv[:,1]>=-.5)&(uv[:,1]<h-.5)
 ids=np.flatnonzero(v)
 if len(ids):
  pp=uv[ids].reshape(-1,1,2)
  if intr['model']=='fisheye':xy=cv2.fisheye.undistortPoints(pp,K,D).reshape(-1,2)
  else:xy=undistort(pp,K,D).reshape(-1,2)
  truth=q[ids,:2]/q[ids,2:3];v[ids]&=np.linalg.norm(xy-truth,axis=1)<1e-4
 if camera.image_mask is not None:
  if camera.image_mask.shape!=(h,w):raise ValueError('Observation mask resolution must match calibration')
  ids=np.flatnonzero(v);ij=np.floor(uv[ids]+.5).astype(int);ij[:,0]=np.clip(ij[:,0],0,w-1);ij[:,1]=np.clip(ij[:,1],0,h-1);v[ids]&=camera.image_mask[ij[:,1],ij[:,0]]>0
 return v

def render_camera(objects,camera,width=320,prepared=None):
 mesh,owner=prepared if prepared is not None else build_scene(objects)
 rays,valid,shape=pixel_rays(camera.intrinsics,width);world=rays@camera.rotation.T;ids=np.flatnonzero(valid);orig=np.tile(camera.center,(len(ids),1))+world[ids]*.001
 d,fi=ray_hits(mesh,orig,world[ids]);rgb=np.tile([19,27,38],(len(rays),1)).astype(np.uint8);rgb[~valid]=[88,43,91];object_ids=np.full(len(rays),-1,int);depth=np.full(len(rays),np.nan);hit=np.flatnonzero(fi>=0)
 if len(hit):
  pixels=ids[hit];faces=fi[hit];which=owner[faces];object_ids[pixels]=which;depth[pixels]=d[hit]+.001
  n=mesh.face_normals[faces];shade=.35+.65*np.abs((n*(-world[pixels])).sum(1));col=np.asarray(mesh.visual.face_colors)[faces,:3].astype(float)
  for oi,obj in enumerate(objects):
   k=which==oi
   if obj.name=='Test board' and k.any():
    points=camera.center+world[pixels[k]]*depth[pixels[k],None];R=Rotation.from_euler('xyz',obj.angles,degrees=True).as_matrix();local=(points-obj.position)@R/obj.scale;tile=(np.floor(local[:,0]/5)+np.floor(local[:,1]/5)).astype(int)%2
    col[k]=np.where(tile[:,None]==0,[230,235,239],[62,81,102])
  rgb[pixels]=np.clip(col*shade[:,None],0,255).astype('uint8')
 target_ids=[i for i,o in enumerate(objects) if o.enabled and o.role=='target'];mask=np.isin(object_ids,target_ids)&(object_ids>=0)
 if camera.image_mask is not None:
  ih,iw=camera.image_mask.shape
  if [iw,ih]!=camera.intrinsics['image_size']:raise ValueError('Observation mask resolution mismatch')
  mx=np.minimum(((np.arange(shape[1])+.5)*iw/shape[1]).astype(int),iw-1);my=np.minimum(((np.arange(shape[0])+.5)*ih/shape[0]).astype(int),ih-1);roi=camera.image_mask[np.ix_(my,mx)].ravel()>0;mask&=roi;rgb[~roi]=(rgb[~roi]*.3).astype('uint8')
 ys,xs=np.where(mask.reshape(shape));bbox=None
 if len(xs):bbox=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
 return {'image':rgb.reshape(*shape,3),'mask':mask.reshape(shape),'depth_mm':depth.reshape(shape),'object_ids':object_ids.reshape(shape),'valid_pixels_fraction':float(valid.mean()),'target_image_fraction':float(mask.mean()),'target_bbox_preview_pixels':bbox,'preview_size':[shape[1],shape[0]]}

def sample_targets(objects,n=10000):
 meshes=[o.world_mesh() for o in objects if o.enabled and o.role=='target']
 if not meshes:raise ValueError('Set at least one enabled object role to target')
 m=trimesh.util.concatenate(meshes);areas=m.area_faces;total=float(areas.sum());rng=np.random.default_rng(42)
 if total<=0:raise ValueError('Zero target area')
 # Stratified by cumulative area, with random barycentrics. Equal sample area.
 q=(np.arange(n)+rng.random(n))/n*total;ids=np.searchsorted(np.cumsum(areas),q);tri=m.triangles[ids];uv=rng.random((n,2));s=np.sqrt(uv[:,0]);b=np.column_stack([1-s,s*(1-uv[:,1]),s*uv[:,1]]);pts=np.einsum('ni,nij->nj',b,tri)
 return pts,np.full(n,total/n),m

def evaluate(objects,cameras,n=10000,prepared=None):
 active=[c for c in cameras if c.active]
 if not active:raise ValueError('No enabled cameras')
 scene,_=prepared if prepared is not None else build_scene(objects);points,weights,target=sample_targets(objects,n);seen=[]
 for cam in active:
  v=project_visible(points,cam);ids=np.flatnonzero(v)
  if len(ids):
   delta=points[ids]-cam.center;distance=np.linalg.norm(delta,axis=1);r=delta/np.maximum(distance[:,None],1e-15);d,_=ray_hits(scene,np.tile(cam.center,(len(ids),1))+r*.001,r)
   v[ids]&=np.isfinite(d)&(np.abs(d+.001-distance)<.003)
  seen.append(v)
 seen=np.array(seen);count=seen.sum(0);total=float(weights.sum());out={'target_area_mm2':total,'sample_count':n,'covered_mm2':float(weights[count>=1].sum()),'overlap2_mm2':float(weights[count>=2].sum()),'blind_mm2':float(weights[count==0].sum()),'per_camera':[],'pairs':[]}
 for cam,v in zip(active,seen):
  pts=points[v];extent=(pts.max(0)-pts.min(0)).tolist() if len(pts) else [0,0,0]
  item={'name':cam.name,'visible_area_mm2':float(weights[v].sum()),'world_bbox_extent_mm':extent,'board_visible_width_mm':None,'board_visible_height_mm':None}
  boards=[o for o in objects if o.enabled and o.role=='target']
  if len(boards)==1 and boards[0].name=='Test board' and len(pts):
   o=boards[0];R=Rotation.from_euler('xyz',o.angles,degrees=True).as_matrix();local=(pts-o.position)@R;wh=local.max(0)-local.min(0);item['board_visible_width_mm']=float(wh[0]);item['board_visible_height_mm']=float(wh[1])
  out['per_camera'].append(item)
 for i in range(len(active)):
  for j in range(i+1,len(active)):
   a=float(weights[seen[i]&seen[j]].sum());u=float(weights[seen[i]|seen[j]].sum());out['pairs'].append({'cameras':[active[i].name,active[j].name],'intersection_mm2':a,'IoU':a/u if u else None})
 out['coverage_fraction']=out['covered_mm2']/total;out['overlap2_fraction']=out['overlap2_mm2']/total
 return out,points,count

def save_session(path,objects,cameras):
 data={'schema':1,'units':'mm','cameras':[c.to_dict() for c in cameras],'objects':[]}
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
  for i,c in enumerate(cameras):
   if c.image_mask is not None:z.writestr(f'camera_mask_{i}.png',cv2.imencode('.png',c.image_mask.astype('uint8'))[1].tobytes())
  for i,o in enumerate(objects):
   b=io.BytesIO();np.savez_compressed(b,vertices=o.mesh.vertices,faces=o.mesh.faces,face_colors=o.mesh.visual.face_colors);z.writestr(f'mesh_{i}.npz',b.getvalue());data['objects'].append({'name':o.name,'role':o.role,'position':o.position.tolist(),'angles':o.angles.tolist(),'scale':o.scale,'enabled':o.enabled})
  z.writestr('session.json',json.dumps(data))

def load_session(path):
 with zipfile.ZipFile(path) as z:
  d=json.loads(z.read('session.json'))
  if d.get('schema')!=1 or d.get('units')!='mm':raise ValueError('Unsupported session')
  objects=[]
  for i,o in enumerate(d['objects']):
   m=np.load(io.BytesIO(z.read(f'mesh_{i}.npz')));mesh=trimesh.Trimesh(m['vertices'],m['faces'],face_colors=m['face_colors'],process=False);objects.append(Object3D(o['name'],mesh,o['role'],np.array(o['position']),np.array(o['angles']),o['scale'],o['enabled']))
  cameras=[Camera.from_dict(c) for c in d['cameras']]
  for i,c in enumerate(cameras):
   name=f'camera_mask_{i}.png'
   if name in z.namelist():c.image_mask=cv2.imdecode(np.frombuffer(z.read(name),np.uint8),cv2.IMREAD_GRAYSCALE)
  return objects,cameras
