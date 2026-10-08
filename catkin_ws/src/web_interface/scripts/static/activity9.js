(() => {
  const script = document.currentScript;
  const { statusUrl, stage, token } = script.dataset;
  const message = document.getElementById('camera-message');
  let leaving = false;
  let failures = 0;
  async function poll() {
    if (leaving) return;
    try {
      const response = await fetch(statusUrl, { cache: 'no-store' });
      if (!response.ok) throw new Error('Status indisponível');
      const state = await response.json();
      failures = 0;
      if (state.stage !== stage || state.token !== token) {
        leaving = true;
        window.location.reload();
        return;
      }
      if (message) message.textContent = state.message;
    } catch (error) {
      failures += 1;
      if (message) message.textContent = 'A conexão está demorando. Aguarde um instante...';
      if (failures >= 15) {
        leaving = true;
        if (message) message.textContent = 'A conexão foi interrompida. Recarregue a página para tentar novamente.';
        return;
      }
    }
    window.setTimeout(poll, 1000);
  }
  window.addEventListener('pagehide', () => {
    leaving = true;
    // Internal navigation keeps multi mode. Closing the page lets its lease expire.
  });
  window.addEventListener('pageshow', event => {
    if (event.persisted) window.location.reload();
  });
  poll();
})();
