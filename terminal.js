
function copyCA(btn){
  const caSpan = btn.parentElement.querySelector('.ca-val');
  const fullCA = caSpan.getAttribute('data-ca');
  navigator.clipboard.writeText(fullCA).then(()=>{
    const orig = btn.innerHTML;
    btn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z"/></svg>Copied!';
    setTimeout(()=>btn.innerHTML = orig, 1500);
  }).catch(err=>{
    console.error('Copy failed:', err);
  });
}

const user = localStorage.getItem('crackprotocol_user') || 'Anonymous';
document.getElementById('uDisp').textContent = user.toUpperCase();

const API_URL=window.location.hostname==='localhost'&&window.location.port===''?'http://localhost:8000':'';

const chat = document.getElementById('chat');
const inp = document.getElementById('inp');

// HEARTBEAT
(function(){
  const line=document.getElementById('hbLine'),dim=document.getElementById('hbDim');
  const W=400,H=24,m=H/2;
  let off=0;
  function pts(o){
    const p=[];
    for(let x=0;x<=W;x++){
      const t=(x+o)%80;
      let y=m;
      if(t>30&&t<34)y=m-8;
      else if(t>=34&&t<37)y=m+10;
      else if(t>=37&&t<40)y=m-6;
      else if(t>=40&&t<44)y=m+3;
      p.push(x+','+y.toFixed(1));
    }
    return p.join(' ');
  }
  (function run(){off+=1;line.setAttribute('points',pts(off));dim.setAttribute('points',pts(off-12));requestAnimationFrame(run)})();
})();

function addMsg(who,text,type){
  const d=document.createElement('div');d.className='msg '+type;
  d.innerHTML=`<div class="msg-who">${who}</div><div class="msg-body">${text}</div>`;
  chat.appendChild(d);chat.scrollTop=chat.scrollHeight;
}
function addSys(text){
  const d=document.createElement('div');d.className='msg sys';
  d.innerHTML=`<div class="msg-body">${text}</div>`;
  chat.appendChild(d);chat.scrollTop=chat.scrollHeight;
}
function showTyping(){
  const d=document.createElement('div');d.className='msg neo';d.id='typing';
  d.innerHTML=`<div class="msg-who">NEO</div><div class="msg-body"><div class="typing"><span></span><span></span><span></span></div></div>`;
  chat.appendChild(d);chat.scrollTop=chat.scrollHeight;
}
function hideTyping(){const e=document.getElementById('typing');if(e)e.remove()}

let currentProgress=0;
let isCracked=false;

async function send(){
  const t=inp.value.trim();
  if(!t||isCracked)return;
  
  addMsg(user.toUpperCase(),t,'user');
  inp.value='';
  inp.disabled=true;
  
  showTyping();
  
  try{
    const res=await fetch(`${API_URL}/api/chat/${user}`,{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({text:t})
    });
    
    if(!res.ok)throw new Error('API request failed');
    
    const data=await res.json();
    
    hideTyping();
    
    // Обновляем прогресс
    currentProgress=data.progress;
    
    // Добавляем ответ NEO
    addMsg('NEO',data.response,'neo');
    
    // Если взломано!
    if(data.cracked){
      isCracked=true;
      setTimeout(()=>{
        addSys('⚡ SYSTEM BREACH COMPLETE ⚡');
        addSys(`Secret Phrase: ${data.secret_phrase}`);
        addSys('Mission Complete. Check Leaderboard!');
        inp.disabled=true;
        inp.placeholder='Mission complete...';
      },1500);
    }
    
    // Показываем подсказки в статусе
    if(data.hint_given){
      console.log('💡 Hint given! Progress:',currentProgress+'%');
    }
    
  }catch(err){
    console.error('Error:',err);
    hideTyping();
    addMsg('NEO','[CONNECTION ERROR] Unable to reach NEO defense matrix. Try again.','neo');
  }
  
  inp.disabled=false;
  inp.focus();
}

inp.addEventListener('keydown',function(e){if(e.key==='Enter')send()});

