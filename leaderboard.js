
const API_URL=window.location.hostname==='localhost'&&window.location.port===''?'http://localhost:8000':'';
const currentUser=localStorage.getItem('crackprotocol_user')||null;

async function loadStats(){
  try{
    const url=currentUser?`${API_URL}/api/stats?username=${currentUser}`:`${API_URL}/api/stats`;
    const res=await fetch(url);
    const data=await res.json();
    
    document.getElementById('totalUsers').textContent=data.total_users;
    document.getElementById('totalAttempts').textContent=data.total_attempts;
    // Successful cracks hidden
    document.getElementById('yourRank').textContent=data.your_rank||'N/A';
  }catch(err){
    console.error('Error loading stats:',err);
  }
}

async function loadLeaderboard(){
  try{
    const res=await fetch(`${API_URL}/api/leaderboard?limit=50`);
    const data=await res.json();
    
    const container=document.getElementById('leaderboard');
    container.innerHTML='';
    
    if(data.length===0){
      container.innerHTML='<div class="loading">No data yet. Be the first!</div>';
      return;
    }
    
    data.forEach(entry=>{
      const row=document.createElement('div');
      row.className='board-row';
      
      if(currentUser&&entry.username.toLowerCase()===currentUser.toLowerCase()){
        row.classList.add('highlight');
      }
      
      const rankClass=entry.rank===1?'top1':entry.rank===2?'top2':entry.rank===3?'top3':'';
      
      row.innerHTML=`
        <div class="rank ${rankClass}">#${entry.rank}</div>
        <div class="username">${entry.username}</div>
        <div class="attempts">${entry.attempts_count} attempts</div>
      `;
      
      container.appendChild(row);
    });
  }catch(err){
    console.error('Error loading leaderboard:',err);
    document.getElementById('leaderboard').innerHTML='<div class="loading">Error loading data. Make sure backend is running.</div>';
  }
}

window.addEventListener('DOMContentLoaded',()=>{
  loadStats();
  loadLeaderboard();
  

  setInterval(()=>{
    loadStats();
    loadLeaderboard();
  },30000);
});
