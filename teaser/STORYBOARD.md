---
format: 1920x1080
duration: 60s
message: "AFS Sentinel menemukan tanda bahaya di laporan keuangan emiten BEI secara otomatis — bertahun-tahun sebelum skandalnya meledak."
arc: Cold-open fakta → Twist (tandanya sudah ada) → Produk → Otonom → Cara kerja → Alert → Bukti → Klimaks backtest → Outro
audience: Juri Sectors Hackathon 2026 dan investor/analis pasar modal Indonesia
mode: autonomous
music: dark cinematic tension underscore building into a driving synth climax
---

## Video direction

- **Palette system** (from `frame.md`, AFS override): ground `ink-black` #0E1920 (alt surface #15232C); text `cream` #E7EEF0, secondary `cream-muted`, tertiary `cream-hint`; hairlines `border-dark`. The ONE loud accent is `fire-orange` = AFS danger red #FF7A70. The "orange register" (full red ground, dark ink) is used exactly twice: Frame 1 (the event) and the "25" payoff inside Frame 8. `status-safe` / `status-warn` / `status-danger` appear ONLY as data semantics (Aman/Waspada/Bahaya markers, Rendah/Sedang/Kritis pills), mirroring the product UI.
- **Type**: display = Instrument Sans 700, lowercase per preset, negative tracking; chrome/kickers/numbers-in-labels = IBM Plex Mono uppercase 0.14em; body = Instrument Sans 400/500. Tabular nums for every number.
- **Real footage treatment**: product recordings (`assets/footage/*.mp4`) always sit inside a browser-window frame — 1px `border-dark`, 10px radius (the only rounded thing besides pills), `ink-black-alt` title bar with three muted dots and mono URL `afs-sentinel.herokuapp.com/<path>`. Window occupies ~70–80% of frame width; never full-bleed; soft dark drop shadow allowed on the window only. Footage is muted (VO + BGM carry sound). Footage is never color-graded or restyled.
- **Motion grammar**: long-tail `power3` settles, `expo.out` for fast arrivals; no bounce/overshoot; entrances via `fromTo`. **Reveal model**: every piece enters on its spoken cue (word timings in each Scene line are the cue); nothing front-loaded. During holds only subtle jitter is allowed. Seams inside a frame are velocity-matched cuts (cut-catalog).
- **Rhythm / held frames**: Frame 1 ends on a held red field (tension). Frame 3 is the breather (single lockup, still hold). Frame 8's "25" lands then HOLDS still — the climax is stillness after the count. Frame 9 is a calm held end card. Frames 4, 5, 6, 7 carry the energy.
- **Caption band**: bottom ~17% is reserved for burned-in Indonesian captions; all content lives in the top ~83%.
- **Negative list**: no purple/blue "AI" gradients, no bokeh, no stock imagery, no fake UI that contradicts the real app, no emoji except those the real Telegram bot sends (🟡 🤖), no numbers not present in the brief/footage, no investment-advice language ("beli", "jual", "rekomendasi"). No slideshow (front-load then freeze); no screensaver (things floating independently); no lazy breathing; no back-half slow pans.

## Frame 1 — Cold open: 8 Mei 2023

- scene: Tanggal "8 mei 2023" menghantam layar merah, lalu baris "perdagangan saham WSKT dihentikan." masuk
- voiceover: "Delapan Mei, dua ribu dua puluh tiga. Bursa menghentikan perdagangan saham Waskita Karya."
- duration: 7.14s
- transition_in: cut
- status: animated
- src: compositions/frames/01-cold-open.html
- type: hook
- persuasion: Pattern interrupt with a real, verifiable event
- beat: tension
- blueprint: kinetic-type-beats
- focal:
- roles:
- sfx: none
- asset_candidates:

