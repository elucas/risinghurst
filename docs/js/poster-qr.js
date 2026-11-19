// Draws a QR code linking to the current page into every [data-poster-qr] element,
// so a printed poster always points at wherever it was printed from (live or dev).
// Uses vendored qrcode-generator 2.0.4 (MIT, Kazuhiko Arase): static/js/qrcode-generator-2.0.4.js
(function () {
    function draw() {
        if (typeof qrcode !== "function") return;
        // Drop query/hash: a shorter URL gives a simpler, easier-to-scan code.
        var url = location.origin + location.pathname;
        document.querySelectorAll("[data-poster-qr]").forEach(function (el) {
            var qr = qrcode(0, "M");   // 0 = smallest size that fits; M = ~15% error correction
            qr.addData(url);
            qr.make();
            el.innerHTML = qr.createSvgTag({ cellSize: 1, margin: 2, scalable: true, title: "QR code: " + url });
        });
        document.querySelectorAll("[data-poster-url]").forEach(function (el) {
            el.textContent = url.replace(/^https?:\/\//, "").replace(/\/$/, "");
        });
    }
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", draw);
    } else {
        draw();
    }
})();
