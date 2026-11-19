(() => {
  "use strict";
  // socialscope site (split from the DGG chat site on Nov 19 2026): Lookup (lookup.js), Bots and About tabs.
  const $ = (s) => document.querySelector(s);

  // ---------- tabs
  const tabs = [...document.querySelectorAll(".tabs button")];
  const show = (name) => {
    tabs.forEach((b) => b.setAttribute("aria-selected", String(b.dataset.tab === name)));
    document.querySelectorAll(".tab").forEach((s) => { s.hidden = s.id !== "tab-" + name; });
    if (location.hash !== "#" + name) history.replaceState(null, "", "#" + name);
  };
  tabs.forEach((b) => b.addEventListener("click", () => show(b.dataset.tab)));
  const fromHash = () => { const t = (location.hash || "#lookup").slice(1).replace(/[^a-z]/g, ""); return ["lookup", "bots", "about"].includes(t) ? t : "lookup"; };
  window.addEventListener("hashchange", () => show(fromHash()));
  show(fromHash());

  // ---------- Bots tab (Nov 11 2026): confirmed finds from data/botfinds.json
  fetch("data/botfinds.json", { cache: "no-cache" }).then((r) => (r.ok ? r.json() : null)).catch(() => null).then((bf) => {
    bf = bf || {};
    const bots = bf.bots || [];
    $("#bots-empty").hidden = bots.length > 0;
    if (bf.updated) $("#about-gen").textContent = `Bots list updated ${bf.updated}.`;
    const mk = (tag, cls, txt) => { const n = document.createElement(tag); if (cls) n.className = cls; if (txt != null) n.textContent = txt; return n; };
    const link = (href, txt) => { const a = mk("a", null, txt); a.href = href; a.rel = "noopener nofollow"; return a; };
    if (bf.dispute) $("#bots-meta").replaceChildren(document.createTextNode(`${bots.length} account${bots.length === 1 ? "" : "s"} · updated ${bf.updated || "—"} · think one is wrong? Email `),
      link("mailto:" + bf.dispute, bf.dispute));
    $("#bots-list").replaceChildren(...bots.map((b) => {
      const c = mk("div", "card bot-card");
      const h = mk("h3"); h.append(link(b.profile, "u/" + b.name)); c.append(h);
      const p = mk("p", "note"); p.append(document.createTextNode(`Found by socialscope, reported ${b.submitted || "—"}. `),
        link(b.listing, "Listed as a bot by Bot Bouncer"), document.createTextNode(` (ban seen ${b.banned_since || "—"}, rechecked ${b.checked}).`));
      c.append(p);
      if (b.signals && b.signals.length) { const ul = mk("ul"); b.signals.forEach((s) => ul.append(mk("li", null, s))); c.append(mk("p", null, "What our detector saw:"), ul); }
      if (b.posts && b.posts.length) {
        c.append(mk("p", null, `Bot-period posts (${b.posts_note}):`));
        const ul = mk("ul", "bot-posts");
        b.posts.forEach((x) => { const li = mk("li"); li.append(mk("span", "note", `${x.time} · r/${x.sub} · ${x.kind}: `), document.createTextNode(x.text)); ul.append(li); });
        c.append(ul);
      } else if (b.posts_note) c.append(mk("p", "note", `No posts shown: ${b.posts_note}.`));
      return c;
    }));
  });
})();
