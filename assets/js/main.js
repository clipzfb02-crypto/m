(() => {
  const root = document.documentElement;

  // Theme toggle: follows the OS until the visitor picks one, then remembers it.
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
  const currentTheme = () => root.dataset.theme || (prefersDark.matches ? 'dark' : 'light');

  document.querySelector('.theme-toggle').addEventListener('click', () => {
    const next = currentTheme() === 'dark' ? 'light' : 'dark';
    root.dataset.theme = next;
    try {
      localStorage.setItem('theme', next);
    } catch (e) {}
  });

  // Mobile menu.
  const navToggle = document.querySelector('.nav-toggle');
  const navLinks = document.getElementById('nav-links');
  const setNavOpen = (open) => {
    navToggle.setAttribute('aria-expanded', String(open));
    navLinks.classList.toggle('open', open);
  };

  navToggle.addEventListener('click', () => {
    setNavOpen(navToggle.getAttribute('aria-expanded') !== 'true');
  });
  navLinks.addEventListener('click', (e) => {
    if (e.target.closest('a')) setNavOpen(false);
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') setNavOpen(false);
  });

  // Hairline under the header once the page has scrolled.
  const header = document.querySelector('.site-header');
  const onScroll = () => header.classList.toggle('scrolled', window.scrollY > 8);
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  // Highlight the nav link for the section currently in view.
  const links = [...navLinks.querySelectorAll('a[href^="#"]')];
  const sectionObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        links.forEach((link) => {
          if (link.getAttribute('href') === `#${entry.target.id}`) {
            link.setAttribute('aria-current', 'true');
          } else {
            link.removeAttribute('aria-current');
          }
        });
      });
    },
    { rootMargin: '-45% 0px -50% 0px' }
  );
  document.querySelectorAll('main section[id]').forEach((section) => sectionObserver.observe(section));

  // Fade elements in as they scroll into view.
  const revealObserver = new IntersectionObserver(
    (entries, observer) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      });
    },
    { rootMargin: '0px 0px -8% 0px' }
  );
  document.querySelectorAll('.reveal').forEach((el) => revealObserver.observe(el));

  // Copy-to-clipboard buttons.
  document.querySelectorAll('[data-copy]').forEach((button) => {
    const label = button.textContent;
    button.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(button.dataset.copy);
        button.textContent = 'Copied!';
      } catch (e) {
        button.textContent = 'Copy failed';
      }
      setTimeout(() => {
        button.textContent = label;
      }, 2000);
    });
  });

  document.getElementById('year').textContent = new Date().getFullYear();
})();
