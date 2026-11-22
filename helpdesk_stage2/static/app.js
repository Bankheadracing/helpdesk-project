const $ = (id) => document.getElementById(id);
let tickets = [];
function textNode(tag, value, className = '') { const el = document.createElement(tag); if(className) el.className = className; el.textContent = String(value ?? ''); return el; }
async function loadTickets(){
  try {
    const r=await fetch('/api/tickets'); if(!r.ok) throw new Error('Failed to load tickets');
    tickets=(await r.json()).tickets;
    $('total').textContent=tickets.length;
    $('auto').textContent=tickets.filter(t=>t.status==='Auto-routed').length;
    $('review').textContent=tickets.filter(t=>t.status!=='Auto-routed').length;
    $('critical').textContent=tickets.filter(t=>t.priority.startsWith('P1')).length;
    renderTickets();
  } catch(err){ $('form-error').hidden=false; $('form-error').textContent=err.message; }
}
function renderTickets(){
 const tbody=$('ticket-list'); tbody.replaceChildren();
 const filtered=tickets.filter(t=>$('filter').value==='all'||t.status===$('filter').value);
 if(!filtered.length){ const tr=document.createElement('tr');const td=textNode('td','No matching tickets yet.','no-tickets');td.colSpan=6;tr.append(td);tbody.append(tr);return; }
 for(const t of filtered){
  const tr=document.createElement('tr');
  for (const value of [t.ticket_id,t.subject,t.category,t.priority,t.assigned_team]) tr.append(textNode('td',value));
  tr.append(textNode('td',t.status,t.status==='Auto-routed'?'status-auto':'status-review'));
  tbody.append(tr);
 }
}
function showResult(t){
 $('empty-result').hidden=true;$('result').hidden=false;
 $('result-id').textContent=t.ticket_id;
 $('result-status').textContent=t.status;
 $('result-status').className='status-pill '+(t.status==='Auto-routed'?'good':'warn');
 for(const [k,v] of [['subject',t.subject],['category',t.category],['priority',t.priority],['team',t.assigned_team],['reason',t.reason]]) $('result-'+k).textContent=v;
}
$('filter').addEventListener('change',renderTickets);
$('refresh').addEventListener('click',loadTickets);
$('ticket-form').addEventListener('submit',async(e)=>{
 e.preventDefault();$('form-error').hidden=true;const button=$('submit-button');button.disabled=true;button.textContent='Processing…';
 const form=new FormData(e.currentTarget);
 const payload=Object.fromEntries(form.entries());
 try{
   const response=await fetch('/api/tickets',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
   const body=await response.json(); if(!response.ok) throw new Error(body.error||'Request failed');
   showResult(body);e.currentTarget.reset();await loadTickets();
 }catch(err){$('form-error').hidden=false;$('form-error').textContent=err.message;}
 finally{button.disabled=false;button.innerHTML='Run automation <span>→</span>';}
});
loadTickets();
