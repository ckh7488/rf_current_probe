'use strict';
(() => {
  const $ = s => document.querySelector(s);
  const $$ = s => [...document.querySelectorAll(s)];
  const NS = 'http://www.w3.org/2000/svg';
  const svgEl = (name, attrs = {}, text) => {
    const n = document.createElementNS(NS, name);
    Object.entries(attrs).forEach(([k, v]) => n.setAttribute(k, String(v)));
    if (text !== undefined) n.textContent = text;
    return n;
  };
  const setPressed = (selector, selected, key) => $$(selector).forEach(b => b.setAttribute('aria-pressed', String(b.dataset[key] === String(selected))));
  const palette = {SIG:'var(--sc-tx)', GND:'var(--sc-ground)'};
  const boardState = {layer:'F.Cu', net:'all', zoom:false};
  function renderBoard() {
    const d = window.A03_BOARD, s = $('#board');
    if (!d) { $('#board-status').textContent = 'PCB 데이터를 읽지 못했습니다. 페이지를 다시 불러오세요.'; return; }
    s.replaceChildren(svgEl('title', {id:'board-title'}, 'A03 실제 PCB와 전류 경로'), svgEl('desc', {id:'board-desc'}, '중앙 SIG와 창 바깥 GND 동박. 앞면과 뒷면은 같은 투시 좌표.'));
    s.setAttribute('viewBox', boardState.zoom ? '46 25 53 43' : '-6 -5 156 104');
    const opacity = net => boardState.net === 'all' || boardState.net === net ? 1 : .1;
    s.append(svgEl('path', {d:d.boardOutlinePath, 'fill-rule':'evenodd',fill:'var(--sc-phy)', 'fill-opacity':.27,stroke:'var(--sc-stage-ink)','stroke-width':.35}));
    for (const z of d.zones.filter(z => z.layer === boardState.layer)) {
      const path = 'M ' + z.points.map(p => p.join(' ')).join(' L ') + ' Z';
      s.append(svgEl('path', {d:path,'fill-rule':z.fillRule || 'evenodd',fill:palette[z.net],opacity:opacity(z.net)*.8,'data-zone-net':z.net}));
    }
    for (const v of [...d.vias, ...d.pads]) {
      const g = svgEl('g', {opacity:v.net ? opacity(v.net) : 1});
      const size = Array.isArray(v.size) ? v.size[0] : v.size;
      if (v.type !== 'np_thru_hole') g.append(svgEl('circle',{cx:v.xy[0],cy:v.xy[1],r:size/2,fill:palette[v.net] || 'var(--sc-stage-ink)',stroke:'var(--sc-stage-ink)','stroke-width':.12}));
      g.append(svgEl('circle',{cx:v.xy[0],cy:v.xy[1],r:v.drill/2,fill:'var(--sc-stage)',stroke:'var(--sc-stage-ink)','stroke-width':.12}));
      if (v.ref) g.append(svgEl('title',{},`${v.ref} ${v.pin || ''} · ${v.net || '고정 홀'} · Ø${v.drill} mm`));
      s.append(g);
    }
    const labels = boardState.zoom ? [[72,29,'중앙 SIG'],[54,58,'창'],[89,58,'창']] : [[84,13,'J1 · IN'],[90,82,'J2 · OUT'],[10,46,'GND'],[132,46,'GND'],[45,49,'창'],[100,49,'창']];
    labels.forEach(([x,y,t]) => s.append(svgEl('text',{x,y,fill:'var(--sc-stage-ink)','font-family':'var(--sc-font)','font-size':boardState.zoom?2.4:3.2,'text-anchor':'middle','font-weight':650},t)));
    const core = svgEl('g',{'aria-label':'설명용 코어 위치 표시'});
    core.append(svgEl('rect',{x:54,y:39.5,width:36,height:13.7,rx:2,fill:'none',stroke:'var(--sc-stage-ink)','stroke-dasharray':'1.8 1.4','stroke-width':.55}));
    core.append(svgEl('text',{x:72,y:boardState.zoom?64:61,fill:'var(--sc-stage-ink)','font-family':'var(--sc-font)','font-size':boardState.zoom?2.3:3,'text-anchor':'middle'},'점선: 코어 위치 개념'));
    s.append(core);
    const dir = svgEl('g',{opacity:opacity('SIG'),fill:palette.SIG});
    dir.append(svgEl('path',{d:'M 70.7 33 L 73.3 33 L 72 36 Z'}));
    s.append(dir);
    const netText = {all:'중앙 SIG와 창 바깥 GND를 함께 표시합니다.',SIG:'중앙 신호 전류 경로를 강조합니다. 아래쪽 접지도 중앙 브리지에서 분리되어 있습니다.',GND:'창 바깥의 귀환 동박을 강조합니다. 코어가 감싸는 중앙 브리지에는 GND가 없습니다.'};
    $('#board-status').textContent = `${boardState.layer === 'F.Cu' ? '앞면' : '뒷면 · 앞에서 투시'} · ${netText[boardState.net]}`;
    setPressed('[data-layer]',boardState.layer,'layer');setPressed('[data-net]',boardState.net,'net');
    $('#zoom-board').setAttribute('aria-pressed',String(boardState.zoom));
  }
  $$('[data-layer]').forEach(b => b.addEventListener('click',()=>{boardState.layer=b.dataset.layer;renderBoard();}));
  $$('[data-net]').forEach(b => b.addEventListener('click',()=>{boardState.net=b.dataset.net;renderBoard();}));
  $('#zoom-board').addEventListener('click',()=>{boardState.zoom=!boardState.zoom;renderBoard();});
  $('#reset-board').addEventListener('click',()=>{Object.assign(boardState,{layer:'F.Cu',net:'all',zoom:false});renderBoard();});

  const stages = [
    {title:'먼저 케이블 끝에서 SOLT', text:'실제 사용할 두 동축 케이블의 끝을 기준면으로 두고 2포트 교정을 적용합니다. 각 포트의 Open·Short·Load와 Through를 장비의 안내에 따라 측정합니다.',save:'교정 ID · 주파수 점 · 출력 레벨 · IFBW',note:'이 교정은 VNA와 케이블의 오차를 처리합니다. A03와 프로브의 교정은 다음 단계에서 진행합니다.'},
    {title:'01 · 빈 지그 응답 저장',text:'프로브를 장착하지 않은 A03에 P1과 P2를 연결합니다. 지그의 반사·전달을 기록하고, 다음 단계의 헤드 장착 결과와 비교합니다.',save:'fixture_through_empty.s2p',note:'이 파일 하나를 빼는 것으로 교정이 끝나지 않습니다. 전류 기준에 사용하는 through는 다음의 헤드 장착 상태입니다.'},
    {title:'02 · 헤드 장착 through',text:'프로브를 중앙 브리지에 장착합니다. 지그 OUT은 P2에, 프로브 SMA 출력은 외장 50 Ω 로드에 연결합니다.',save:'fixture_through_head_loaded.s2p',note:'여기서 S21,thr와 S22,thr를 얻습니다. 지그·프로브·입력 동축의 위치를 고정한 채 다음 단계로 갑니다.'},
    {title:'03 · 프로브 전달 측정',text:'RF OFF 후 P2와 같은 외장 로드의 위치를 맞바꿉니다. 지그 OUT은 로드로, 프로브 SMA는 P2로 연결합니다.',save:'probe_transfer_5t.s2p',note:'여기서 S21,tr를 얻습니다. P2가 프로브의 50 Ω 종단을 맡으므로 프로브 출력에 외장 로드를 병렬로 더하지 않습니다.'},
    {title:'04 · 같은 로드의 반사',text:'RF OFF 후 2포트 교정과 배치를 저장하고 P2 케이블을 분리합니다. VNA의 SMA 암 포트에 모델이 확인된 수형 OPEN·SHORT·LOAD로 별도 1포트 SOL을 적용합니다. 같은 외장 수형 로드를 그 암 포트에 직접 연결해 복소 ΓL을 저장합니다.',save:'primary_load_s11.s1p',note:'물리 P2 반사 S22를 1포트 S1P로 내보내면 파일 안에서는 S11입니다. 로드·암 기준면·표준 모델·물리 포트·별도 교정 ID를 기록합니다. M/M 케이블 끝에는 직접 연결되지 않으며 F/F 어댑터만 추가해 기존 교정을 유지하지 않습니다. 작업용 로드를 SOL 표준으로 쓰지 않습니다. through/전달 재측정 전 2포트 배치를 복구하고 유효성을 재확인합니다.'}
  ];
  let activeStage = 0;
  function drawConnection() {
    const s=$('#connection-diagram'),mobile=window.matchMedia('(max-width:500px)').matches;
    s.replaceChildren(svgEl('title',{id:'connection-title'},stages[activeStage].title));
    const W=mobile?360:840,H=mobile?410:420;s.setAttribute('viewBox',`0 0 ${W} ${H}`);
    function node(x,y,w,h,label,sub,cls='') {
      const g=svgEl('g',{class:`node ${cls}`});g.append(svgEl('rect',{x,y,width:w,height:h,rx:9}));
      g.append(svgEl('text',{x:x+w/2,y:y+(sub?h/2-3:h/2+6),'text-anchor':'middle'},label));
      if(sub) g.append(svgEl('text',{x:x+w/2,y:y+h/2+20,'text-anchor':'middle',class:'small'},sub));
      s.append(g);
    }
    function wire(path,cls='') {s.append(svgEl('path',{d:path,class:`wire ${cls}`}));}
    function note(x,y,t) {s.append(svgEl('text',{x,y,class:'diagram-note','text-anchor':'middle'},t));}
    if (activeStage===0) {
      if (mobile) {
        wire('M 85 110 V 175');wire('M 275 110 V 175','secondary');
        node(25,35,120,75,'VNA P1','케이블 1');node(215,35,120,75,'VNA P2','케이블 2');
        node(20,175,130,65,'케이블 끝','기준면');node(210,175,130,65,'케이블 끝','기준면');
        node(25,280,310,75,'각 포트 O / S / L','두 기준면 사이 Through');note(180,385,'먼저 2포트 교정을 적용합니다.');
      } else {
        wire('M 220 125 H 335');wire('M 620 125 H 505','secondary');
        node(60,85,160,80,'VNA P1','케이블 1');node(620,85,160,80,'VNA P2','케이블 2');
        node(335,83,170,84,'케이블 끝','두 교정 기준면');
        node(195,250,450,80,'각 포트 Open / Short / Load','두 기준면 사이 Through');
        note(420,380,'SOLT 후 케이블 끝에 A03를 연결합니다.');
      }
      return;
    }
    if (activeStage===4) {
      if(mobile){wire('M 180 115 V 240','load');node(85,35,190,80,'VNA P2 · SMA 암','별도 1포트 SOL');node(85,240,190,80,'외장 50 Ω · SMA 수','같은 작업용 로드','load');note(180,180,'암 기준면에 직접 연결');note(180,375,'P2 S22 → S1P의 S11 → ΓL');}
      else{wire('M 245 175 H 575','load');node(65,130,180,90,'VNA P2 · SMA 암','별도 1포트 SOL');node(575,130,200,90,'외장 50 Ω · SMA 수','같은 작업용 로드','load');note(410,140,'암 기준면에 직접 연결');note(420,320,'P2 S22 → S1P의 S11 → ΓL · 같은 로드 사용');}
      return;
    }
    const loaded=activeStage>=2,transfer=activeStage===3;
    if(mobile) {
      // Fixed node locations keep the P2/load swap visible between steps 02 and 03.
      wire('M 67 97 V 133 H 119 V 163');
      wire('M 242 198 H 295 V 98',transfer?'load':'secondary');
      if(loaded){wire('M 180 233 V 273','coupling');wire('M 240 308 H 270',transfer?'secondary':'load');}
      node(10,25,116,72,'VNA P1','입력');
      node(234,25,116,72,transfer?'외장 50 Ω':'VNA P2',transfer?'출구 종단':'출구 수신',transfer?'load':'');
      node(68,163,174,70,'A03 · IN → OUT',loaded?'헤드 장착':'빈 지그','fixture');
      if(loaded){node(105,273,135,70,'프로브','SMA 출력');node(270,273,80,70,transfer?'P2':'50 Ω',transfer?'수신':'로드',transfer?'':'load');note(117,258,'자기 결합');}
      note(180,390,loaded?'02 ↔ 03: P2와 로드만 교환':'프로브 없이 S2P를 저장합니다.');
    } else {
      wire('M 190 130 H 330');wire('M 525 130 H 650',transfer?'load':'secondary');
      if(loaded){wire('M 428 175 V 263','coupling');wire('M 525 307 H 650',transfer?'secondary':'load');}
      node(30,85,160,90,'VNA P1','입력');node(330,85,195,90,'A03 · IN → OUT',loaded?'헤드 장착':'빈 지그','fixture');
      node(650,85,165,90,transfer?'외장 50 Ω':'VNA P2',transfer?'출구 종단':'출구 수신',transfer?'load':'');
      if(loaded){node(330,263,195,90,'프로브','SMA 출력');node(650,263,165,90,transfer?'VNA P2':'외장 50 Ω',transfer?'프로브 수신':'헤드 종단',transfer?'':'load');note(487,223,'자기 결합');}
      note(420,400,loaded?'같은 배치 유지 · 02 ↔ 03에서 P2와 로드 교환':'프로브 없이 지그 응답을 저장합니다.');
    }
  }
  function selectStage(n) {
    activeStage=n;setPressed('[data-stage]',n,'stage');
    const st=stages[n],target=$('#stage-detail');target.replaceChildren();
    const h=document.createElement('h3');h.textContent=st.title;
    const p=document.createElement('p');p.textContent=st.text;
    const save=document.createElement('p');save.className='save';
    const small=document.createElement('small');small.textContent='저장할 것';const code=document.createElement('code');code.textContent=st.save;save.append(small,code);
    const note=document.createElement('p');note.textContent=st.note;target.append(h,p,save,note);drawConnection();
  }
  $$('[data-stage]').forEach(b=>b.addEventListener('click',()=>selectStage(Number(b.dataset.stage))));
  let resizeTask;
  window.addEventListener('resize',()=>{clearTimeout(resizeTask);resizeTask=setTimeout(drawConnection,100);});

  const resultState={frequency:500,metric:'S21_dB'};
  const metrics={
    S11_dB:{label:'S11 · 반사',heading:'입구로 돌아온 신호',description:'큰 반사 자체를 교정 제외 조건으로 쓰지 않습니다. 출력으로 전달된 전류를 측정에 반영하고 K로 코어 전류를 구합니다.',limits:[-20,0],ticks:[-20,-15,-10,-5,0]},
    S21_dB:{label:'S21 · 전달',heading:'출력으로 전달된 신호',description:'500 MHz에서 약 −5.0…−5.8 dB의 전달 감소가 있습니다. 이 감소 자체는 보정을 막지 않습니다. 실제 교정에는 헤드 장착 상태의 복소 응답을 사용합니다.',limits:[-7,0],ticks:[-6,-4,-2,0]},
    K_dB:{label:'K · 전류비',heading:'출구에서 코어 위치로 환산',description:'K는 Icore/Iout입니다. 표의 크기는 적용할 보정량입니다. 모델 변형의 범위나 K값을 보정 후 잔여 오차로 읽지 않습니다.',limits:[0,2],ticks:[0,.5,1,1.5,2]}
  };
  function renderResults() {
    const data=window.A03_RESULTS;if(!data)return;
    const point=data.points.find(p=>p.frequency_mhz===resultState.frequency);
    const cards=$('#metrics');cards.replaceChildren();
    for(const [key,meta] of Object.entries(metrics)) {
      const r=point[key],card=document.createElement('div');card.className='metric';
      const small=document.createElement('small');small.textContent=meta.label;
      const b=document.createElement('b');b.textContent=`${r.min.toFixed(2)} … ${r.max.toFixed(2)}`;
      const span=document.createElement('span');span.textContent=`dB · ${point.frequency_mhz} MHz`;card.append(small,b,span);cards.append(card);
    }
    const meta=metrics[resultState.metric];$('#plot-heading').textContent=meta.heading;$('#plot-description').textContent=meta.description;
    setPressed('[data-frequency]',resultState.frequency,'frequency');setPressed('[data-metric]',resultState.metric,'metric');
    const plot=$('#result-plot');plot.replaceChildren(svgEl('title',{},`${meta.label} · 저장된 세 주파수의 모델 최소–최대 범위`));
    const top=25,bottom=230,left=65,right=665;
    const y=v=>bottom-(v-meta.limits[0])/(meta.limits[1]-meta.limits[0])*(bottom-top);
    for(const tick of meta.ticks){plot.append(svgEl('line',{x1:left,y1:y(tick),x2:right,y2:y(tick),stroke:'var(--sc-line)'}));plot.append(svgEl('text',{x:52,y:y(tick)+5,'text-anchor':'end'},String(tick)));}
    plot.append(svgEl('text',{x:20,y:16},'dB'));
    for(const [i,p] of data.points.entries()) {
      const x=140+i*235,r=p[resultState.metric],selected=p.frequency_mhz===resultState.frequency;
      if(selected)plot.append(svgEl('rect',{x:x-70,y:top,width:140,height:bottom-top,fill:'var(--sc-accent-soft)',opacity:.55}));
      const color=selected?'var(--sc-accent)':'var(--sc-phy)';
      plot.append(svgEl('line',{x1:x,y1:y(r.min),x2:x,y2:y(r.max),stroke:color,'stroke-width':4}));
      for(const v of [r.min,r.max])plot.append(svgEl('line',{x1:x-15,y1:y(v),x2:x+15,y2:y(v),stroke:color,'stroke-width':3}));
      plot.append(svgEl('circle',{cx:x,cy:y(r.max),r:4,fill:color}));
      plot.append(svgEl('text',{x,y:261,'text-anchor':'middle',class:selected?'plot-selected':''},`${p.frequency_mhz} MHz`));
    }
  }
  $$('[data-frequency]').forEach(b=>b.addEventListener('click',()=>{resultState.frequency=Number(b.dataset.frequency);renderResults();}));
  $$('[data-metric]').forEach(b=>b.addEventListener('click',()=>{resultState.metric=b.dataset.metric;renderResults();}));
  renderBoard();selectStage(0);renderResults();
})();
