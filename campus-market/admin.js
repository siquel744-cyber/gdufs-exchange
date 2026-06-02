async function apiGet(path){
  const r = await fetch(path);
  return r.json();
}
async function apiPost(path, body){
  const r = await fetch(path, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
  return r.json();
}
async function apiDelete(path){
  const r = await fetch(path, {method:'DELETE'});
  return r.json();
}

function el(tag, inner){ const d = document.createElement(tag); if(inner!==undefined) d.innerHTML = inner; return d; }

async function loadUsers(){
  const box = document.getElementById('usersList');
  box.innerHTML = '加载中...';
  const users = await apiGet('/api/admin/users');
  if(users.error){ box.innerHTML = '无法加载：'+users.error; return; }
  const table = document.createElement('table');
  table.style.width='100%';
  table.innerHTML = '<tr><th>学号</th><th>管理员</th><th>封禁</th><th>注册时间</th><th>操作</th></tr>';
  users.forEach(u=>{
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${u.username}</td><td>${u.is_admin?'<strong>是</strong>':'否'}</td><td>${u.is_banned?'<strong>是</strong>':'否'}</td><td>${u.created_at||''}</td>`;
    const ops = document.createElement('td');
    const btnAdmin = document.createElement('button'); btnAdmin.className='secondary-button small'; btnAdmin.textContent = u.is_admin? '取消管理员' : '设为管理员';
    btnAdmin.addEventListener('click', async ()=>{
      await apiPost(`/api/admin/users/${u.id}/set_admin`, {is_admin: u.is_admin?0:1});
      await loadUsers();
    });
    const btnBan = document.createElement('button'); btnBan.className='secondary-button small'; btnBan.style.marginLeft='8px'; btnBan.textContent = u.is_banned? '解封' : '封禁';
    btnBan.addEventListener('click', async ()=>{
      if(!u.is_banned && !confirm('确定要封禁该用户吗？')) return;
      await apiPost(`/api/admin/users/${u.id}/set_ban`, {is_banned: u.is_banned?0:1});
      await loadUsers();
    });
    ops.appendChild(btnAdmin); ops.appendChild(btnBan);
    tr.appendChild(ops);
    table.appendChild(tr);
  });
  box.innerHTML=''; box.appendChild(table);
}

async function loadProducts(){
  const box = document.getElementById('productsList');
  box.innerHTML = '加载中...';
  const items = await apiGet('/api/admin/products');
  if(items.error){ box.innerHTML = '无法加载：'+items.error; return; }
  const table = document.createElement('table'); table.style.width='100%';
  table.innerHTML = '<tr><th>ID</th><th>标题</th><th>卖家</th><th>价格</th><th>状态</th><th>发布时间</th><th>操作</th></tr>';
  items.forEach(p=>{
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${p.id}</td><td>${p.title}</td><td>${p.seller}</td><td>¥${p.price}</td><td>${p.sold? '已售出':'在售'}</td><td>${p.created_at}</td>`;
    const ops = document.createElement('td');
    const btnSold = document.createElement('button'); btnSold.className='secondary-button small'; btnSold.textContent='强制下架';
    btnSold.addEventListener('click', async ()=>{
      if(!confirm('确定将此商品标记为已售出（强制下架）吗？')) return;
      await apiPost(`/api/admin/products/${p.id}/force_sold`, {});
      await loadProducts();
    });
    const btnDel = document.createElement('button'); btnDel.className='secondary-button small'; btnDel.style.marginLeft='8px'; btnDel.textContent='删除';
    btnDel.addEventListener('click', async ()=>{
      if(!confirm('确定删除此商品？该操作不可恢复。')) return;
      await apiDelete(`/api/admin/products/${p.id}`);
      await loadProducts();
    });
    ops.appendChild(btnSold); ops.appendChild(btnDel);
    tr.appendChild(ops);
    table.appendChild(tr);
  });
  box.innerHTML=''; box.appendChild(table);
}

async function loadReports(){
  const box = document.getElementById('reportsList');
  box.innerHTML = '加载中...';
  const reps = await apiGet('/api/admin/reports');
  if(reps.error){ box.innerHTML = '无法加载：'+reps.error; return; }
  if(!reps.length){ box.innerHTML = '暂无举报。'; return; }
  const table = document.createElement('table'); table.style.width='100%';
  table.innerHTML = '<tr><th>ID</th><th>类型</th><th>目标ID</th><th>理由</th><th>时间</th><th>操作</th></tr>';
  reps.forEach(r=>{
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${r.id}</td><td>${r.type||''}</td><td>${r.target_id||''}</td><td>${r.reason||''}</td><td>${r.created_at||''}</td>`;
    const ops = document.createElement('td');
    const btnHandle = document.createElement('button'); btnHandle.className='secondary-button small'; btnHandle.textContent='标记已处理';
    btnHandle.addEventListener('click', async ()=>{ await apiPost(`/api/admin/reports/${r.id}/resolve`, {}); await loadReports(); });
    const btnDel = document.createElement('button'); btnDel.className='secondary-button small'; btnDel.style.marginLeft='8px'; btnDel.textContent='删除举报';
    btnDel.addEventListener('click', async ()=>{ if(!confirm('确定删除该举报？')) return; await apiDelete(`/api/admin/reports/${r.id}`); await loadReports(); });
    ops.appendChild(btnHandle); ops.appendChild(btnDel);
    tr.appendChild(ops);
    table.appendChild(tr);
  });
  box.innerHTML=''; box.appendChild(table);
}

window.addEventListener('DOMContentLoaded', ()=>{
  document.getElementById('tabUsers').addEventListener('click', ()=>{ document.getElementById('panelUsers').classList.remove('hidden'); document.getElementById('panelProducts').classList.add('hidden'); document.getElementById('panelReports').classList.add('hidden'); });
  document.getElementById('tabProducts').addEventListener('click', ()=>{ document.getElementById('panelUsers').classList.add('hidden'); document.getElementById('panelProducts').classList.remove('hidden'); document.getElementById('panelReports').classList.add('hidden'); });
  document.getElementById('tabReports').addEventListener('click', ()=>{ document.getElementById('panelUsers').classList.add('hidden'); document.getElementById('panelProducts').classList.add('hidden'); document.getElementById('panelReports').classList.remove('hidden'); });
  loadUsers(); loadProducts(); loadReports();
});
