/** TVBO platform docs front-end: on-this-page TOC, code-copy buttons, server
 *  search, and the mobile nav toggle. Same-origin (CSP-safe); no-ops off /docs.
 */
(function () {
    "use strict";

    function buildToc() {
        var body = document.querySelector(".o_tvbo_docs_body");
        var holder = document.getElementById("o_docs_toc");
        if (!body || !holder) {
            return;
        }
        var all = Array.prototype.slice.call(body.querySelectorAll("h1[id], h2[id], h3[id]"));
        if (all.length && all[0].tagName === "H1") {
            all.shift();
        }
        if (!all.length) {
            var rail = holder.closest(".o_docs_toc");
            if (rail) rail.style.display = "none";
            return;
        }
        var ul = document.createElement("ul");
        ul.className = "o_docs_toc_list";
        all.forEach(function (h) {
            var li = document.createElement("li");
            li.className = "o_docs_toc_" + h.tagName.toLowerCase();
            var a = document.createElement("a");
            a.href = "#" + h.id;
            a.textContent = (h.textContent || "").replace(/¶$/, "").trim();
            a.dataset.target = h.id;
            li.appendChild(a);
            ul.appendChild(li);
        });
        holder.appendChild(ul);
        wireScrollSpy(all, ul);
    }

    function wireScrollSpy(headings, ul) {
        var links = ul.querySelectorAll("a");
        if (!("IntersectionObserver" in window)) {
            return;
        }
        var observer = new IntersectionObserver(
            function (entries) {
                entries.forEach(function (entry) {
                    if (!entry.isIntersecting) return;
                    links.forEach(function (l) {
                        l.classList.toggle("active", l.dataset.target === entry.target.id);
                    });
                });
            },
            { rootMargin: "0px 0px -75% 0px", threshold: 0 }
        );
        headings.forEach(function (h) {
            observer.observe(h);
        });
    }

    function addCopyButtons() {
        var blocks = document.querySelectorAll(".o_tvbo_docs_body pre");
        blocks.forEach(function (block) {
            if (block.querySelector(".o_docs_copy")) return;
            var btn = document.createElement("button");
            btn.type = "button";
            btn.className = "o_docs_copy";
            btn.textContent = "Copy";
            btn.addEventListener("click", function () {
                var code = block.querySelector("code") || block;
                var text = code.innerText.replace(/\n$/, "");
                navigator.clipboard.writeText(text).then(function () {
                    btn.textContent = "Copied!";
                    setTimeout(function () { btn.textContent = "Copy"; }, 1500);
                });
            });
            block.appendChild(btn);
        });
    }

    function wireSearch() {
        var input = document.getElementById("o_docs_search_input");
        var results = document.getElementById("o_docs_search_results");
        if (!input || !results) {
            return;
        }
        var timer = null;
        function run() {
            var q = input.value.trim();
            if (q.length < 2) {
                results.innerHTML = "";
                return;
            }
            fetch("/docs/search?q=" + encodeURIComponent(q), { headers: { Accept: "application/json" } })
                .then(function (r) { return r.json(); })
                .then(function (rows) {
                    if (!rows.length) {
                        results.innerHTML = '<div class="o_docs_search_empty">No matches</div>';
                        return;
                    }
                    results.innerHTML = "";
                    rows.forEach(function (row) {
                        var a = document.createElement("a");
                        a.href = "/docs/" + row.slug;
                        a.className = "o_docs_search_hit";
                        a.innerHTML =
                            '<span class="o_docs_search_name"></span>' +
                            '<span class="o_docs_search_cat"></span>';
                        a.querySelector(".o_docs_search_name").textContent = row.name;
                        a.querySelector(".o_docs_search_cat").textContent = row.category;
                        results.appendChild(a);
                    });
                })
                .catch(function () { results.innerHTML = ""; });
        }
        input.addEventListener("input", function () {
            clearTimeout(timer);
            timer = setTimeout(run, 200);
        });
        document.addEventListener("click", function (e) {
            if (!results.contains(e.target) && e.target !== input) {
                results.innerHTML = "";
            }
        });
    }

    function wireNavToggle() {
        var btn = document.querySelector(".o_docs_nav_toggle");
        var nav = document.querySelector(".o_docs_nav");
        if (!btn || !nav) {
            return;
        }
        btn.addEventListener("click", function () {
            var open = nav.classList.toggle("is-open");
            btn.setAttribute("aria-expanded", open ? "true" : "false");
        });
    }

    function init() {
        buildToc();
        addCopyButtons();
        wireSearch();
        wireNavToggle();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