Adapt: keep the statement-builds-across-beats signature (each token is its own slam); orange register (red #FF7A70 ground, #0E1920 ink) for the whole frame; second line is a sentence, not a token.
Scene 1 (0.0–0.5s): full red field, empty except a tiny mono kicker top-left "BURSA EFEK INDONESIA · 2023" fading in — nothing else (VO silent lead-in).
Scene 2 (0.5–2.6s): display-size lowercase date builds token by token on the VO: "8" slams in at 0.5s, "mei" at 0.87s, "2023" at 1.43s — kinetic beat-slam (`kinetic-beat-slam`), each token a distinct entrance (scale-slam / side-snap / rise), locked on one baseline, left-aligned at rule-of-thirds, ~70% frame width. Ink #0E1920.
Scene 3 (3.4–5.9s): as the VO says "Bursa menghentikan perdagangan saham Waskita Karya", the date slides up on a smooth power3 settle and a second line reveals per-word (`dynamic-content-sequencing`) under it in h2 scale: "perdagangan saham WSKT dihentikan." — "WSKT" set in mono caps; a 36×2px ink rule stub draws before it.
Scene 4 (5.9–7.14s): hold still. Subtle jitter only. The frame is a held tension beat.

narrativeRole: Buka dengan kejadian nyata yang dikenal pasar — tanpa logo, tanpa perkenalan.
keyMessage: Skandal emiten itu nyata dan mahal.

## Frame 2 — Twist: tandanya sudah ada

- scene: Layar gelap; "tandanya sudah ada." lalu "di laporan keuangan." lalu "bertahun-tahun sebelumnya." menumpuk; lalu dinding 33 kode emiten memenuhi layar dan pertanyaan "siapa yang sempat membaca semuanya?"
- voiceover: "Padahal tandanya sudah ada di laporan keuangan, bertahun-tahun sebelumnya. Tapi siapa yang sempat membaca semuanya?"
- duration: 7.828s
- transition_in: zoom-through
- status: animated
- src: compositions/frames/02-twist.html
- type: problem
- persuasion: Pain agitation — too much to read by hand
- beat: frustration + curiosity
- blueprint: kinetic-type-beats
- focal:
- roles:
- sfx: none
- asset_candidates:

Adapt: kinetic-type stack for the first sentence; the question is carried by an accumulation of the 33 real Universe tickers (ASII UNTR TLKM EXCL ISAT TOWR UNVR ICBP INDF MYOR CPIN JPFA BUMI ITMG ANTM PGAS ACES GOTO MAPI KLBF MDKA MEDC AKRA BRPT EMTK SIDO TPIA INCO INTP AADI AMRT SMGR PTBA) — keep the "clutter shoved aside, question in the opened center" signature.
Scene 1 (0.0–1.5s): dark ground. h1 lowercase "tandanya sudah ada." reveals per-word at 0.3s, left-aligned upper third.
Scene 2 (1.5–2.7s): "di laporan keuangan." reveals under it on "laporan" (1.6s), cream-muted.
Scene 3 (2.7–4.5s): "bertahun-tahun sebelumnya." reveals at 2.73s in `fire-orange` red — the only colored line; a keyword glow (`asr-keyword-glow`) peaks on "bertahun-tahun".
Scene 4 (4.5–6.2s): on "Tapi" (4.74s) the three lines slide up and dim to 25%; a wall of the 33 mono tickers cascades in behind, row by row (`waterfall-entry`), filling the frame at low contrast (cream-hint, ~30% opacity), dense — overwhelm.
Scene 5 (6.2–7.83s): on "semuanya" (5.94s) the ticker wall is shoved outward to the edges (`center-outward-expansion` inverted — clutter pushed to the frame edge) and the question "siapa yang sempat membaca semuanya?" lands centered in h2, cream; hold still.

narrativeRole: Balik kejadian menjadi masalah yang bisa dicegah; bangun rasa penasaran.
keyMessage: Sinyalnya ada, tapi terkubur.

## Frame 3 — Perkenalan: AFS Sentinel

- scene: Cincin radar forensik menggambar diri, wordmark "AFS Sentinel" terbentuk, subjudul "pengawas dini laporan keuangan emiten" dan baris chip
- voiceover: "Kenalkan AFS Sentinel, pengawas forensik otomatis untuk emiten di Bursa Efek Indonesia."
- duration: 6.22s
- transition_in: blur-crossfade
- status: animated
- src: compositions/frames/03-intro.html
- type: product_intro
- persuasion: Named solution reveal
- beat: relief + intrigue
- blueprint: logo-assemble-lockup
- focal:
- roles:
- sfx: none
- asset_candidates:

Adapt: keep the "brand mark comes to exist on screen" signature — here an SVG scanning ring (thin circle + a 60° red arc + three tick marks) draws itself, then the wordmark letters cascade in beside it; the lockup extends with a chip row instead of a URL.
Scene 1 (0.0–0.7s): dark ground; the ring self-draws (`svg-path-draw`) centered-left of a centered lockup (~40% frame width together).
Scene 2 (0.7–1.9s): on "AFS Sentinel" (0.7s) the wordmark "AFS Sentinel" (display ~9cqw, NOT lowercased — it is a proper name; "AFS" in fire-orange red, "Sentinel" in cream) cascades in letter by letter (`waterfall-entry`); the red arc on the ring completes one sweep and stops.
Scene 3 (1.9–3.1s): on "pengawas forensik otomatis" subtitle in lead size, cream-muted: "pengawas dini laporan keuangan emiten" reveals per-word under the wordmark.
Scene 4 (3.1–6.22s): on "untuk emiten di Bursa Efek Indonesia" a mono chip row reveals left-to-right, 3 chips with 1px hairline borders: "BEI · 33 EMITEN NON-KEUANGAN" · "DATA: SECTORS API" · "OTONOM · TIAP 3 HARI"; hold still.

narrativeRole: Jawab pertanyaan Frame 2 dengan nama produk.
keyMessage: Ada penjaga yang membaca semuanya untuk Anda.

## Frame 4 — Berjalan sendiri

- scene: Jendela browser berisi rekaman dashboard lalu /logs asli; baris-baris "Otomatis · sistem" disorot; pill "setiap 3 hari", "tanpa manusia", "data Sectors API" muncul di sisi; penghitung "33 emiten"
- voiceover: "Setiap tiga hari, tanpa disentuh manusia, ia menarik data Sectors API dan memindai tiga puluh tiga emiten."
- duration: 7.032s
- transition_in: crossfade
- status: animated
- src: compositions/frames/04-autonomous.html
- type: key_feature
- persuasion: Show-don't-tell proof (real unattended run log)
- beat: control + ease
- blueprint: device-surface-showcase
- focal: assets/footage/logs.mp4
- roles: logs.mp4 = cutout (hero, inside browser window) · dashboard.mp4 = supporting (opening screen inside the same window)
- sfx: none
- asset_candidates: assets/footage/logs.mp4 — real /logs audit-run table, every row "Otomatis · sistem", row expands to per-emiten results; assets/footage/dashboard.mp4 — dashboard "Sistem aktif · pemindaian otomatis tiap 3 hari"

Adapt (v2, camera): the browser window is LARGE — a 1680×780 screen at (120,100), 87.5% of the frame width, bottom edge at y=881 so the caption band (y≥900) stays clear. The footage plays at 1:1 inside a virtual camera (one GSAP-transformed wrapper, seek-safe, same paused timeline) that punches in on the VO cue words. Kicker "JEJAK AUDIT · DATA ASLI PRODUKSI" top-left and the three pills top-right, above the window. Focus marks (red ring, spotlight that dims the rest, click ripple) are drawn in footage coordinates inside the camera, so they stay locked to the UI under zoom; callouts sit in frame space and never scale.
Scene 1 (0.0–1.45s): window rises; dashboard footage from 0.3s; camera 1.0→1.75× (0.3–0.9s, power3.inOut) onto the "Sistem aktif" card; ring "· pemindaian otomatis tiap 3 hari" (0.66s), then ring "Berikutnya: Jumat, 25 Sep 2026, 12:15 WIB" (1.0s). Pill 1 "SETIAP 3 HARI" at 0.3s.
Scene 2 (1.45–2.86s): hard cut to /logs, the camera cuts with it to 1.7× on the Pemicu + Dipindai columns. Ring sweeps down the "Otomatis · sistem" column (1.5s) with callout "OTOMATIS · SISTEM — PEMICU SETIAP RUN" on the newest run row; the recording's real click on that row (footage 0.55s → 2.0s) gets a ripple at the row centre, the row expands, and the ring narrows to "Otomatis · sistem … 33 / 0". Pill 2 "TANPA MANUSIA".
Scene 3 (2.86–4.3s): pill 3 "DATA SECTORS API"; marks clear and the camera pulls back to 1:1 (2.9–3.55s) before the footage scrolls (3.1–4.65s).
Scene 4 (4.3–7.03s): on "memindai tiga puluh tiga emiten" the camera punches 1.45× into the per-emiten list (4.3–4.95s), ring + spotlight on the Emiten column once the scroll settles (4.8s); a callout card counts 0→33 "EMITEN DIPINDAI · TIAP RUN". Camera releases to 1:1 at 6.35–6.95s before the slide-out.

narrativeRole: Bukti syarat Track 2 — eksekusi terjadwal tanpa manusia.
keyMessage: Otonom, bukan tombol manual.

## Frame 5 — Enam aturan forensik

- scene: Enam kartu rule bernomor 1–6 tersusun (Sloan, Divergensi Laba–Kas, Altman Z'', Beneish, Penjualan Orang Dalam, Laba tanpa Dividen) dengan subjudul awam; penanda menyala sesuai kata VO
- voiceover: "Enam aturan forensik mencari laba yang tak berwujud kas, utang yang melonjak, dan risiko gagal bayar."
- duration: 6.528s
- transition_in: push-slide LEFT
- status: animated
- src: compositions/frames/05-rules.html
- type: key_feature
- persuasion: Rule of three over a six-part method (authority by method)
- beat: clarity + confidence
- blueprint: grid-card-assemble
- focal:
- roles:
- sfx: none
- asset_candidates:

Adapt: keep the staggered self-assembly of N tiles into a grid; then instead of a zoom-out, tiles light up with status markers on their VO cue. Grid 3×2, ~80% frame width, upper 75% of frame. Each card: `ink-black-alt` surface, 1px hairline top border only (stat-card component), a numbered circle marker (1–6, like the product UI legend), rule name (h3, NOT lowercased: "Sloan Accrual Ratio", "Divergensi Laba–Kas", "Altman Z'' (Adapted)", "Beneish (Adapted)", "Penjualan Orang Dalam", "Laba tanpa Dividen"), and plain-language subtitle in caption size ("Seberapa banyak laba yang bukan uang tunai", "Laba naik, tapi kas operasi turun", "Risiko kesulitan keuangan", "Tanda tekanan untuk memoles laporan", "Orang dalam/pemegang saham utama menjual", "Untung, tapi tidak membagi kas"). Mono kicker above grid: "6 FORENSIC RULE · SKOR KOMPOSIT 0–100".
Scene 1 (0.0–1.1s): on "Enam aturan forensik" (0.3s) the six cards cascade in 1→6 (expo.out rise, stagger ≤0.35s) in a wide shot; all markers neutral grey.
Scene 2 (1.1–2.7s): virtual camera (`coordinate-target-zoom`, 1.45×) pushes to cards 1+2 on "mencari"; other cards dim (bottom row hidden so nothing sits in the caption band). Card 1 lights `status-danger` "BAHAYA" on "laba" (1.43s), card 2 `status-warn` "WASPADA" on "kas" (2.36s). Lighting = marker fill + ripple ring, 6px top bar, status frame with glow, tag pop, subtitle brightens.
Scene 3 (2.7–4.0s): on "utang" the camera travels to card 4 (1.75×); it lights `status-warn` "WASPADA" on "melonjak" (3.35s).
Scene 4 (4.0–5.1s): on "risiko" the camera travels to card 3 (1.75×); it lights `status-danger` "BAHAYA" on "gagal" (4.60s).
Scene 5 (5.15–7.03s): camera pulls back to the full grid; cards 5 and 6 light `status-safe` "AMAN" as the grid returns; hold.

narrativeRole: Jelaskan cara kerja dalam satu tarikan napas.
keyMessage: Metode forensik yang dikenal, dijalankan otomatis.

## Frame 6 — Alert Telegram

- scene: Jendela chat Telegram gelap "AFS Sentinel Bot"; pesan bot (format asli) muncul baris demi baris: "🟡 Sedang · UNVR — Unilever Indonesia Tbk", "Skor 45/100 · Laporan 2026-Q2", baris 🤖 ringkasan AI, dua poin temuan, tombol "Buka Incident"
- voiceover: "Begitu ada yang janggal, peringatan langsung masuk ke Telegram Anda."
- duration: 4.608s
- transition_in: crossfade
- status: animated
- src: compositions/frames/06-alert.html
- type: key_feature
- persuasion: Feature-to-benefit translation (you don't watch — it tells you)
- beat: urgency + control
- blueprint: agent-progress-theater
- focal:
- roles:
- sfx: none
- asset_candidates:

Adapt: keep "the receipt cascades in, rows arrive" signature, as a single bot message whose lines arrive; no loaders. Layout: centered chat panel ~44% frame width (Telegram-dark styling: panel #17212B, bubble #182533, header with round avatar "AS" in red and name "AFS Sentinel Bot" + "bot"), left of center; to the right a mono kicker + h2 "anda dikabari, bukan mencari." revealing last.
Reconstruction, not a phone recording: only text the real bot sends, no chat ids.
Scene 1 (0.0–0.9s): chat panel (1090px, camera at 1.05× centred) rises; "mengetik…" indicator on "Begitu ada yang".
Scene 2 (0.91–1.6s): on "janggal" a push-notification banner ("AFS Sentinel Bot" / "🟡 Sedang · UNVR — Unilever Indonesia Tbk") slams in over the chat — short decaying frame shake, red top-edge glow, avatar ping ring.
Scene 3 (1.67–2.9s): on "peringatan" the banner hands off and the camera pushes into the message (1.3×). The bubble grows top-down one line per cue: header 1.67s, "Skor 45/100 · Laporan 2026-Q2" on "langsung" 2.06s, 🤖 AI line on "masuk" 2.34s, bullets on "Telegram" 2.59s/2.76s, timestamp "12:15".
Scene 4 (2.92–5.0s): on "Anda" the camera pulls back to the wide layout; "Buka Incident ↗" arrives and gets one press (3.5s) with a click ripple; right-column kicker + h2 "anda dikabari, bukan mencari." reveal per-word; hold.

narrativeRole: Nilai nyata untuk analis: tidak perlu memantau.
keyMessage: Anda dikabari, bukan mencari.

## Frame 7 — Bukti yang bisa dilacak

- scene: Rekaman asli halaman Incident UNVR di jendela browser (diputar 2×): vonis → Ringkasan AI → kartu Sloan terbuka dengan formula dan endpoint; callout mono "SETIAP ANGKA → ENDPOINT SECTORS"
- voiceover: "Lengkap dengan ringkasan AI, dan bukti perhitungan yang bisa dilacak sampai ke data sumbernya."
- duration: 5.784s
- transition_in: zoom-through
- status: animated
- src: compositions/frames/07-evidence.html
- type: key_feature
- persuasion: Show-don't-tell proof + transparency (risk reversal against black-box AI)
- beat: trust
- blueprint: transcript-scroll-artifact-reveal
- focal: assets/footage/incident.mp4
- roles: incident.mp4 = cutout (hero, inside browser window)
- sfx: none
- asset_candidates: assets/footage/incident.mp4 — real incident page UNVR: verdict, Ringkasan AI, Bukti perhitungan cards, Sloan card expanded with formula + endpoint

Adapt (v2, camera): same LARGE window as Frame 4 (1680×780 screen at (120,100), clear of the caption band), URL "afs-sentinel.herokuapp.com/incidents/AFS-2026-Q2-0003". The real recorded scroll (2× clip, frame time = media time) has three static stretches — 1.05–2.45s, 3.15–4.15s, 4.95s–end — and the virtual camera lands on each one; marks are cleared before every scroll so they never drift off the UI.
Beat 1 (0.62–2.3s): camera 1.0→1.5× onto "Ringkasan AI" as the scroll settles; spotlight on the block, ring on its footnote "Ditulis AI dari 6 Rule Finding di bawah"; callout "RINGKASAN AI — DITULIS DARI 6 RULE FINDING".
Beat 2 (2.3–4.0s): on "bukti perhitungan" the camera rides the scroll to 1.45× on the evidence cards; rings on "22,7%" (Sloan) and "Z = 0,57" (Altman); callout "BUKTI PERHITUNGAN — SLOAN 22,7% · ALTMAN 0,57". The recording's real click on "Lihat rincian perhitungan" (~3.67s) gets a ripple, the spotlight narrows to the Sloan card, and the opened Formula gets a ring (3.78s).
Beat 3 (4.1–5.78s): camera follows the scroll down to 1.6× on Ambang + "Endpoint sumber /v2/financials/quarterly/UNVR.JK/"; ring + spotlight on the endpoint (4.95s) with a leader to the red callout "SETIAP ANGKA → ENDPOINT SECTORS API" (4.85s); hold.

narrativeRole: Tunjukkan kedalaman dan kejujuran analisis.
keyMessage: Bukan kotak hitam — semua angka punya sumber.

## Frame 8 — Klimaks: 25 bulan lebih awal

- scene: Rekaman asli /backtest WSKT (grafik skor per kuartal + garis kejadian 8 Mei 2023), lalu register merah: angka "25" menghitung naik, "bulan sebelum suspensi WSKT"; baris kecil "SRIL · 42 bulan sebelum pailit"
- voiceover: "Diuji pada kasus nyata, Sentinel sudah menandai Waskita dua puluh lima bulan sebelum suspensi."
- duration: 6.992s
- transition_in: crossfade
- status: animated
- src: compositions/frames/08-proof.html
- type: social_proof
- persuasion: Statistical proof from a backtest against a real event
- beat: awe + triumph
- blueprint: dataviz-countup
- focal: assets/footage/backtest.mp4
- roles: backtest.mp4 = cutout (inside browser window, first half) then background (dimmed behind red wipe)
- sfx: none
- asset_candidates: assets/footage/backtest.mp4 — real backtest WSKT chart with claim sentence "Pertama kali Sedang: 2021-Q1, 25 bulan sebelum ..." and SRIL tab

Adapt: keep "one exploding statistic, camera pushes THROUGH to the hero metric" — the push goes through the real backtest chart into the red register where the count-up lives.
The footage is a frame-local `<video>` (f08-backtest.mp4) inside a camera rig — it must NOT also be hoisted into index.html. Window 1360px wide (~71%), annotations are authored in footage pixels so they ride the camera.
Scene 1 (0.0–1.3s): wide shot; the real page scroll to the WSKT chart plays. HUD kicker "BACKTEST · DIUJI PADA KASUS NYATA" on "Diuji" (0.3s), leaving as the camera starts.
Scene 2 (1.3–2.44s): camera pushes (1.7× footage) to the first flag point — 2021-Q1 on the score line, with the y-axis and the dashed 8-Mei-2023 line in view — landing on "Sentinel" (1.88s): spotlight ring + ripple on the point, label "2021-Q1 · PERTAMA KALI SEDANG".
Scene 3 (2.44–3.06s): on "menandai" the camera travels up to the real claim sentence (1.9×), landing on "Waskita" (2.86s): spotlight box around "Pertama kali Sedang: 2021-Q1, 25 bulan sebelum", red marker underline sweeps under "Sedang: 2021-Q1, 25 bulan".
Scene 4 (3.06–5.2s): the camera accelerates THROUGH the "25" glyphs (blur), the red register floods in, and on "dua puluh lima" (3.28s) the giant number counts 0→25 with "bulan" on 3.74s; "sebelum suspensi saham WSKT (8 mei 2023)" on 4.03s.
Scene 5 (5.2–7.59s): mono sub-line "SRIL · 42 BULAN SEBELUM PAILIT · SUMBER: OUTPUT /BACKTEST"; hold still — the climax is stillness.

narrativeRole: Payoff dari cold open — lingkaran cerita tertutup.
keyMessage: Sentinel akan melihatnya 25 bulan lebih awal.

## Frame 9 — Outro

- scene: Lockup "AFS Sentinel" + tagline "peringatan dini, sebelum terlambat."; baris "Powered by Sectors API · Sectors Hackathon 2026 · Track 2 — Automation & Workflows"; disclaimer kecil
- voiceover: "AFS Sentinel. Peringatan dini, sebelum terlambat."
- duration: 7.048s
- transition_in: blur-crossfade
- status: animated
- src: compositions/frames/09-outro.html
- type: brand_outro
- persuasion: Future pacing
- beat: confidence + urgency-to-act
- blueprint: titlecard-reveal
- focal:
- roles:
- sfx: none
- asset_candidates:

Adapt: keep the calm "one clean title, one restrained move, still hold" signature; extended with a footer credit line and the mandatory disclaimer. Centered layout.
Scene 1 (0.0–2.2s): on "AFS Sentinel" (0.4s) the same ring mark from Frame 3 (already drawn) + wordmark "AFS Sentinel" slide-up crossfade in, centered, ~50% frame width.
Scene 2 (2.27–4.5s): on "Peringatan dini, sebelum terlambat" tagline "peringatan dini, sebelum terlambat." reveals per-word in h2 lowercase; "sebelum terlambat." in fire-orange red.
Scene 3 (4.5–6.5s): mono footer line fades up above the caption band: "POWERED BY SECTORS API · SECTORS HACKATHON 2026 · TRACK 2 — AUTOMATION & WORKFLOWS"; under it caption-size cream-hint disclaimer "Alat analisis & informasi, bukan nasihat investasi."; hold still.
Scene 4 (6.5–7.05s): final exit — whole frame fades to #0E1920 black-ink (the only real exit in the video).

narrativeRole: Tutup dengan nama, janji, sumber data, dan disclaimer wajib.
keyMessage: Ingat namanya.
