(function(){
  'use strict';
  var doc=document, root=doc.documentElement;
  var reduce=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function $(s,c){return (c||doc).querySelector(s)}
  function $$(s,c){return Array.prototype.slice.call((c||doc).querySelectorAll(s))}
  function setHash(h){try{history.replaceState(null,'',h?('#'+h):(location.pathname+location.search))}catch(e){}}

  /* ---------- header: stuck + dark-band awareness ---------- */
  var head=$('#site-head'), darkBands=$$('.on-mocha,.on-loam,.on-night').filter(function(el){return el!==head});
  function onScroll(){
    head.classList.toggle('is-stuck',window.scrollY>8);
    var probe=head.getBoundingClientRect().bottom+1, dark=false;
    for(var i=0;i<darkBands.length;i++){var r=darkBands[i].getBoundingClientRect();if(r.top<=probe&&r.bottom>probe){dark=true;break}}
    head.classList.toggle('is-dark',dark);
  }
  var ticking=false;
  window.addEventListener('scroll',function(){if(ticking)return;ticking=true;requestAnimationFrame(function(){ticking=false;onScroll()})},{passive:true});
  window.addEventListener('resize',onScroll,{passive:true});
  onScroll();

  /* ---------- mobile menu ---------- */
  var menuBtn=$('#menu-btn'), mnav=$('#mobile-nav');
  function setMenu(open){menuBtn.setAttribute('aria-expanded',String(open));mnav.hidden=!open;$('#menu-label').textContent=open?'Close':'Menu'}
  menuBtn.addEventListener('click',function(){setMenu(menuBtn.getAttribute('aria-expanded')!=='true')});
  $$('a',mnav).forEach(function(a){a.addEventListener('click',function(){setMenu(false)})});

  /* ---------- project filters ---------- */
  var chips=$$('.chip'), cards=$$('[data-tags]'), countEl=$('#work-count');
  function applyFilter(f){
    var n=0;
    cards.forEach(function(c){var show=f==='all'||c.getAttribute('data-tags').split(' ').indexOf(f)>-1;c.hidden=!show;if(show)n++});
    chips.forEach(function(ch){ch.setAttribute('aria-pressed',String(ch.getAttribute('data-filter')===f))});
    countEl.textContent=n===1?'Showing 1 project':'Showing '+n+' projects';
    $('#work-empty').hidden=n>0;
  }
  chips.forEach(function(ch){ch.addEventListener('click',function(){applyFilter(ch.getAttribute('data-filter'))})});

  /* ---------- case-study dialog ---------- */
  var caseDlg=$('#case'), caseMount=$('#case-mount'), order=$$('.case-src').map(function(a){return a.id});
  var current=null, lastFocus=null;
  function openCase(id,push){
    var src=doc.getElementById(id); if(!src||!src.classList.contains('case-src')) return false;
    current=id;
    caseMount.innerHTML='';
    var node=src.cloneNode(true); node.removeAttribute('id'); node.hidden=false; node.classList.remove('case-src'); caseMount.appendChild(node);
    var i=order.indexOf(id);
    $('#case-pos').textContent='Project '+String(i+1).padStart(2,'0')+' / '+String(order.length).padStart(2,'0');
    var prev=order[(i-1+order.length)%order.length], next=order[(i+1)%order.length];
    $('#case-prev').setAttribute('data-go',prev); $('#case-next').setAttribute('data-go',next);
    $$('[data-go-label="prev"]',caseMount).forEach(function(b){b.setAttribute('data-go',prev);b.querySelector('span').textContent=titleOf(prev)});
    $$('[data-go-label="next"]',caseMount).forEach(function(b){b.setAttribute('data-go',next);b.querySelector('span').textContent=titleOf(next)});
    wireFigures();
    if(!caseDlg.open){lastFocus=doc.activeElement;if(caseDlg.showModal)caseDlg.showModal();else caseDlg.setAttribute('open','');root.style.overflow='hidden'}
    caseDlg.scrollTop=0;
    var h=$('h2',caseMount); if(h){h.setAttribute('tabindex','-1');h.focus({preventScroll:true})}
    if(push!==false) setHash(id);
    return true;
  }
  function titleOf(id){var s=doc.getElementById(id);return s?s.getAttribute('data-title'):''}
  function closeCase(){
    if(caseDlg.open){if(caseDlg.close)caseDlg.close();else caseDlg.removeAttribute('open')}
  }
  caseDlg.addEventListener('close',function(){root.style.overflow='';current=null;setHash('');if(lastFocus&&lastFocus.focus)lastFocus.focus()});
  caseDlg.addEventListener('click',function(e){
    var go=e.target.closest('[data-go]'); if(go){e.preventDefault();openCase(go.getAttribute('data-go'));return}
    if(e.target.closest('[data-close]')){e.preventDefault();closeCase()}
  });
  $$('[data-case]').forEach(function(a){a.addEventListener('click',function(e){
    if(e.metaKey||e.ctrlKey||e.shiftKey) return;
    if(openCase(a.getAttribute('data-case'))) e.preventDefault();
  })});
  function fromHash(){var h=(location.hash||'').slice(1); if(h&&order.indexOf(h)>-1) openCase(h,false)}
  window.addEventListener('hashchange',fromHash);
  fromHash();

  /* ---------- lightbox with zoom + pan ---------- */
  var lb=$('#lightbox'), stage=$('#lb-stage'), lbImg=$('#lb-img'), lbCap=$('#lb-cap'), lbCount=$('#lb-count');
  var figs=[], fi=0, scale=1, tx=0, ty=0, pointers={}, startDist=0, startScale=1, last=null;
  function wireFigures(){
    figs=$$('.fig button',caseMount);
    figs.forEach(function(b,i){
      b.addEventListener('click',function(){openLb(i)});
      var im=b.querySelector('img');
      if(i<4){im.loading='eager'; if(i<2) im.setAttribute('fetchpriority','high')}
      trackImg(im,b);
    });
  }
  /* loading state: the placeholder shows until the map arrives; failed loads get a retry */
  function trackImg(im,box){
    function ok(){box.classList.add('is-loaded');box.classList.remove('is-error')}
    function bad(){box.classList.add('is-error')}
    if(im.complete&&im.naturalWidth){ok();return}
    im.addEventListener('load',ok); im.addEventListener('error',bad);
    box.addEventListener('click',function(e){
      if(!box.classList.contains('is-error'))return;
      e.preventDefault(); e.stopImmediatePropagation();
      box.classList.remove('is-error'); var u=im.getAttribute('src'); im.removeAttribute('src'); im.setAttribute('src',u);
    },true);
  }
  $$('.card .thumb').forEach(function(t){var im=t.querySelector('img'); if(im) trackImg(im,t)});
  function apply(){lbImg.style.transform='translate('+tx+'px,'+ty+'px) scale('+scale+')';$('#lb-out').disabled=scale<=1;$('#lb-reset').disabled=scale===1&&tx===0&&ty===0}
  function reset(){scale=1;tx=0;ty=0;apply()}
  function zoom(f,cx,cy){
    var ns=Math.min(6,Math.max(1,scale*f)); if(ns===scale)return;
    var r=stage.getBoundingClientRect(); cx=(cx==null?r.left+r.width/2:cx)-(r.left+r.width/2); cy=(cy==null?r.top+r.height/2:cy)-(r.top+r.height/2);
    tx=cx-(cx-tx)*(ns/scale); ty=cy-(cy-ty)*(ns/scale); scale=ns; if(scale===1){tx=0;ty=0} apply();
  }
  function show(i){
    fi=(i+figs.length)%figs.length; var b=figs[fi], im=b.querySelector('img');
    /* show the thumbnail at once, then swap in the full-resolution map when it arrives */
    var full=b.getAttribute('data-full'), want=fi;
    lbImg.src=b.getAttribute('data-thumb'); lbImg.alt=im.alt;
    lbImg.width=+b.getAttribute('data-w'); lbImg.height=+b.getAttribute('data-h');
    var ld=$('#lb-loading'); ld.hidden=false;
    var pre=new Image(); pre.decoding='async';
    pre.onload=function(){if(fi===want){lbImg.src=full;ld.hidden=true}};
    pre.onerror=function(){if(fi===want){ld.textContent='Full resolution unavailable · showing preview'}};
    ld.textContent='Loading full resolution…'; pre.src=full;
    lbCap.innerHTML=''; var l=doc.createElement('span'); l.className='label'; l.textContent=titleOf(current); lbCap.appendChild(l); lbCap.appendChild(doc.createTextNode(b.parentNode.querySelector('figcaption').textContent));
    lbCount.textContent=(fi+1)+' / '+figs.length;
    $('#lb-prev').disabled=$('#lb-next').disabled=figs.length<2;
    reset();
  }
  function openLb(i){show(i); if(lb.showModal)lb.showModal();else lb.setAttribute('open',''); $('#lb-close').focus()}
  function closeLb(){if(lb.open){if(lb.close)lb.close();else lb.removeAttribute('open')} var b=figs[fi]; if(b)b.focus()}
  $('#lb-in').addEventListener('click',function(){zoom(1.5)});
  $('#lb-out').addEventListener('click',function(){zoom(1/1.5)});
  $('#lb-reset').addEventListener('click',reset);
  $('#lb-prev').addEventListener('click',function(){show(fi-1)});
  $('#lb-next').addEventListener('click',function(){show(fi+1)});
  $('#lb-close').addEventListener('click',closeLb);
  lb.addEventListener('cancel',function(e){e.preventDefault();closeLb()});
  lb.addEventListener('keydown',function(e){
    if(e.key==='ArrowRight'){show(fi+1)} else if(e.key==='ArrowLeft'){show(fi-1)}
    else if(e.key==='+'||e.key==='='){zoom(1.5)} else if(e.key==='-'){zoom(1/1.5)} else if(e.key==='0'){reset()}
  });
  stage.addEventListener('wheel',function(e){e.preventDefault();zoom(e.deltaY<0?1.2:1/1.2,e.clientX,e.clientY)},{passive:false});
  stage.addEventListener('dblclick',function(e){if(scale>1)reset();else zoom(2.5,e.clientX,e.clientY)});
  stage.addEventListener('pointerdown',function(e){
    stage.setPointerCapture(e.pointerId); pointers[e.pointerId]={x:e.clientX,y:e.clientY};
    var ids=Object.keys(pointers);
    if(ids.length===2){var a=pointers[ids[0]],b=pointers[ids[1]];startDist=Math.hypot(a.x-b.x,a.y-b.y);startScale=scale}
    last={x:e.clientX,y:e.clientY}; stage.classList.add('is-dragging');
  });
  stage.addEventListener('pointermove',function(e){
    if(!pointers[e.pointerId])return; pointers[e.pointerId]={x:e.clientX,y:e.clientY};
    var ids=Object.keys(pointers);
    if(ids.length===2&&startDist){var a=pointers[ids[0]],b=pointers[ids[1]];var d=Math.hypot(a.x-b.x,a.y-b.y);var target=Math.min(6,Math.max(1,startScale*d/startDist));zoom(target/scale,(a.x+b.x)/2,(a.y+b.y)/2);return}
    if(scale>1&&last){tx+=e.clientX-last.x;ty+=e.clientY-last.y;apply()}
    last={x:e.clientX,y:e.clientY};
  });
  function up(e){delete pointers[e.pointerId]; if(Object.keys(pointers).length<2)startDist=0; if(!Object.keys(pointers).length){stage.classList.remove('is-dragging');last=null}}
  stage.addEventListener('pointerup',up); stage.addEventListener('pointercancel',up);

  /* ---------- email (assembled here so plain-text scrapers miss it) ---------- */
  var addr=['dhananjaysmadaik','gmail.com'].join('@');
  $$('[data-mail]').forEach(function(el){
    if(el.tagName==='A'){el.href='mailto:'+addr} else {el.textContent=addr}
  });
  var copyBtn=$('#copy-mail');
  if(copyBtn){copyBtn.addEventListener('click',function(){
    function done(t){copyBtn.textContent=t;setTimeout(function(){copyBtn.textContent='Copy'},1800)}
    function fallback(){var el=$('#mail-text'),r=doc.createRange();r.selectNodeContents(el);var s=getSelection();s.removeAllRanges();s.addRange(r);done('Selected')}
    if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(addr).then(function(){done('Copied')},fallback)}else fallback();
  })}
  var yr=$('#year'); if(yr) yr.textContent=String(new Date().getFullYear());

  /* ---------- hero: procedural contour map ---------- */
  var cv=$('#contours');
  function rng(seed){var a=seed>>>0;return function(){a=a+0x6D2B79F5|0;var t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296}}
  function noise(seed){
    var r=rng(seed),p=new Uint8Array(512),q=[],i,j,t;for(i=0;i<256;i++)q[i]=i;
    for(i=255;i>0;i--){j=(r()*(i+1))|0;t=q[i];q[i]=q[j];q[j]=t}for(i=0;i<512;i++)p[i]=q[i&255];
    var gx=[1,-1,1,-1,1,-1,0,0],gy=[1,1,-1,-1,0,0,1,-1];
    return function(x,y){var X=Math.floor(x),Y=Math.floor(y),xf=x-X,yf=y-Y;X&=255;Y&=255;
      var u=xf*xf*xf*(xf*(xf*6-15)+10),v=yf*yf*yf*(yf*(yf*6-15)+10);
      var a=p[p[X]+Y]&7,b=p[p[X+1]+Y]&7,c=p[p[X]+Y+1]&7,d=p[p[X+1]+Y+1]&7;
      var n0=gx[a]*xf+gy[a]*yf,n1=gx[b]*(xf-1)+gy[b]*yf,n2=gx[c]*xf+gy[c]*(yf-1),n3=gx[d]*(xf-1)+gy[d]*(yf-1);
      var x1=n0+u*(n1-n0),x2=n2+u*(n3-n2);return x1+v*(x2-x1)};
  }
  function drawContours(){
    if(!cv||!cv.getContext)return;
    var w=cv.clientWidth,h=cv.clientHeight,dpr=Math.min(2,window.devicePixelRatio||1);
    if(!w||!h)return;
    cv.width=Math.round(w*dpr);cv.height=Math.round(h*dpr);
    var ctx=cv.getContext('2d');ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,w,h);
    var n1=noise(7),n2=noise(31),cell=w<700?7:9,cols=Math.ceil(w/cell)+1,rows=Math.ceil(h/cell)+1,F=new Float32Array(cols*rows);
    var sc=2.6/Math.max(w,900);
    for(var y=0;y<rows;y++)for(var x=0;x<cols;x++){
      var u=x*cell*sc,v=y*cell*sc,wx=u+.45*n2(u*.6+4,v*.6+9),wy=v+.45*n2(u*.6+13,v*.6+2);
      var e=.55*n1(wx,wy)+.28*n1(wx*2.1+5,wy*2.1+1)+.12*n1(wx*4.3+9,wy*4.3+7);
      /* a valley running across the sheet, like the Satluj */
      var vy=h*(.62+.12*Math.sin(x*cell/w*5.2+.8)+.05*Math.sin(x*cell/w*13.1)),dv=Math.abs(y*cell-vy)/h;
      F[y*cols+x]=e+Math.min(1,dv*2.2)*.55;
    }
    var levels=22,minV=-.6,maxV=1.2,step=(maxV-minV)/levels;
    function seg(lv){
      ctx.beginPath();
      for(var y=0;y<rows-1;y++)for(var x=0;x<cols-1;x++){
        var a=F[y*cols+x],b=F[y*cols+x+1],c=F[(y+1)*cols+x+1],d=F[(y+1)*cols+x];
        var idx=(a>lv?8:0)|(b>lv?4:0)|(c>lv?2:0)|(d>lv?1:0); if(idx===0||idx===15)continue;
        var X=x*cell,Y=y*cell,t;
        var pT=[X+cell*((lv-a)/(b-a)),Y],pR=[X+cell,Y+cell*((lv-b)/(c-b))],pB=[X+cell*((lv-d)/(c-d)),Y+cell],pL=[X,Y+cell*((lv-a)/(d-a))];
        var L={1:[pL,pB],2:[pB,pR],3:[pL,pR],4:[pT,pR],5:[pL,pT,pB,pR],6:[pT,pB],7:[pL,pT],8:[pL,pT],9:[pT,pB],10:[pT,pR,pL,pB],11:[pT,pR],12:[pL,pR],13:[pB,pR],14:[pL,pB]}[idx];
        for(var k=0;k<L.length;k+=2){ctx.moveTo(L[k][0],L[k][1]);ctx.lineTo(L[k+1][0],L[k+1][1])}
      }
      ctx.stroke();
    }
    for(var i=1;i<levels;i++){
      var idxLine=i%5===0;
      ctx.strokeStyle=idxLine?'rgba(229,228,226,.26)':'rgba(229,228,226,.11)';
      ctx.lineWidth=idxLine?1.1:.8; seg(minV+i*step);
    }
    /* river along the valley floor */
    ctx.beginPath();ctx.strokeStyle='rgba(159,214,236,.55)';ctx.lineWidth=1.6;
    for(var px=0;px<=w;px+=6){var py=h*(.62+.12*Math.sin(px/w*5.2+.8)+.05*Math.sin(px/w*13.1));if(px===0)ctx.moveTo(px,py);else ctx.lineTo(px,py)}
    ctx.stroke();
    cv.classList.add('is-drawn');
  }
  if(cv){
    var rz; window.addEventListener('resize',function(){clearTimeout(rz);rz=setTimeout(drawContours,180)},{passive:true});
    (window.requestIdleCallback||function(f){return setTimeout(f,60)})(drawContours);
  }
})();
