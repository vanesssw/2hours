// Главная страница CRACK PROTOCOL - логика регистрации и навигации

function copyCA(){
  const caSpan = document.querySelector('.chip-val[data-ca]');
  const fullCA = caSpan.getAttribute('data-ca');
  navigator.clipboard.writeText(fullCA).then(()=>{
    const t=document.getElementById('toast');
    t.classList.add('show');
    setTimeout(()=>t.classList.remove('show'),1500)
  })
}

function openM(){
  document.getElementById('modal').classList.add('on');
  setTimeout(()=>document.getElementById('uInput').focus(),200)
}

function closeM(){
  document.getElementById('modal').classList.remove('on')
}

document.getElementById('uInput').addEventListener('input',function(){
  document.getElementById('goBtn').disabled=this.value.trim().length<2
});

document.getElementById('uInput').addEventListener('keydown',function(e){
  if(e.key==='Enter'&&this.value.trim().length>=2)go()
});

// API URL работает с Docker (через nginx proxy) и локально
const API_URL=window.location.hostname==='localhost'&&window.location.port===''?'http://localhost:8000':'';

async function go(){
  const u=document.getElementById('uInput').value.trim();
  if(u.length<2)return;
  
  const btn=document.getElementById('goBtn');
  btn.disabled=true;
  btn.textContent='Connecting...';
  
  try{
    // Регистрация через API
    const res=await fetch(`${API_URL}/api/auth/register`,{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({username:u})
    });
    
    if(!res.ok){
      const err=await res.json();
      if(err.detail==='Username already exists'){
        // Пользователь уже существует, просто продолжаем
        localStorage.setItem('crackprotocol_user',u);
        window.location.href='terminal';
      }else{
        throw new Error(err.detail||'Registration failed');
      }
    }else{
      // Успешная регистрация
      localStorage.setItem('crackprotocol_user',u);
      window.location.href='terminal';
    }
  }catch(err){
    console.error('Error:',err);
    // Откат на локальное хранение если API недоступен
    localStorage.setItem('crackprotocol_user',u);
    window.location.href='terminal';
  }
}

document.getElementById('modal').addEventListener('click',function(e){
  if(e.target===this)closeM()
});
