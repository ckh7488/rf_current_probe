from pathlib import Path
P=Path(__file__).resolve().parent
p=P/'clamp_viewer.js';s=p.read_text(encoding='utf-8')
start=s.index('cable:`');end=s.index('`};',start)
s=s[:start]+'''cable:`<span class="eyebrow">한 노브로 중심까지</span><h2>선을 가운데 맞추는 조작은 따로 없습니다</h2><p>Ø12 mm 선을 일부러 오른쪽 아래에 놓았습니다. 아래의 <b>큰 노브 조임</b> 하나만 움직여 보세요. 세 턱이 함께 좁아지며 선을 가운데로 모읍니다.</p><div class="callout"><b>오른쪽 큰 노브:</b> 세 턱의 동시 조절.<br><b>위의 작은 나사 두 개:</b> 선을 넣기 위해 가로대를 열고 닫는 용도. 중심을 맞추는 조절 나사가 아닙니다.</div><p>01 구역에서 선을 넣을 수 있게 가로대를 여는 모습을 볼 수 있습니다. 선을 넣고 가로대를 닫은 뒤에는 큰 노브 하나로 조절하는 설계입니다.</p><div class="metric"><span>표시된 중심 편차</span><b id="centerError">5.83 mm</b></div><p class="fine">이 화면은 마찰·외피 변형·기구 유격을 생략한 원리 시연입니다. 실제 선이 매끄럽게 중심으로 이동하는지와 눌림·반복성은 아직 시험하지 않았습니다. 조임 힘 제한 장치도 아직 없습니다.</p>''' +s[end:]
s=s.replace("const axes=new T.AxesHelper(16);", "const knobMarkPivot=new T.Group();knobMarkPivot.position.set(80,62.5,23);groups[0].add(knobMarkPivot);const knobMark=new T.Mesh(new T.BoxGeometry(2,.5,11),new T.MeshBasicMaterial({color:'#235164'}));knobMark.position.z=6;knobMarkPivot.add(knobMark);\nconst axes=new T.AxesHelper(16);")
s=s.replace("function update(){const r=Number($('diameter').value)/2,open=Number($('opening').value)/100,", "function update(){const closing=Number($('centering').value)/100,r=mode==='cable'?13-7*closing:Number($('diameter').value)/2,open=mode==='cable'?0:Number($('opening').value)/100,")
old="cable.visible=mode!=='assembly';cable.scale.set(r,mode==='pair'?360:95,r);cable.position.set(0,mode==='cable'?clamp((open-.55)/.45)*35:0,mode==='pair'?0:10);"
new="cable.visible=mode!=='assembly';const cr=mode==='cable'?6:r;const cc=mode==='cable'?window.C01_CENTER_CABLE(r,cr):[0,0];cable.scale.set(cr,mode==='pair'?360:95,cr);cable.position.set(cc[0],cc[1],mode==='pair'?0:10);if($('centerError'))$('centerError').textContent=Math.hypot(...cc).toFixed(2)+' mm';$('centeringOut').textContent=closing===0?'풀림 · 선이 치우친 상태':closing===1?'중심에 모임 · 원리 시연':Math.round(closing*100)+'% 조임';knobMarkPivot.rotation.y=-(r-13)*Math.PI*2;"
assert old in s;s=s.replace(old,new)
s=s.replace("cable:'위 가로대를 열어 케이블 넣기'","cable:'큰 노브 하나 → 치우친 선이 중심으로'")
s=s.replace("$('openingLabel').hidden=m==='assembly';", "$('diameterLabel').hidden=m==='cable';$('centeringLabel').hidden=m!=='cable';$('centering').value=0;$('openingLabel').hidden=m==='assembly'||m==='cable';")
s=s.replace("['diameter','opening','explode','transparent']", "['diameter','opening','explode','transparent','centering']")
s=s.replace("controls.update();renderer.render(scene,camera);", "controls.update();const kp=V(80,66,23+groups[0].position.z).project(camera);$('knobLabel').hidden=mode==='assembly'||kp.z>1;$('knobLabel').style.left=(kp.x+1)*host.clientWidth/2+'px';$('knobLabel').style.top=(1-kp.y)*host.clientHeight/2+'px';renderer.render(scene,camera);")
s=s.replace("setMode('mechanism');$('loading').hidden=true;", "setMode('cable');$('loading').hidden=true;")
p.write_text(s,encoding='utf-8')
