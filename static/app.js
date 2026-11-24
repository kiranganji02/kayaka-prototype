const $ = (s) => document.querySelector(s);
const toast = (msg) => { const t=$("#toast"); t.textContent=msg; t.classList.add("show"); setTimeout(()=>t.classList.remove("show"),2600); };
const workerForm=$("#workerForm"), jobForm=$("#jobForm"), matches=$("#matches");
function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
$("#voiceBtn").addEventListener("click",()=>{
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR){toast("Voice input is not supported in this browser. Please type your skill.");return;}
  const rec=new SR(); rec.lang="kn-IN"; rec.interimResults=false; rec.onstart=()=>toast("Listening… speak your skill");
  rec.onresult=e=>{$("#skill").value=e.results[0][0].transcript;toast("Skill captured. Please check the text.");};
  rec.onerror=()=>toast("Could not capture speech. Please try typing."); rec.start();
});
workerForm.addEventListener("submit",async e=>{
  e.preventDefault(); const data=new FormData(workerForm);
  try{
    const r=await fetch("/api/workers",{method:"POST",body:data}); const w=await r.json();
    const mr=await fetch(`/api/matches/${w.id}`); const jobs=await mr.json();
    $("#resultCaption").textContent=`Top opportunities for ${w.name} · ${w.area}`;
    if(!jobs.length){matches.className="matches empty";matches.innerHTML='<div class="empty-icon">⌕</div><b>No close matches yet.</b><span>Try a broader skill or distance.</span>';return;}
    matches.className="matches";matches.innerHTML=jobs.map(j=>`<article class="job-card"><div><h4>${escapeHtml(j.title)}</h4><p>${escapeHtml(j.employer)} · ${escapeHtml(j.area)}</p></div><span class="score">${Math.round(j.match_score*100)}% match</span><div class="job-meta"><span>⌖ ${j.distance} km away · ${escapeHtml(j.duration)}</span><span class="wage">₹${j.wage}/day</span></div></article>`).join("");
    toast("Your profile is ready. Matches found!");
  }catch(err){toast("Could not connect to the demo server.");}
});
jobForm.addEventListener("submit",async e=>{
  e.preventDefault();try{const r=await fetch("/api/jobs",{method:"POST",body:new FormData(jobForm)});if(!r.ok)throw new Error();jobForm.reset();toast("Demo job published successfully.");}catch(err){toast("Could not publish job. Is the server running?");}
});
