(function () {
  var C = window.TRIP_CFG || {}, R = C.rate, KEY = C.key + '-choices', CKEY = C.key + '-checklist';
  function nf(x) { return Math.round(x).toLocaleString('ru-RU').replace(/ /g, ' '); }
  function k(v) { v = v / 1000; return (v < 10 ? (Math.round(v * 10) / 10) : Math.round(v)).toString().replace('.', ','); }
  function rr(lo, hi) { var a = k(lo * R), b = k(hi * R); return (a === b ? a : a + '–' + b) + ' ' + C.thousand + ' ' + C.home; }
  function num(el, a) { return el ? (parseFloat(el.getAttribute(a)) || 0) : 0; }
  function calc() {
    var dLo = 0, dHi = 0, upg = 0;
    document.querySelectorAll('article.day').forEach(function (day) {
      var lo = num(day, 'data-flo'), hi = num(day, 'data-fhi'), w = num(day, 'data-fwalk');
      day.querySelectorAll('input[type=radio]:checked').forEach(function (r) {
        lo += num(r, 'data-lo'); hi += num(r, 'data-hi'); w += num(r, 'data-walk'); if (r.value !== '0') upg++;
      });
      dLo += lo; dHi += hi;
      var c = day.querySelector('[data-cost]'); if (c) c.textContent = '≈ ' + nf(lo) + '–' + nf(hi) + ' ' + C.local + ' · ' + rr(lo, hi);
      var wt = (Math.round(w * 10) / 10).toString().replace('.', ',');
      var wk = day.querySelector('[data-walk]'); if (wk) wk.textContent = '≈ ' + wt + ' км';
      var wc = day.querySelector('[data-walkchip]'); if (wc) wc.textContent = 'пешком ≈ ' + wt + ' км';
    });
    var hLo = 0, hHi = 0, names = [];
    document.querySelectorAll('.hotels-choice').forEach(function (g) {
      var n = num(g, 'data-nights'), r = g.querySelector('input:checked');
      hLo += num(r, 'data-lo') * n; hHi += num(r, 'data-hi') * n;
      if (r) { names.push(r.closest('.opt').querySelector('.ot').firstChild.textContent + ' × ' + n);
        if (!r.closest('.opt').querySelector('.rec') && g.querySelector('.rec')) upg++; }
    });
    var tLo = C.fixed[0] + (hLo + dLo) * R, tHi = C.fixed[1] + (hHi + dHi) * R;
    var tt = '≈ ' + Math.round(tLo / 1000) + '–' + Math.round(tHi / 1000) + ' ' + C.thousand + ' ' + C.home;
    document.querySelectorAll('[data-total]').forEach(function (e) { e.textContent = tt; });
    var ht = document.querySelector('[data-hoteltotal]'); if (ht) ht.textContent = '≈ ' + rr(hLo, hHi);
    var hc = document.querySelector('[data-hotelcalc]'); if (hc) hc.textContent = names.join(', ');
    var u = document.querySelector('[data-upg]'); if (u) u.textContent = 'улучшений: ' + upg;
    function setc(key, v) { var e = document.querySelector('[data-c="' + key + '"]'); if (e) e.textContent = nf(v); }
    setc('hotel-lo', hLo * R); setc('hotel-hi', hHi * R); setc('days-lo', dLo * R); setc('days-hi', dHi * R); setc('tot-lo', tLo); setc('tot-hi', tHi);
    var bh = document.querySelector('[data-bar="hotel"]'); if (bh) bh.style.flex = (hLo + hHi) * R / 2;
    var bd = document.querySelector('[data-bar="days"]'); if (bd) bd.style.flex = (dLo + dHi) * R / 2;
  }
  function save() {
    var st = {}; document.querySelectorAll('.opt input[type=radio]:checked').forEach(function (r) { st[r.name] = r.value; });
    try { localStorage.setItem(KEY, JSON.stringify(st)); } catch (e) {}
  }
  function load() {
    var st = null; try { st = JSON.parse(localStorage.getItem(KEY) || 'null'); } catch (e) {}
    if (st) Object.keys(st).forEach(function (n) { var r = document.querySelector('input[name="' + n + '"][value="' + st[n] + '"]'); if (r) r.checked = true; });
  }
  load(); calc();
  document.addEventListener('change', function (e) { if (e.target.matches('.opt input')) { calc(); save(); } });
  var rs = document.getElementById('reset');
  if (rs) rs.addEventListener('click', function () {
    document.querySelectorAll('.choice').forEach(function (c) {
      var rec = c.querySelector('.rec'); var r = rec ? rec.closest('.opt').querySelector('input') : c.querySelector('input'); r.checked = true;
    });
    calc(); save();
  });
  // checklist persistence
  var boxes = document.querySelectorAll('#checks input[type=checkbox]'), saved = {};
  try { saved = JSON.parse(localStorage.getItem(CKEY) || '{}') || {}; } catch (e) {}
  boxes.forEach(function (b) {
    if (saved[b.id]) b.checked = true;
    b.addEventListener('change', function () { saved[b.id] = b.checked; try { localStorage.setItem(CKEY, JSON.stringify(saved)); } catch (e) {} });
  });
})();
