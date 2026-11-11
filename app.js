'use strict';
/* Buku Kedai — rekod belian, jualan, untung rugi.
 * Semua data disimpan dalam IndexedDB pada peranti pengguna. */

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];

const BULAN = ['Januari', 'Februari', 'Mac', 'April', 'Mei', 'Jun', 'Julai', 'Ogos', 'September', 'Oktober', 'November', 'Disember'];
const BULAN_PENDEK = ['Jan', 'Feb', 'Mac', 'Apr', 'Mei', 'Jun', 'Jul', 'Ogos', 'Sep', 'Okt', 'Nov', 'Dis'];
const LABEL = { sales: 'Jualan', purchases: 'Belian' };
const TYPES = ['sales', 'purchases'];

const pad = n => String(n).padStart(2, '0');
const round2 = n => Math.round((Number(n) + Number.EPSILON) * 100) / 100;
const num = n => (Number(n) || 0).toLocaleString('en-MY', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const fmt = n => (n < 0 ? '-RM ' : 'RM ') + num(Math.abs(n));
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const uid = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
const today = () => { const d = new Date(); return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`; };
const thisMonth = () => today().slice(0, 7);
const fmtDate = d => `${d.slice(8, 10)}/${d.slice(5, 7)}/${d.slice(0, 4)}`;
const monthName = ym => `${BULAN[+ym.slice(5, 7) - 1]} ${ym.slice(0, 4)}`;
const periodLabel = p => (p.length === 4 ? `Tahun ${p}` : monthName(p));
const sumTotal = arr => round2(arr.reduce((a, r) => a + (Number(r.total) || 0), 0));

/* ---------- Sokongan pelayar lama ---------- */
// Pelayar lama (cth iOS < 15.4) tiada <dialog>.showModal — guna gantian ringkas.
for (const d of document.querySelectorAll('dialog')) {
  if (typeof d.showModal !== 'function') {
    d.classList.add('dlg-fallback');
    d.showModal = () => { d.setAttribute('open', ''); document.body.classList.add('modal-open'); };
    d.close = () => {
      d.removeAttribute('open');
      if (!document.querySelector('dialog[open]')) document.body.classList.remove('modal-open');
    };
  }
}
// Papar ralat kepada pengguna supaya masalah mudah dikenal pasti.
window.addEventListener('error', e => toast('Ralat: ' + (e.message || 'tidak diketahui')));
window.addEventListener('unhandledrejection', e => toast('Ralat: ' + ((e.reason && e.reason.message) || e.reason || 'tidak diketahui')));

/* ---------- IndexedDB ---------- */
let db;
const data = { sales: [], purchases: [] };
let bizName = '';

function openDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open('buku-kedai', 1);
    req.onupgradeneeded = () => {
      const d = req.result;
      for (const s of TYPES) if (!d.objectStoreNames.contains(s)) d.createObjectStore(s, { keyPath: 'id' });
      if (!d.objectStoreNames.contains('meta')) d.createObjectStore('meta', { keyPath: 'key' });
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}
function tx(store, mode, fn) {
  return new Promise((resolve, reject) => {
    const t = db.transaction(store, mode);
    const req = fn(t.objectStore(store));
    t.oncomplete = () => resolve(req && req.result);
    t.onerror = () => reject(t.error);
    t.onabort = () => reject(t.error);
  });
}
const getAll = s => tx(s, 'readonly', st => st.getAll());
const put = (s, v) => tx(s, 'readwrite', st => st.put(v));
const del = (s, id) => tx(s, 'readwrite', st => st.delete(id));
const clear = s => tx(s, 'readwrite', st => st.clear());

async function load() {
  for (const t of TYPES) {
    data[t] = await getAll(t);
    data[t].sort((a, b) => b.date.localeCompare(a.date) || (b.createdAt || 0) - (a.createdAt || 0));
  }
  const meta = await tx('meta', 'readonly', st => st.get('bizName'));
  bizName = meta ? meta.value : '';
}

/* ---------- Kiraan ---------- */
function totals(prefix) {
  const s = sumTotal(data.sales.filter(r => r.date.startsWith(prefix)));
  const b = sumTotal(data.purchases.filter(r => r.date.startsWith(prefix)));
  return { sales: s, purchases: b, profit: round2(s - b) };
}

/* ---------- Navigasi ---------- */
let activeTab = 'dashboard';
function showTab(name) {
  activeTab = name;
  $$('#tabs button').forEach(b => b.classList.toggle('active', b.dataset.tab === name));
  $$('.tab').forEach(s => s.classList.toggle('active', s.id === 'tab-' + name));
  render();
  window.scrollTo(0, 0);
}

function render() {
  $('#bizName').textContent = bizName || 'Buku Kedai';
  document.title = bizName ? `${bizName} — Buku Kedai` : 'Buku Kedai';
  if (activeTab === 'dashboard') renderDashboard();
  else if (activeTab === 'sales' || activeTab === 'purchases') renderList(activeTab);
  else if (activeTab === 'report') renderReport();
  else if (activeTab === 'settings') renderSettings();
}

/* ---------- Utama ---------- */
let chart;
function renderDashboard() {
  const mi = $('#dashMonth');
  if (!mi.value) mi.value = thisMonth();
  const m = mi.value;
  const t = totals(m);
  $('#statSales').textContent = fmt(t.sales);
  $('#statPurch').textContent = fmt(t.purchases);
  $('#statProfitLabel').textContent = t.profit >= 0 ? 'Untung' : 'Rugi';
  $('#statProfit').textContent = fmt(Math.abs(t.profit));
  const card = $('#statProfitCard');
  card.classList.toggle('pos', t.profit > 0);
  card.classList.toggle('neg', t.profit < 0);

  const y = m.slice(0, 4);
  $('#dashYear').textContent = y;
  drawChart(y);

  const recent = [
    ...data.sales.map(r => ['sales', r]),
    ...data.purchases.map(r => ['purchases', r]),
  ].sort((a, b) => b[1].date.localeCompare(a[1].date) || (b[1].createdAt || 0) - (a[1].createdAt || 0)).slice(0, 6);
  $('#recent').innerHTML = recent.length
    ? recent.map(([type, r]) => entryCard(type, r)).join('')
    : '<div class="empty">Belum ada rekod. Tekan “+ Rekod Jualan” atau “+ Rekod Belian” untuk mula.</div>';
}

function drawChart(y) {
  const ok = !!window.Chart;
  $('#chart').hidden = !ok;
  $('#chartFallback').hidden = ok;
  if (!ok) return;
  const ts = BULAN.map((_, i) => totals(`${y}-${pad(i + 1)}`));
  const css = getComputedStyle(document.documentElement);
  const v = n => css.getPropertyValue(n).trim();
  const cfg = {
    type: 'bar',
    data: {
      labels: BULAN_PENDEK,
      datasets: [
        { label: 'Jualan', data: ts.map(t => t.sales), backgroundColor: v('--c-sales'), borderRadius: 4, order: 2 },
        { label: 'Belian', data: ts.map(t => t.purchases), backgroundColor: v('--c-purch'), borderRadius: 4, order: 3 },
        { label: 'Untung/Rugi', type: 'line', data: ts.map(t => t.profit), borderColor: v('--c-profit'),
          backgroundColor: v('--c-profit'), cubicInterpolationMode: 'monotone', pointRadius: 3, borderWidth: 2, order: 1 },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false, animation: { duration: 300 },
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { labels: { color: v('--text'), usePointStyle: true, boxWidth: 8 } },
        tooltip: { callbacks: { label: c => `${c.dataset.label}: ${fmt(c.parsed.y)}` } },
      },
      scales: {
        x: { ticks: { color: v('--muted'), maxRotation: 0, autoSkip: true }, grid: { display: false } },
        y: { ticks: { color: v('--muted'), callback: n => 'RM' + Number(n).toLocaleString('en-MY') }, grid: { color: v('--border') } },
      },
    },
  };
  if (chart) chart.destroy();
  chart = new Chart($('#chart'), cfg);
}

/* ---------- Senarai ---------- */
const listState = { sales: { month: thisMonth(), q: '' }, purchases: { month: thisMonth(), q: '' } };

function renderList(type) {
  const sec = $('#tab-' + type);
  const st = listState[type];
  $('.f-month', sec).value = st.month;
  let rows = data[type].filter(r => !st.month || r.date.startsWith(st.month));
  if (st.q) {
    const q = st.q.toLowerCase();
    rows = rows.filter(r => [r.party, r.note, ...r.items.map(i => i.name)].join(' ').toLowerCase().includes(q));
  }
  $('.list-total', sec).innerHTML =
    `${rows.length} rekod · Jumlah <strong>${fmt(sumTotal(rows))}</strong> · ${st.month ? esc(monthName(st.month)) : 'Semua bulan'}`;
  $('.list', sec).innerHTML = rows.length
    ? rows.map(r => entryCard(type, r)).join('')
    : `<div class="empty">Tiada rekod ${LABEL[type].toLowerCase()} untuk tempoh ini.</div>`;
}

function entryCard(type, r) {
  const items = r.items.map(i => `${esc(i.name)} × ${esc(i.qty)}`).join(', ');
  const thumb = r.receipt
    ? `<img class="thumb" src="${esc(r.receipt)}" alt="Resit" data-view loading="lazy">`
    : `<div class="thumb ph" aria-hidden="true">${type === 'sales' ? '💰' : '🧾'}</div>`;
  return `<article class="entry" data-type="${type}" data-id="${esc(r.id)}">
    ${thumb}
    <div class="e-main">
      <div class="e-top"><strong>${esc(r.party || LABEL[type])}</strong><span class="amt ${type}">${type === 'purchases' ? '−' : '+'}${fmt(r.total)}</span></div>
      <div class="e-sub">${LABEL[type]} · ${fmtDate(r.date)}${r.payment ? ' · ' + esc(r.payment) : ''}</div>
      <div class="e-items">${items}</div>
      ${r.note ? `<div class="e-note">${esc(r.note)}</div>` : ''}
    </div>
    <div class="e-act">
      <button class="icon" data-edit title="Edit" aria-label="Edit">✏️</button>
      <button class="icon" data-del title="Padam" aria-label="Padam">🗑️</button>
    </div>
  </article>`;
}

/* ---------- Borang ---------- */
let editing = null;
let receiptData = null;

function openForm(type, rec) {
  editing = { type, id: rec?.id || null, createdAt: rec?.createdAt };
  const f = $('#entryForm');
  f.reset();
  $('#dlgTitle').textContent = (rec ? 'Edit ' : 'Tambah ') + LABEL[type];
  $('#partyLabel').textContent = type === 'sales' ? 'Pelanggan' : 'Pembekal / Kedai';
  $('#receiptLabel').textContent = type === 'purchases' ? '📷 Upload / ambil gambar resit' : '📷 Lampir gambar (pilihan)';
  f.date.value = rec?.date || today();
  f.party.value = rec?.party || '';
  f.note.value = rec?.note || '';
  f.payment.value = rec?.payment || 'Tunai';
  receiptData = rec?.receipt || null;
  showReceipt();
  $('#itemRows').innerHTML = '';
  (rec?.items?.length ? rec.items : [{ name: '', qty: 1, price: '' }]).forEach(addRow);
  fillDatalists(type);
  calc();
  $('#entryDlg').showModal();
  if (!rec) setTimeout(() => $('.i-name')?.focus(), 50);
}

function addRow(it = { name: '', qty: 1, price: '' }) {
  const d = document.createElement('div');
  d.className = 'item-row';
  d.innerHTML = `<input class="i-name" placeholder="Nama barang" list="itemList" value="${esc(it.name)}" aria-label="Nama barang" autocomplete="off">
    <input class="i-qty" type="number" inputmode="decimal" min="0" step="any" value="${esc(it.qty)}" placeholder="Kuantiti" aria-label="Kuantiti">
    <input class="i-price" type="number" inputmode="decimal" min="0" step="any" value="${esc(it.price)}" placeholder="Harga RM" aria-label="Harga seunit (RM)">
    <span class="i-sub">0.00</span>
    <button type="button" class="icon i-del" title="Buang barang" aria-label="Buang barang">✕</button>`;
  $('#itemRows').append(d);
  return d;
}

function readItems() {
  return $$('#itemRows .item-row').map(r => {
    const qty = Number($('.i-qty', r).value) || 0;
    const price = Number($('.i-price', r).value) || 0;
    return { name: $('.i-name', r).value.trim(), qty, price, subtotal: round2(qty * price) };
  });
}

function calc() {
  let total = 0;
  $$('#itemRows .item-row').forEach(r => {
    const s = round2((Number($('.i-qty', r).value) || 0) * (Number($('.i-price', r).value) || 0));
    $('.i-sub', r).textContent = num(s);
    total += s;
  });
  $('#grandTotal').textContent = fmt(round2(total));
}

function fillDatalists(type) {
  const names = new Map();
  const parties = new Set();
  // data disusun terbaru dahulu, jadi harga pertama yang dijumpai ialah harga terkini
  for (const r of data[type]) {
    if (r.party) parties.add(r.party);
    for (const i of r.items) if (i.name && !names.has(i.name)) names.set(i.name, i.price);
  }
  lastPrice = names;
  $('#itemList').innerHTML = [...names.keys()].map(n => `<option value="${esc(n)}">`).join('');
  $('#partyList').innerHTML = [...parties].map(n => `<option value="${esc(n)}">`).join('');
}
let lastPrice = new Map();

$('#itemRows').addEventListener('input', e => {
  if (e.target.classList.contains('i-name')) {
    const row = e.target.closest('.item-row');
    const price = $('.i-price', row);
    if (!price.value && lastPrice.has(e.target.value)) price.value = lastPrice.get(e.target.value);
  }
  calc();
});
$('#itemRows').addEventListener('click', e => {
  if (!e.target.closest('.i-del')) return;
  const rows = $$('#itemRows .item-row');
  if (rows.length > 1) e.target.closest('.item-row').remove();
  else rows[0].querySelectorAll('input').forEach(i => (i.value = i.classList.contains('i-qty') ? 1 : ''));
  calc();
});
$('#addItem').addEventListener('click', () => { $('.i-name', addRow()).focus(); });

$('#entryForm').addEventListener('submit', async e => {
  e.preventDefault();
  const f = e.target;
  if (!f.date.value) return toast('Sila pilih tarikh');
  const items = readItems().filter(i => i.name || i.price);
  items.forEach(i => { if (!i.name) i.name = LABEL[editing.type]; });
  if (!items.length) return toast('Sila masukkan sekurang-kurangnya satu barang');
  const rec = {
    id: editing.id || uid(),
    date: f.date.value,
    party: f.party.value.trim(),
    payment: f.payment.value,
    note: f.note.value.trim(),
    items,
    total: round2(items.reduce((a, i) => a + i.subtotal, 0)),
    receipt: receiptData,
    createdAt: editing.createdAt || Date.now(),
    updatedAt: Date.now(),
  };
  try {
    await put(editing.type, rec);
  } catch (err) {
    console.error(err);
    return toast('Gagal simpan. Ruang storan mungkin penuh.');
  }
  await load();
  $('#entryDlg').close();
  render();
  toast(`${LABEL[editing.type]} disimpan ✔`);
});

/* ---------- Gambar resit ---------- */
function compressImage(file, max = 1600, quality = 0.72) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      const s = Math.min(1, max / Math.max(img.naturalWidth, img.naturalHeight));
      const w = Math.round(img.naturalWidth * s), h = Math.round(img.naturalHeight * s);
      const c = document.createElement('canvas');
      c.width = w; c.height = h;
      const ctx = c.getContext('2d');
      ctx.fillStyle = '#fff';
      ctx.fillRect(0, 0, w, h);
      ctx.drawImage(img, 0, 0, w, h);
      URL.revokeObjectURL(url);
      resolve(c.toDataURL('image/jpeg', quality));
    };
    img.onerror = () => { URL.revokeObjectURL(url); reject(new Error('bad image')); };
    img.src = url;
  });
}
function showReceipt() {
  $('#receiptPreview').innerHTML = receiptData
    ? `<img src="${esc(receiptData)}" alt="Gambar resit" data-viewsrc><button type="button" class="btn small" id="rmReceipt">Buang gambar</button>`
    : '';
}
$('#receiptInput').addEventListener('change', async e => {
  const file = e.target.files[0];
  e.target.value = '';
  if (!file) return;
  try { receiptData = await compressImage(file); showReceipt(); }
  catch { toast('Gambar tidak dapat dibaca. Cuba format JPG/PNG.'); }
});
function viewImg(src) {
  $('#imgFull').src = src;
  $('#imgDlg').showModal();
}

/* ---------- Laporan ---------- */
function repPeriod() {
  const mode = $('input[name=period]:checked').value;
  return mode === 'year' ? $('#repYear').value : ($('#repMonth').value || thisMonth());
}
function yearsAvailable() {
  const set = new Set([today().slice(0, 4)]);
  for (const t of TYPES) data[t].forEach(r => set.add(r.date.slice(0, 4)));
  return [...set].sort().reverse();
}

function buildReport(p) {
  const byDate = (a, b) => a.date.localeCompare(b.date) || (a.createdAt || 0) - (b.createdAt || 0);
  const sales = data.sales.filter(r => r.date.startsWith(p)).sort(byDate);
  const purchases = data.purchases.filter(r => r.date.startsWith(p)).sort(byDate);
  const t = totals(p);
  let breakdown;
  if (p.length === 4) {
    breakdown = BULAN.map((b, i) => ({ label: b, ...totals(`${p}-${pad(i + 1)}`) }));
  } else {
    const days = new Date(+p.slice(0, 4), +p.slice(5, 7), 0).getDate();
    breakdown = [];
    for (let d = 1; d <= days; d++) {
      const k = `${p}-${pad(d)}`;
      const x = totals(k);
      if (x.sales || x.purchases) breakdown.push({ label: fmtDate(k), ...x });
    }
  }
  const prod = new Map();
  for (const r of sales) for (const i of r.items) {
    const key = i.name.trim().toLowerCase();
    const o = prod.get(key) || { name: i.name.trim(), qty: 0, amount: 0 };
    o.qty += Number(i.qty) || 0;
    o.amount = round2(o.amount + (i.subtotal ?? i.qty * i.price));
    prod.set(key, o);
  }
  const products = [...prod.values()].sort((a, b) => b.amount - a.amount);
  return {
    p, label: periodLabel(p), sales, purchases, t, breakdown, products,
    margin: t.sales ? round2((t.profit / t.sales) * 100) : null,
  };
}

function renderReport() {
  const ys = yearsAvailable();
  const sel = $('#repYear');
  const cur = sel.value || ys[0];
  sel.innerHTML = ys.map(y => `<option${y === cur ? ' selected' : ''}>${y}</option>`).join('');
  if (!$('#repMonth').value) $('#repMonth').value = thisMonth();
  const isYear = $('input[name=period]:checked').value === 'year';
  sel.hidden = !isYear;
  $('#repMonth').hidden = isYear;

  const R = buildReport(repPeriod());
  const pl = R.t.profit;
  $('#repSummary').innerHTML = `
    <div class="card stat sales"><span>Jualan · ${esc(R.label)}</span><strong>${fmt(R.t.sales)}</strong></div>
    <div class="card stat purchases"><span>Belian · ${esc(R.label)}</span><strong>${fmt(R.t.purchases)}</strong></div>
    <div class="card stat profit ${pl > 0 ? 'pos' : pl < 0 ? 'neg' : ''}"><span>${pl >= 0 ? 'Untung' : 'Rugi'} bersih${R.margin != null ? ` · margin ${R.margin}%` : ''}</span><strong>${fmt(Math.abs(pl))}</strong></div>`;

  $('#repTableTitle').textContent = isYear ? `Pecahan bulanan ${R.p}` : `Pecahan harian ${R.label}`;
  const cls = n => (n > 0 ? 'pos' : n < 0 ? 'neg' : '');
  $('#repTable').innerHTML = R.breakdown.length ? `<table>
    <thead><tr><th>${isYear ? 'Bulan' : 'Tarikh'}</th><th>Jualan</th><th>Belian</th><th>Untung/Rugi</th></tr></thead>
    <tbody>${R.breakdown.map(b => `<tr><td>${esc(b.label)}</td><td>${num(b.sales)}</td><td>${num(b.purchases)}</td><td class="${cls(b.profit)}">${fmt(b.profit)}</td></tr>`).join('')}</tbody>
    <tfoot><tr><td>Jumlah</td><td>${num(R.t.sales)}</td><td>${num(R.t.purchases)}</td><td class="${cls(pl)}">${fmt(pl)}</td></tr></tfoot>
  </table>` : '<div class="empty">Tiada transaksi untuk tempoh ini.</div>';

  $('#repProducts').innerHTML = R.products.length ? `<table>
    <thead><tr><th>Barang</th><th>Kuantiti</th><th>Jumlah jualan</th></tr></thead>
    <tbody>${R.products.slice(0, 15).map(x => `<tr><td>${esc(x.name)}</td><td>${esc(x.qty)}</td><td>${fmt(x.amount)}</td></tr>`).join('')}</tbody>
  </table>` : '<div class="empty">Tiada jualan untuk tempoh ini.</div>';
}

const fileSlug = () => (bizName || 'Buku_Kedai').replace(/[^\w-]+/g, '_').replace(/^_+|_+$/g, '') || 'Buku_Kedai';

function exportXlsx() {
  if (!window.XLSX) return toast('Pustaka Excel gagal dimuatkan. Semak sambungan internet.');
  const R = buildReport(repPeriod());
  const isYear = R.p.length === 4;
  const wb = XLSX.utils.book_new();

  const moneyCols = (ws, cols, fromRow = 0) => {
    const range = XLSX.utils.decode_range(ws['!ref']);
    for (let r = fromRow; r <= range.e.r; r++) for (const c of cols) {
      const cell = ws[XLSX.utils.encode_cell({ r, c })];
      if (cell && cell.t === 'n') cell.z = '#,##0.00';
    }
  };

  const summary = [
    [bizName || 'Laporan Perniagaan'],
    [`Laporan Untung Rugi — ${R.label}`],
    [`Dijana pada ${fmtDate(today())}`],
    [],
    ['Perkara', 'Jumlah (RM)'],
    ['Jumlah Jualan', R.t.sales],
    ['Jumlah Belian', R.t.purchases],
    [R.t.profit >= 0 ? 'Untung Bersih' : 'Rugi Bersih', R.t.profit],
    ['Margin Untung (%)', R.margin ?? '-'],
    ['Bilangan Transaksi Jualan', R.sales.length],
    ['Bilangan Transaksi Belian', R.purchases.length],
    [],
    [isYear ? 'Bulan' : 'Tarikh', 'Jualan (RM)', 'Belian (RM)', 'Untung/Rugi (RM)'],
    ...R.breakdown.map(b => [b.label, b.sales, b.purchases, b.profit]),
    ['JUMLAH', R.t.sales, R.t.purchases, R.t.profit],
  ];
  const ws1 = XLSX.utils.aoa_to_sheet(summary);
  ws1['!cols'] = [{ wch: 28 }, { wch: 16 }, { wch: 16 }, { wch: 18 }];
  moneyCols(ws1, [1, 2, 3], 5);
  for (const r of [8, 9, 10]) { const c = ws1['B' + (r + 1)]; if (c) delete c.z; }
  XLSX.utils.book_append_sheet(wb, ws1, 'Ringkasan');

  const detail = (type, partyLabel) => {
    const rows = [['Tarikh', partyLabel, 'Barang', 'Kuantiti', 'Harga Seunit (RM)', 'Jumlah (RM)', 'Cara Bayaran', 'Catatan', 'Ada Resit']];
    for (const r of R[type]) r.items.forEach((i, ix) => rows.push([
      fmtDate(r.date), r.party, i.name, i.qty, i.price, i.subtotal ?? round2(i.qty * i.price),
      r.payment || '', ix === 0 ? r.note : '', ix === 0 ? (r.receipt ? 'Ya' : 'Tidak') : '',
    ]));
    rows.push([], ['', '', '', '', 'JUMLAH', R.t[type]]);
    const ws = XLSX.utils.aoa_to_sheet(rows);
    ws['!cols'] = [{ wch: 12 }, { wch: 20 }, { wch: 28 }, { wch: 9 }, { wch: 16 }, { wch: 14 }, { wch: 14 }, { wch: 24 }, { wch: 10 }];
    moneyCols(ws, [4, 5], 1);
    return ws;
  };
  XLSX.utils.book_append_sheet(wb, detail('sales', 'Pelanggan'), 'Jualan');
  XLSX.utils.book_append_sheet(wb, detail('purchases', 'Pembekal'), 'Belian');

  const ws4 = XLSX.utils.aoa_to_sheet([['Barang', 'Kuantiti Terjual', 'Jumlah Jualan (RM)'], ...R.products.map(x => [x.name, x.qty, x.amount])]);
  ws4['!cols'] = [{ wch: 30 }, { wch: 16 }, { wch: 18 }];
  moneyCols(ws4, [2], 1);
  XLSX.utils.book_append_sheet(wb, ws4, 'Barang Laris');

  XLSX.writeFile(wb, `Laporan_${fileSlug()}_${R.p}.xlsx`);
  toast('Fail Excel dimuat turun ✔');
}

function imageSize(src) {
  return new Promise(resolve => {
    const img = new Image();
    img.onload = () => resolve({ w: img.naturalWidth, h: img.naturalHeight });
    img.onerror = () => resolve(null);
    img.src = src;
  });
}

async function exportPdf() {
  if (!window.jspdf) return toast('Pustaka PDF gagal dimuatkan. Semak sambungan internet.');
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF({ unit: 'mm', format: 'a4' });
  if (typeof doc.autoTable !== 'function') return toast('Pustaka jadual PDF gagal dimuatkan.');
  const R = buildReport(repPeriod());
  const isYear = R.p.length === 4;
  const W = doc.internal.pageSize.getWidth();
  const H = doc.internal.pageSize.getHeight();
  const M = 14;
  const BRAND = [15, 118, 110], AMBER = [180, 83, 9], GREEN = [21, 128, 61], RED = [220, 38, 38];
  const plText = n => (n < 0 ? '-' : '') + num(Math.abs(n));

  // Kepala
  doc.setFillColor(...BRAND);
  doc.rect(0, 0, W, 30, 'F');
  doc.setTextColor(255);
  doc.setFont('helvetica', 'bold'); doc.setFontSize(17);
  doc.text(bizName || 'Laporan Perniagaan', M, 13);
  doc.setFont('helvetica', 'normal'); doc.setFontSize(11);
  doc.text(`Laporan Untung Rugi - ${R.label}`, M, 21);
  doc.setFontSize(9);
  doc.text(`Dijana: ${fmtDate(today())}`, W - M, 21, { align: 'right' });

  // Kotak ringkasan
  const pl = R.t.profit;
  const boxes = [
    ['Jumlah Jualan', fmt(R.t.sales), BRAND],
    ['Jumlah Belian', fmt(R.t.purchases), AMBER],
    [`${pl >= 0 ? 'Untung' : 'Rugi'} Bersih${R.margin != null ? ` (margin ${R.margin}%)` : ''}`, fmt(Math.abs(pl)), pl >= 0 ? GREEN : RED],
  ];
  const bw = (W - M * 2 - 8) / 3;
  boxes.forEach(([label, val, col], i) => {
    const x = M + i * (bw + 4);
    doc.setDrawColor(...col); doc.setLineWidth(0.7);
    doc.roundedRect(x, 36, bw, 22, 2, 2);
    doc.setFontSize(8.5); doc.setTextColor(90); doc.text(label, x + 4, 43);
    doc.setFont('helvetica', 'bold'); doc.setFontSize(14); doc.setTextColor(...col);
    doc.text(val, x + 4, 52.5);
    doc.setFont('helvetica', 'normal');
  });
  doc.setTextColor(20);

  const base = {
    theme: 'grid', margin: { left: M, right: M },
    styles: { fontSize: 9, cellPadding: 2 },
    headStyles: { fillColor: BRAND, textColor: 255 },
    footStyles: { fillColor: [235, 240, 240], textColor: 20, fontStyle: 'bold' },
  };
  let y = 66;
  const heading = text => {
    if (y > H - 40) { doc.addPage(); y = 20; }
    doc.setFont('helvetica', 'bold'); doc.setFontSize(12); doc.setTextColor(20);
    doc.text(text, M, y);
    doc.setFont('helvetica', 'normal');
    y += 3;
  };
  const after = () => { y = doc.lastAutoTable.finalY + 10; };

  heading(isYear ? `Pecahan Bulanan ${R.p}` : `Pecahan Harian ${R.label}`);
  doc.autoTable({
    ...base, startY: y,
    head: [[isYear ? 'Bulan' : 'Tarikh', 'Jualan (RM)', 'Belian (RM)', 'Untung/Rugi (RM)']],
    body: R.breakdown.length ? R.breakdown.map(b => [b.label, num(b.sales), num(b.purchases), plText(b.profit)]) : [['Tiada transaksi', '', '', '']],
    foot: [['JUMLAH', num(R.t.sales), num(R.t.purchases), plText(pl)]],
    columnStyles: { 1: { halign: 'right' }, 2: { halign: 'right' }, 3: { halign: 'right' } },
    didParseCell: d => {
      if (d.column.index > 0 && d.section !== 'body' ) d.cell.styles.halign = 'right';
      if (d.column.index === 3 && d.section === 'body' && R.breakdown[d.row.index]) {
        const v = R.breakdown[d.row.index].profit;
        if (v < 0) d.cell.styles.textColor = RED; else if (v > 0) d.cell.styles.textColor = GREEN;
      }
    },
  });
  after();

  const txTable = (type, title, partyLabel) => {
    heading(`${title} (${R[type].length} transaksi)`);
    doc.autoTable({
      ...base, startY: y,
      head: [['Tarikh', partyLabel, 'Barang', 'Bayaran', 'Jumlah (RM)']],
      body: R[type].length ? R[type].map(r => [
        fmtDate(r.date), r.party || '-',
        r.items.map(i => `${i.name} x${i.qty} @ ${num(i.price)}`).join('\n') + (r.note ? `\nCatatan: ${r.note}` : ''),
        r.payment || '-', num(r.total),
      ]) : [['-', 'Tiada rekod', '', '', '']],
      foot: [['', '', '', 'JUMLAH', num(R.t[type])]],
      columnStyles: { 0: { cellWidth: 22 }, 1: { cellWidth: 34 }, 3: { cellWidth: 24 }, 4: { halign: 'right', cellWidth: 26 } },
      headStyles: { ...base.headStyles, fillColor: type === 'sales' ? BRAND : AMBER },
      didParseCell: d => { if (d.column.index === 4) d.cell.styles.halign = 'right'; },
    });
    after();
  };
  txTable('sales', 'Senarai Jualan', 'Pelanggan');
  txTable('purchases', 'Senarai Belian', 'Pembekal');

  if (R.products.length) {
    heading('Barang Paling Laris');
    doc.autoTable({
      ...base, startY: y,
      head: [['#', 'Barang', 'Kuantiti', 'Jumlah Jualan (RM)']],
      body: R.products.map((x, i) => [i + 1, x.name, x.qty, num(x.amount)]),
      columnStyles: { 0: { cellWidth: 10 }, 2: { halign: 'right' }, 3: { halign: 'right' } },
    });
    after();
  }

  if ($('#repImages').checked) {
    const withImg = R.purchases.filter(r => r.receipt);
    for (const r of withImg) {
      const size = await imageSize(r.receipt);
      if (!size) continue;
      doc.addPage();
      doc.setFont('helvetica', 'bold'); doc.setFontSize(12); doc.setTextColor(20);
      doc.text(`Resit: ${r.party || 'Belian'} - ${fmtDate(r.date)} - ${fmt(r.total)}`, M, 18);
      doc.setFont('helvetica', 'normal');
      const maxW = W - M * 2, maxH = H - 40;
      const s = Math.min(maxW / size.w, maxH / size.h);
      const w = size.w * s, h = size.h * s;
      doc.addImage(r.receipt, 'JPEG', (W - w) / 2, 24, w, h);
    }
  }

  const pages = doc.getNumberOfPages();
  for (let i = 1; i <= pages; i++) {
    doc.setPage(i);
    doc.setFontSize(8); doc.setTextColor(130);
    doc.text(`${bizName || 'Buku Kedai'} - ${R.label}`, M, H - 8);
    doc.text(`Muka ${i} / ${pages}`, W - M, H - 8, { align: 'right' });
  }
  doc.save(`Laporan_${fileSlug()}_${R.p}.pdf`);
  toast('Fail PDF dimuat turun ✔');
}

/* ---------- Tetapan & sandaran ---------- */
async function renderSettings() {
  $('#setName').value = bizName;
  const info = $('#storageInfo');
  let txt = `${data.sales.length} rekod jualan, ${data.purchases.length} rekod belian.`;
  try {
    if (navigator.storage?.estimate) {
      const { usage } = await navigator.storage.estimate();
      txt += ` Ruang digunakan: ${(usage / 1024 / 1024).toFixed(1)} MB.`;
    }
  } catch { /* abaikan */ }
  info.textContent = txt;
}

function download(blob, name) {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = name;
  document.body.append(a);
  a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
}

function backup() {
  const payload = { app: 'buku-kedai', version: 1, exportedAt: new Date().toISOString(), bizName, sales: data.sales, purchases: data.purchases };
  download(new Blob([JSON.stringify(payload)], { type: 'application/json' }), `sandaran-${fileSlug()}-${today()}.json`);
  toast('Sandaran dimuat turun ✔');
}

function cleanRecord(r) {
  if (!r || typeof r !== 'object' || !/^\d{4}-\d{2}-\d{2}$/.test(r.date) || !Array.isArray(r.items)) return null;
  const items = r.items.map(i => {
    const qty = Number(i?.qty) || 0, price = Number(i?.price) || 0;
    return { name: String(i?.name ?? '').slice(0, 200), qty, price, subtotal: round2(qty * price) };
  }).filter(i => i.name);
  if (!items.length) return null;
  return {
    id: typeof r.id === 'string' && r.id ? r.id.slice(0, 64) : uid(),
    date: r.date,
    party: String(r.party ?? '').slice(0, 200),
    payment: String(r.payment ?? '').slice(0, 50),
    note: String(r.note ?? '').slice(0, 1000),
    items,
    total: round2(items.reduce((a, i) => a + i.subtotal, 0)),
    receipt: typeof r.receipt === 'string' && /^data:image\/(jpeg|png|webp);base64,/.test(r.receipt) ? r.receipt : null,
    createdAt: Number(r.createdAt) || Date.now(),
    updatedAt: Number(r.updatedAt) || Date.now(),
  };
}

async function restore(file) {
  let j;
  try { j = JSON.parse(await file.text()); } catch { return toast('Fail sandaran tidak sah'); }
  if (!j || j.app !== 'buku-kedai' || !Array.isArray(j.sales) || !Array.isArray(j.purchases)) return toast('Ini bukan fail sandaran Buku Kedai');
  if (!confirm(`Pulihkan ${j.sales.length} jualan dan ${j.purchases.length} belian?\nRekod sedia ada akan dikekalkan (rekod sama akan dikemas kini).`)) return;
  let count = 0;
  for (const t of TYPES) for (const r of j[t]) {
    const c = cleanRecord(r);
    if (c) { await put(t, c); count++; }
  }
  if (j.bizName && !bizName) await put('meta', { key: 'bizName', value: String(j.bizName).slice(0, 100) });
  await load();
  render();
  toast(`${count} rekod dipulihkan ✔`);
}

/* ---------- Toast ---------- */
let toastTimer;
function toast(msg) {
  const t = $('#toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove('show'), 2600);
}

/* ---------- Event ---------- */
document.addEventListener('click', async e => {
  const t = e.target;
  const tabBtn = t.closest('#tabs button');
  if (tabBtn) return showTab(tabBtn.dataset.tab);
  const nw = t.closest('[data-new]');
  if (nw) return openForm(nw.dataset.new);
  if (t.closest('[data-close]')) return t.closest('dialog').close();
  if (t.matches('[data-viewsrc]')) return viewImg(t.src);
  if (t.id === 'rmReceipt') { receiptData = null; return showReceipt(); }

  const card = t.closest('.entry');
  if (card) {
    const { type, id } = card.dataset;
    const rec = data[type].find(r => r.id === id);
    if (!rec) return;
    if (t.closest('[data-del]')) {
      if (!confirm(`Padam rekod ${LABEL[type].toLowerCase()} ${fmt(rec.total)} pada ${fmtDate(rec.date)}?`)) return;
      await del(type, id);
      await load();
      render();
      return toast('Rekod dipadam');
    }
    if (t.closest('[data-view]')) return viewImg(rec.receipt);
    return openForm(type, rec);
  }
});

// tutup dialog bila klik di luar
for (const d of $$('dialog')) d.addEventListener('click', e => { if (e.target === d) d.close(); });

$('#dashMonth').addEventListener('change', renderDashboard);

for (const type of TYPES) {
  const sec = $('#tab-' + type);
  $('.f-month', sec).addEventListener('change', e => { listState[type].month = e.target.value; renderList(type); });
  $('.f-all', sec).addEventListener('click', () => { listState[type].month = ''; renderList(type); });
  $('.f-search', sec).addEventListener('input', e => { listState[type].q = e.target.value.trim(); renderList(type); });
}

$$('input[name=period]').forEach(r => r.addEventListener('change', renderReport));
$('#repYear').addEventListener('change', renderReport);
$('#repMonth').addEventListener('change', renderReport);
$('#btnXlsx').addEventListener('click', () => {
  try { exportXlsx(); } catch (err) { console.error(err); toast('Gagal jana Excel'); }
});
$('#btnPdf').addEventListener('click', async e => {
  const b = e.currentTarget;
  b.disabled = true;
  try { await exportPdf(); } catch (err) { console.error(err); toast('Gagal jana PDF'); }
  finally { b.disabled = false; }
});

$('#saveName').addEventListener('click', async () => {
  bizName = $('#setName').value.trim().slice(0, 100);
  await put('meta', { key: 'bizName', value: bizName });
  render();
  toast('Nama disimpan ✔');
});
$('#btnBackup').addEventListener('click', backup);
$('#restoreFile').addEventListener('change', e => { const f = e.target.files[0]; e.target.value = ''; if (f) restore(f); });
$('#btnWipe').addEventListener('click', async () => {
  if (!confirm('Padam SEMUA rekod jualan dan belian? Tindakan ini tidak boleh dibatalkan.')) return;
  if (prompt('Taip PADAM untuk sahkan') !== 'PADAM') return toast('Dibatalkan');
  for (const t of TYPES) await clear(t);
  await load();
  render();
  toast('Semua data dipadam');
});

/* ---------- Mula ---------- */
(async function init() {
  try {
    db = await openDB();
    await load();
  } catch (err) {
    console.error(err);
    document.querySelector('main').innerHTML = '<div class="card"><h3>Storan tidak tersedia</h3><p>Pelayar ini tidak membenarkan simpanan data (mungkin mod peribadi/incognito). Sila buka dalam pelayar biasa.</p></div>';
    return;
  }
  render();
  try { await navigator.storage?.persist?.(); } catch { /* abaikan */ }
  if ('serviceWorker' in navigator && location.protocol.startsWith('http')) {
    navigator.serviceWorker.register('sw.js').catch(() => {});
  }
})();
