(function(){
  const state = {
    cardObserver:null,
    revealObserver:null,
    splashDone:false,
    navReady:false
  };

  const easeOutQuart = t => 1 - Math.pow(1 - t, 4);

  function raf(fn){ requestAnimationFrame(() => requestAnimationFrame(fn)); }

  function imgReveal(el){
    if(!el || !el.parentElement) return;
    el.parentElement.classList.add("loaded");
    el.classList.add("img-reveal");
  }

  function animatePageMount(root){
    const scope = root || document;
    raf(() => {
      scope.querySelectorAll(".page > .shell > *").forEach((el, i) => {
        el.style.animationDelay = `${i * 60}ms`;
        el.classList.add("anim-page-in");
      });
      observeReveal(scope);
      updateNavIndicators();
    });
  }

  function animateCards(){
    const cards = document.querySelectorAll(".grid .card");
    if(!cards.length) return;
    if(state.cardObserver) state.cardObserver.disconnect();
    if(!("IntersectionObserver" in window)){
      cards.forEach(card => card.classList.add("card-visible"));
      return;
    }
    state.cardObserver = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if(entry.isIntersecting){
          entry.target.classList.add("card-visible");
          state.cardObserver.unobserve(entry.target);
        }
      });
    }, {threshold:.08});
    cards.forEach((card, i) => {
      card.style.setProperty("--i", Math.min(i, 10));
      state.cardObserver.observe(card);
    });
  }

  function observeReveal(root){
    const scope = root || document;
    const items = scope.querySelectorAll(".section,.episode-panel,.detail-top,.list-page-head,.player-grid,.empty,.error");
    if(!items.length) return;
    if(!state.revealObserver && "IntersectionObserver" in window){
      state.revealObserver = new IntersectionObserver(entries => {
        entries.forEach(entry => {
          if(entry.isIntersecting){
            entry.target.classList.add("is-visible");
            state.revealObserver.unobserve(entry.target);
          }
        });
      }, {threshold:.1});
    }
    items.forEach(item => {
      if(item.classList.contains("is-visible")) return;
      item.classList.add("reveal-item");
      if(state.revealObserver) state.revealObserver.observe(item);
      else item.classList.add("is-visible");
    });
  }

  function animateCounters(){
    document.querySelectorAll(".stat-value").forEach(el => {
      const raw = el.textContent.trim();
      const num = parseInt(raw.replace(/\D/g,""), 10);
      if(!num || num < 2 || el.dataset.counted === "1") return;
      el.dataset.counted = "1";
      const suffix = raw.replace(/[\d,]/g,"");
      let start = null;
      const duration = 1200;
      const step = ts => {
        if(!start) start = ts;
        const progress = Math.min((ts - start) / duration, 1);
        el.textContent = Math.round(easeOutQuart(progress) * num) + suffix;
        if(progress < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    });
  }

  function animateProgressBars(){
    document.querySelectorAll(".bar-fill").forEach(fill => {
      if(fill.dataset.animated === "1") return;
      fill.dataset.animated = "1";
      const target = fill.style.width || getComputedStyle(fill).width;
      fill.style.width = "0";
      setTimeout(() => { fill.style.width = target; }, 300);
    });
  }

  function createRipple(target, event){
    if(!target || target.disabled) return;
    const rect = target.getBoundingClientRect();
    if(!rect.width || !rect.height) return;
    const ripple = document.createElement("span");
    const size = Math.max(rect.width, rect.height) * 1.6;
    ripple.style.cssText = `position:absolute;border-radius:50%;pointer-events:none;width:${size}px;height:${size}px;left:${event.clientX - rect.left - size/2}px;top:${event.clientY - rect.top - size/2}px;background:rgba(255,255,255,0.15);transform:scale(0);animation:ripple 500ms ease-out forwards;`;
    target.appendChild(ripple);
    setTimeout(() => ripple.remove(), 520);
  }

  function bindRipple(){
    document.addEventListener("click", event => {
      const target = event.target.closest(".btn,.round,.icon-btn,.view-btn,.tab-btn,.fs-action,.fs-close");
      if(!target) return;
      createRipple(target, event);
      if(target.classList.contains("card")){
        target.classList.add("card-press");
        setTimeout(() => target.classList.remove("card-press"), 130);
      }
    }, {passive:true});
  }

  function updateHeader(){
    const header = document.querySelector(".app-header");
    if(!header) return;
    const y = Math.min(window.scrollY || 0, 120);
    header.classList.toggle("header-scrolled", y > 20);
    header.style.setProperty("--scroll-shadow", `${Math.round(y / 4)}px`);
  }

  function bindHeader(){
    updateHeader();
    window.addEventListener("scroll", updateHeader, {passive:true});
  }

  function ensureNavIndicator(container){
    if(!container || container.querySelector(":scope > .nav-indicator")) return;
    const indicator = document.createElement("span");
    indicator.className = "nav-indicator";
    container.prepend(indicator);
  }

  function updateOneIndicator(container){
    if(!container) return;
    ensureNavIndicator(container);
    const indicator = container.querySelector(":scope > .nav-indicator");
    const active = container.querySelector("button.active,[data-go].active");
    if(!indicator || !active){
      if(indicator) indicator.style.setProperty("--nav-opacity", "0");
      return;
    }
    const c = container.getBoundingClientRect();
    const a = active.getBoundingClientRect();
    indicator.style.setProperty("--nav-left", `${a.left - c.left}px`);
    indicator.style.setProperty("--nav-top", `${a.top - c.top}px`);
    indicator.style.setProperty("--nav-width", `${a.width}px`);
    indicator.style.setProperty("--nav-height", `${a.height}px`);
    indicator.style.setProperty("--nav-opacity", "1");
  }

  function updateNavIndicators(){
    updateOneIndicator(document.querySelector(".nav-icons"));
    updateOneIndicator(document.querySelector(".mobile-tabs .rail"));
    updateOneIndicator(document.querySelector(".bottom-nav"));
  }

  function bindNavIndicators(){
    if(state.navReady) return;
    state.navReady = true;
    window.addEventListener("resize", updateNavIndicators, {passive:true});
    document.addEventListener("click", event => {
      if(event.target.closest("[data-go],.tab-btn,.bottom-nav button,.round")){
        setTimeout(updateNavIndicators, 40);
      }
    });
    setInterval(updateNavIndicators, 800);
  }

  function hideSplash(){
    if(state.splashDone) return;
    const splash = document.getElementById("splashScreen");
    if(!splash) return;
    state.splashDone = true;
    splash.classList.add("splash-hidden");
    setTimeout(() => splash.remove(), 560);
  }

  function initSplash(){
    const app = document.getElementById("app");
    const started = Date.now();
    const minTime = 1550;
    const maxTime = 4200;
    const maybeHide = () => {
      const wait = Math.max(0, minTime - (Date.now() - started));
      setTimeout(hideSplash, wait);
    };
    if(!app){
      setTimeout(hideSplash, minTime);
      return;
    }
    const observer = new MutationObserver(() => {
      if(app.querySelector(".card,.hero,.detail-top,.player-grid,.error,.empty")) {
        observer.disconnect();
        maybeHide();
      }
    });
    observer.observe(app, {childList:true, subtree:true});
    setTimeout(() => {
      observer.disconnect();
      hideSplash();
    }, maxTime);
  }

  function initMutationBridge(){
    const app = document.getElementById("app");
    if(!app) return;
    const observer = new MutationObserver(() => {
      raf(() => {
        animateCards();
        observeReveal(app);
        animateCounters();
        animateProgressBars();
        updateNavIndicators();
      });
    });
    observer.observe(app, {childList:true, subtree:true});
  }

  function initAnimations(){
    initSplash();
    bindRipple();
    bindHeader();
    bindNavIndicators();
    initMutationBridge();
    animatePageMount(document);
    animateCards();
    observeReveal(document);
    animateCounters();
    animateProgressBars();
  }

  window.imgReveal = imgReveal;
  window.animateCards = animateCards;
  window.animateCounters = animateCounters;
  window.animatePageMount = animatePageMount;
  window.BaltigoAnimations = {
    init:initAnimations,
    cards:animateCards,
    counters:animateCounters,
    page:animatePageMount,
    reveal:observeReveal,
    progress:animateProgressBars,
    nav:updateNavIndicators,
    splash:hideSplash
  };

  if(document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAnimations, {once:true});
  } else {
    initAnimations();
  }
})();
