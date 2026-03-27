document.addEventListener('DOMContentLoaded', () => {
  // Fade-up on scroll
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); });
  }, { threshold: 0.1 });
  document.querySelectorAll('.fade-up').forEach(el => obs.observe(el));

  // Mobile nav
  const toggle = document.querySelector('.nav-toggle');
  const links = document.querySelector('.nav-links');
  if (toggle) toggle.addEventListener('click', () => links.classList.toggle('open'));

  // Tabs
  document.querySelectorAll('.tabs').forEach(tg => {
    tg.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        tg.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        tg.parentElement.querySelectorAll('.tab-panel').forEach(p => {
          p.classList.toggle('active', p.id === btn.dataset.tab);
        });
      });
    });
  });

  // Accordion
  document.querySelectorAll('.accordion-header').forEach(h => {
    h.addEventListener('click', () => {
      const item = h.parentElement;
      const open = item.classList.contains('open');
      item.parentElement.querySelectorAll('.accordion-item').forEach(i => i.classList.remove('open'));
      if (!open) item.classList.add('open');
    });
  });

  // Code copy
  document.querySelectorAll('.code-copy').forEach(btn => {
    btn.addEventListener('click', () => {
      const text = btn.closest('.code-block').querySelector('.code-body').textContent;
      navigator.clipboard.writeText(text).then(() => {
        btn.textContent = 'Copied!';
        setTimeout(() => btn.textContent = 'Copy', 1200);
      });
    });
  });

  // Book mobile TOC — clone sidebar content into collapsible inline TOC
  const sb = document.querySelector('.book-sidebar');
  const mobileToc = document.getElementById('mobile-toc');
  if (sb && mobileToc) {
    const btn = document.createElement('button');
    btn.className = 'mobile-toc-toggle';
    btn.innerHTML = 'Table of Contents <span class="arrow">&#9660;</span>';
    const body = document.createElement('div');
    body.className = 'mobile-toc-body';
    body.innerHTML = sb.innerHTML;
    mobileToc.appendChild(btn);
    mobileToc.appendChild(body);

    btn.addEventListener('click', () => {
      btn.classList.toggle('open');
      body.classList.toggle('open');
    });
    body.querySelectorAll('a').forEach(a => a.addEventListener('click', () => {
      btn.classList.remove('open');
      body.classList.remove('open');
    }));
  }

  // Book sidebar toggle (legacy, hidden on mobile now)
  const st = document.querySelector('.sidebar-toggle');
  if (st && sb) {
    st.addEventListener('click', () => sb.classList.toggle('open'));
  }

  // Book sidebar active tracking
  const slinks = document.querySelectorAll('.sidebar-chapter, .sidebar-section-link');
  if (slinks.length) {
    const sections = document.querySelectorAll('.book-content [id]');
    const update = () => {
      let cur = '';
      sections.forEach(s => { if (s.getBoundingClientRect().top <= 100) cur = s.id; });
      slinks.forEach(l => { const h = l.getAttribute('href'); if (h) l.classList.toggle('active', h === '#' + cur); });
    };
    window.addEventListener('scroll', update);
    update();
  }

  // Smooth anchor scroll
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const t = document.querySelector(a.getAttribute('href'));
      if (t) { e.preventDefault(); t.scrollIntoView({ behavior: 'smooth' }); }
    });
  });

  // Run calculator
  const calc = document.getElementById('run-calculator');
  if (calc) {
    const go = () => {
      const d = document.getElementById('calc-design').value;
      const k = +document.getElementById('calc-factors').value || 2;
      const l = +document.getElementById('calc-levels').value || 2;
      const b = +document.getElementById('calc-blocks').value || 1;
      let n = 0, info = '';
      switch (d) {
        case 'full_factorial': n = l ** k; info = `${l}^${k}`; break;
        case 'fractional_factorial': n = 2 ** Math.max(k - 1, 1); info = `2^(${k}-1)`; break;
        case 'plackett_burman': n = k + 1; if (n % 4) n = Math.ceil(n / 4) * 4; info = `next multiple of 4 >= ${k}+1`; break;
        case 'latin_hypercube': n = Math.max(10, 2 * k); info = `max(10, 2x${k})`; break;
        case 'central_composite': { const f = 2 ** k, s = 2 * k, c = Math.max(3, k); n = f + s + c; info = `${f}+${s}+${c}`; break; }
        case 'box_behnken': n = k < 3 ? 0 : [0, 0, 0, 15, 27, 46][k] || k * 8; info = k < 3 ? 'needs 3+ factors' : 'Box-Behnken'; break;
      }
      document.getElementById('calc-result').innerHTML =
        `Design: ${d.replace(/_/g, ' ')}  |  Base: ${n} (${info})  |  Blocks: ${b}  |  Total: ${n * b}`;
    };
    calc.querySelectorAll('select, input').forEach(el => { el.addEventListener('change', go); el.addEventListener('input', go); });
    go();
  }
});
