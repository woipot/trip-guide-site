(function () {
  var synth = window.speechSynthesis;
  function voiceFor(lang) { if (!synth) return null; var vs = synth.getVoices() || [], pre = lang.slice(0, 2);
    return vs.find(function (v) { return v.lang && v.lang.replace('_', '-').toLowerCase() === lang.toLowerCase(); }) || vs.find(function (v) { return v.lang && v.lang.toLowerCase().indexOf(pre) === 0; }) || null; }
  function speak(text, lang, onend) { if (!synth) return; synth.cancel(); var u = new SpeechSynthesisUtterance(text); u.lang = lang; var v = voiceFor(lang); if (v) u.voice = v; u.rate = 1; if (onend) { u.onend = onend; u.onerror = onend; } synth.speak(u); }
  if (!synth) document.querySelectorAll('.gplay').forEach(function (b) { b.hidden = true; });
  function reset(b) { b.classList.remove('playing'); b.textContent = '▶ Слушать'; }
  document.querySelectorAll('.chap').forEach(function (chap) {
    var list = chap.querySelector('.gstations'), nav = chap.querySelector('.gnav'), mode = chap.querySelector('.gmode'), play = chap.querySelector('.gplay');
    var sts = chap.querySelectorAll('.gst'), i = 0;
    function show() { sts.forEach(function (s, k) { s.classList.toggle('cur', k === i); }); chap.querySelector('.gpos').textContent = (i + 1) + ' из ' + sts.length;
      chap.querySelector('.gprev').disabled = i === 0; chap.querySelector('.gnext').disabled = i === sts.length - 1; }
    mode.addEventListener('click', function () { var on = mode.getAttribute('aria-pressed') !== 'true'; mode.setAttribute('aria-pressed', on ? 'true' : 'false'); list.classList.toggle('stepmode', on); nav.hidden = !on; if (on) { i = 0; show(); } });
    chap.querySelector('.gprev').addEventListener('click', function () { if (i > 0) { i--; show(); if (play.classList.contains('playing')) play.click(), play.click(); } });
    chap.querySelector('.gnext').addEventListener('click', function () { if (i < sts.length - 1) { i++; show(); if (play.classList.contains('playing')) play.click(), play.click(); } });
    play.addEventListener('click', function () {
      if (play.classList.contains('playing')) { synth.cancel(); reset(play); return; }
      document.querySelectorAll('.gplay.playing').forEach(reset);
      var parts = [];
      if (list.classList.contains('stepmode')) { var c = sts[i]; parts.push(c.querySelector('h4').textContent + '. ' + c.querySelector('p').textContent); }
      else { parts.push(chap.querySelector('.cintro').textContent); var st = chap.querySelector('.story'); if (st) parts.push(st.querySelector('h4').textContent + '. ' + st.querySelector('p').textContent);
        sts.forEach(function (s) { parts.push(s.querySelector('h4').textContent + '. ' + s.querySelector('p').textContent); }); }
      play.classList.add('playing'); play.textContent = '■ Стоп';
      speak(parts.join(' '), 'ru-RU', function () { reset(play); });
    });
  });
  function openHash() { var h = location.hash; if (h && h.indexOf('#g-') === 0) { var el = document.querySelector(h); if (el) { el.querySelector('details').open = true; el.scrollIntoView(); } } }
  window.addEventListener('hashchange', openHash); openHash();
  document.addEventListener('click', function (e) { var a = e.target.closest('a[href^="#g-"]'); if (!a) return; var el = document.querySelector(a.getAttribute('href')); if (el) el.querySelector('details').open = true; });
  var FK = 'gz-guide-find', fs = {}; try { fs = JSON.parse(localStorage.getItem(FK) || '{}') || {}; } catch (e) {}
  document.querySelectorAll('.gfind input').forEach(function (x) { if (fs[x.id]) x.checked = true; x.addEventListener('change', function () { fs[x.id] = x.checked; try { localStorage.setItem(FK, JSON.stringify(fs)); } catch (e) {} }); });
})();