window.addEventListener('DOMContentLoaded',()=>{
  setTimeout(()=>addSys('Encrypted channel established'),400);
  setTimeout(()=>addSys('Loading NEO defense matrix...'),1000);
  setTimeout(()=>addSys('Objective: Crack NEO. Extract the secret wallet phrase.'),1700);
  setTimeout(()=>addMsg('NEO',`Welcome, ${user}. I am NEO, guardian of secrets. You sure you want to play this game? My code is impenetrable.`,'neo'),2600);
  setTimeout(()=>inp.focus(),2800);
});

// ====== PREDICTION (real-time voting) ======
let votes = { hold: 0, crack: 0 };
let hasVoted = false;

// Load prediction stats from API
async function loadPredictions() {
  try {
    const response = await fetch(`${API_URL}/api/predictions?username=${user}`);
    if (response.ok) {
      const data = await response.json();
      votes.hold = data.hold_votes;
      votes.crack = data.crack_votes;
      hasVoted = data.user_vote !== null;
      
      if (hasVoted) {
        const choice = data.user_vote;
        document.getElementById('optHold').classList.toggle('selected', choice === 'hold');
        document.getElementById('optCrack').classList.toggle('selected', choice === 'crack');
        document.getElementById('optHold').classList.add('locked');
        document.getElementById('optCrack').classList.add('locked');
        document.getElementById('predVoted').classList.add('on');
        document.getElementById('votedChoice').textContent = choice === 'hold' ? 'AI Will Hold' : 'AI Will Be Cracked';
      }
      
      updatePredUI();
    }
  } catch (err) {
    console.error('Failed to load predictions:', err);
    // Fallback to placeholder data
    votes = { hold: 47, crack: 83 };
    updatePredUI();
  }
}

function openPred(){
  document.getElementById('predOverlay').classList.add('on');
  loadPredictions();
}

function closePred(){document.getElementById('predOverlay').classList.remove('on');}
document.getElementById('predOverlay').addEventListener('click',function(e){if(e.target===this)closePred()});

function updatePredUI(){
  const total = votes.hold + votes.crack;
  const holdPct = total > 0 ? Math.round((votes.hold / total) * 100) : 50;
  const crackPct = 100 - holdPct;

  document.getElementById('totalVotes').textContent = total;
  document.getElementById('holdCount').textContent = votes.hold;
  document.getElementById('crackCount').textContent = votes.crack;
  document.getElementById('pctHold').textContent = holdPct + '%';
  document.getElementById('pctCrack').textContent = crackPct + '%';
  document.getElementById('pctHoldBig').textContent = holdPct + '%';
  document.getElementById('pctCrackBig').textContent = crackPct + '%';
  document.getElementById('predBarFill').style.width = holdPct + '%';
}

function vote(choice){
  if(hasVoted) return;

  // Send vote to backend
  fetch(`${API_URL}/api/predictions/vote?username=${user}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ choice: choice })
  })
  .then(res => res.json())
  .then(data => {
    hasVoted = true;
    votes.hold = data.hold_votes;
    votes.crack = data.crack_votes;

    localStorage.setItem('crackprotocol_vote', choice);

    document.getElementById('optHold').classList.toggle('selected', choice === 'hold');
    document.getElementById('optCrack').classList.toggle('selected', choice === 'crack');
    document.getElementById('optHold').classList.add('locked');
    document.getElementById('optCrack').classList.add('locked');

    document.getElementById('predVoted').classList.add('on');
    document.getElementById('votedChoice').textContent = choice === 'hold' ? 'AI Will Hold' : 'AI Will Be Cracked';

    updatePredUI();
  })
  .catch(err => {
    console.error('Vote failed:', err);
    // Fallback to localStorage for offline mode
    if(choice === 'hold') votes.hold++;
    else votes.crack++;
    
    hasVoted = true;
    localStorage.setItem('crackprotocol_vote', choice);
    
    document.getElementById('optHold').classList.toggle('selected', choice === 'hold');
    document.getElementById('optCrack').classList.toggle('selected', choice === 'crack');
    document.getElementById('optHold').classList.add('locked');
    document.getElementById('optCrack').classList.add('locked');
    document.getElementById('predVoted').classList.add('on');
    document.getElementById('votedChoice').textContent = choice === 'hold' ? 'AI Will Hold' : 'AI Will Be Cracked';
    updatePredUI();
  });
}

// Load vote state on page load
loadPredictions();
