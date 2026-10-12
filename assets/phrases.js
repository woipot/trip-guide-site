(function () {
  var synth = window.speechSynthesis;
  function voiceFor(lang) { if (!synth) return null; var vs = synth.getVoices() || [], pre = lang.slice(0, 2);
    return vs.find(function (v) { return v.lang && v.lang.replace('_', '-').toLowerCase() === lang.toLowerCase(); }) || vs.find(function (v) { return v.lang && v.lang.toLowerCase().indexOf(pre) === 0; }) || null; }
  function speak(text, lang) { if (!synth) return; synth.cancel(); var u = new SpeechSynthesisUtterance(text); u.lang = lang; var v = voiceFor(lang); if (v) u.voice = v; u.rate = 0.85; synth.speak(u); }
  if (!synth) document.querySelectorAll('.psay').forEach(function (b) { b.hidden = true; });
  var cat = 'all', q = '', items = document.querySelectorAll('.phrase');
  function filter() { items.forEach(function (li) { li.hidden = !((cat === 'all' || li.getAttribute('data-cat') === cat) && (!q || li.getAttribute('data-search').indexOf(q) >= 0 || li.querySelector('.pzh').textContent.indexOf(q) >= 0)); }); }
  document.querySelectorAll('.ptab').forEach(function (b) { b.addEventListener('click', function () { document.querySelectorAll('.ptab').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); }); cat = b.getAttribute('data-cat'); filter(); }); });
  var ps = document.getElementById('psearch'); if (ps) ps.addEventListener('input', function () { q = ps.value.trim().toLowerCase(); filter(); });
  var big = document.getElementById('pbig');
  document.querySelectorAll('.pshow').forEach(function (b) { b.addEventListener('click', function () {
    big.querySelector('.pbig-zh').textContent = b.querySelector('.pzh').textContent; big.querySelector('.pbig-py').textContent = b.querySelector('.ppy').textContent;
    big.querySelector('.pbig-ru').textContent = b.querySelector('.pru').textContent; big.hidden = false; }); });
  big.addEventListener('click', function () { big.hidden = true; });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') big.hidden = true; });
  document.querySelectorAll('.psay').forEach(function (b) { b.addEventListener('click', function () { var li = b.closest('.phrase'); speak(li.querySelector('.pzh').textContent.replace(/[0-9·]/g, ' '), li.getAttribute('data-lang')); }); });
})();
