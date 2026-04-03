(function () {
  const cfg = window.eduTrackAnalytics;
  if (!cfg || !cfg.articleId || !cfg.endpoint) return;

  const articleId = cfg.articleId;
  const endpoint = cfg.endpoint;
  const sessionId = localStorage.getItem("edutrack_session") || crypto.randomUUID();
  localStorage.setItem("edutrack_session", sessionId);

  const trackedSections = Array.from(document.querySelectorAll(".track-section"));
  const visibleSince = new Map();

  function sendPayload(section, durationSeconds) {
    if (durationSeconds <= 0) return;
    const payload = {
      article_id: articleId,
      section,
      duration_seconds: Math.round(durationSeconds),
      session_id: sessionId,
    };

    navigator.sendBeacon(endpoint, new Blob([JSON.stringify(payload)], { type: "application/json" }));
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        const section = entry.target.dataset.section;
        if (!section) return;

        if (entry.isIntersecting) {
          visibleSince.set(section, Date.now());
        } else if (visibleSince.has(section)) {
          const startedAt = visibleSince.get(section);
          const elapsed = (Date.now() - startedAt) / 1000;
          sendPayload(section, elapsed);
          visibleSince.delete(section);
        }
      });
    },
    { threshold: 0.4 }
  );

  trackedSections.forEach((sectionNode) => observer.observe(sectionNode));

  const articleStart = Date.now();
  window.addEventListener("beforeunload", () => {
    visibleSince.forEach((startedAt, section) => {
      sendPayload(section, (Date.now() - startedAt) / 1000);
    });
    sendPayload("article", (Date.now() - articleStart) / 1000);
  });
})();
