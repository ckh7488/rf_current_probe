"""Create a self-contained viewer from the current saved CAD, without remodelling."""
from pathlib import Path
import base64, hashlib, json, shutil, struct

P=Path(__file__).resolve().parent; R=P.parent
S=R/'mechanical/clamp_A07_DRAFT'
P.joinpath('dist').mkdir(exist_ok=True); P.joinpath('vendor').mkdir(exist_ok=True)
vendor=Path(r'C:\Users\artzy\Documents\ChatGPT\test_board\showcase\reports\porta-pcb\vendor')
for n in ['three.min.js','OrbitControls.js','LICENSE-three.txt']:
 if not (P/'vendor'/n).exists(): shutil.copy2(vendor/n,P/'vendor'/n)
fixture=json.loads((S/'fixture_mesh.json').read_text())
head=json.loads((S/'assembly_mesh.json').read_text())
buf=bytearray(); parts=[]; maxerr=0.0
for n,p in fixture.items():
 vs=[v for row in p['vertices'] for v in row]; ids=[i for row in p['triangles'] for i in row]
 vo=len(buf); vb=struct.pack('<'+'f'*len(vs),*vs); buf.extend(vb)
 io=len(buf); buf.extend(struct.pack('<'+'I'*len(ids),*ids))
 maxerr=max(maxerr,max(abs(a-b) for a,b in zip(vs,struct.unpack('<'+'f'*len(vs),vb))))
 base=n.removeprefix('Head_').removeprefix('Standalone_')
 group=head.get(base,{}).get('group','BENCH')
 parts.append(dict(name=n,base=base,group=group,color=p['color'],vo=vo,vc=len(vs)//3,io=io,ic=len(ids)))
metadata={'format':'RFCP indexed actual CAD mesh / millimetres','parts':parts,
 'revision':'A07','source_directory':str(S.relative_to(R)),
 'source_sha256':{n:hashlib.sha256((S/n).read_bytes()).hexdigest() for n in ['fixture_mesh.json','assembly_mesh.json']},
 'triangle_count':sum(p['ic']//3 for p in parts),'maximum_float32_rounding_mm':maxerr,
 'binary_sha256':hashlib.sha256(buf).hexdigest(),'remodelled':False,'decimated':False}
model={**metadata,'data':base64.b64encode(buf).decode()}
template=(P/'template.html').read_text(encoding='utf-8')
style=(P/'style.css').read_text(encoding='utf-8'); script='\n'.join((P/n).read_text(encoding='utf-8') for n in ['content.js','kinematics.js','viewer.js'])
html=template.replace('<!--STYLE-->', '<style>'+style+'</style>')
code='\n'.join((P/'vendor'/n).read_text(encoding='utf-8') for n in ['three.min.js','OrbitControls.js'])
html=html.replace('<!--SCRIPTS-->', '<script>'+code.replace('</script','<\\/script')+'</script>\n<script>window.RFCP_MODEL='+json.dumps(model,separators=(',',':'))+';</script>\n<script>'+script+'</script>')
(P/'dist/index.html').write_text(html,encoding='utf-8')
(P/'mesh_manifest.json').write_text(json.dumps(metadata,indent=2)+'\n')
print(json.dumps({'parts':len(parts),'triangles':metadata['triangle_count'],'binary_bytes':len(buf),'html_bytes':(P/'dist/index.html').stat().st_size,'maximum_rounding_mm':maxerr}))
