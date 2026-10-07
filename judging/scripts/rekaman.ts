// Generates REKAMAN.md (the team's recording checklist) from src/script.ts.
// Usage: node scripts/rekaman.ts
import { writeFileSync } from "node:fs";
import { SCENES, type Person } from "../src/script.ts";
import { phraseGroups, scheduleWords } from "../src/words.ts";

type Row = { file: string; scene: string; text: string; target: number; direction: string; kind: string };
const byPerson: Record<Person, Row[]> = { Fathan: [], Ais: [], Yahya: [] };

for (const s of SCENES) {
  for (const l of s.lines) {
    for (const clip of l.clips) {
      const who = l.who === "Bertiga" ? (clip.split("_").at(-1) as Person) : l.who;
      byPerson[who].push({ file: clip, scene: `${s.id} · ${s.title}`, text: l.text, target: l.target, direction: l.direction, kind: l.kind });
    }
  }
  for (const r of s.reactions ?? []) {
    byPerson[r.who].push({ file: r.clip, scene: `${s.id} · ${s.title}`, text: r.text, target: r.target, direction: r.direction, kind: "cam" });
  }
}

const out: string[] = [
  "# Daftar rekaman — Video Judging AFS Sentinel",
  "",
  "> Dibuat otomatis dari `src/script.ts` (`npm run checklist`). Ubah naskah di sana, bukan di sini.",
  "",
  "Semua visual, rekaman layar produk, Telegram, musik, SFX, dan subtitle sudah ada di video.",
  "Yang kurang hanya **wajah + suara** kalian.",
  "",
  "## Cara A (disarankan): kamera laptop + perekam bawaan",
  "",
  "Prompter dan perekam jadi satu halaman: rekaman mulai tepat bersama prompter, file langsung bernama benar.",
  "",
  "1. Butuh: folder `judging/` dari repo + Node.js (versi 18 ke atas) + Chrome/Edge. **Tidak perlu `npm install`.**",
  "2. Di folder `judging/`, jalankan `npm run rekam` → browser terbuka di `http://localhost:4747` (izinkan kamera & mic).",
  "3. Pilih nama kalian (Fathan / Ais / Yahya), pilih klip, cek posisi wajah di preview, lalu tekan **Spasi**.",
  "4. Layar penuh: hitung mundur 3-2-1 → **langsung baca kata yang menyala kuning**. Teks ada di atas layar, dekat kamera.",
  "5. Muncul **TAHAN DIAM** → tetap menatap kamera; rekaman berhenti sendiri.",
  "6. Tonton ulang → **Enter** simpan, **R** ulangi. File masuk ke `public/recordings/` dengan nama yang benar;",
  "   take lama otomatis dipindah ke `public/recordings/_old/`. Halaman memberi tahu kalau tempo kalian terlalu cepat/lambat.",
  "7. Selesai semua klip → kirim isi `public/recordings/` (tanpa `_old/`) ke editor.",
  "",
  "Tips: pilih mic earphone/eksternal di dropdown kalau ada (mic laptop menangkap kipas). Tinggikan laptop sampai kamera",
  "sejajar mata. Esc membatalkan take.",
  "",
  "## Cara B: kamera HP + video prompter",
  "",
  "Video prompter per klip ada di `out/prompter/<Fathan|Ais|Yahya>/` (`npm run prompter`), daftar putarnya `out/prompter/index.html`.",
  "Pasang HP tepat di atas layar laptop, pakai earphone satu telinga (bip hitung mundur jangan masuk mic), **mulai rekam di HP",
  "dulu** baru putar prompter, baca kata yang menyala, tahan diam di akhir. Simpan dengan nama file persis seperti tabel.",
  "iPhone: Settings → Camera → Formats → Most Compatible.",
  "",
  "Kenapa harus ikut prompter: zoom, stabilo, lingkaran merah, dan subtitle di video dipicu oleh kata yang sama dengan",
  "kata yang menyala di prompter. Kalau tempo kalian sama dengan prompter, semua efek jatuh tepat di kata yang diucapkan.",
  "",
  "## Aturan rekam",
  "",
  "- **Kamera**: landscape, 720p ke atas. Wajah di tengah (kotak kuning di preview), sisakan ruang di atas kepala — akan di-crop jadi kotak potret.",
  "- **Cahaya**: jendela/lampu di depan wajah, bukan di belakang. Latar polos & rapi. Baju sama di semua klip.",
  "- **Suara**: ruangan sepi, HP/mic dekat mulut (±30 cm). Kalau ada mic clip-on, pakai.",
  "- **Arah mata**: ke lensa kamera; baca prompter dengan melirik sedikit ke bawah.",
  "- **Nama file** (cara B): persis seperti tabel, ekstensi bebas (`.mp4`/`.mov`/`.webm`; suara saja boleh `.wav`/`.m4a`).",
  "",
];
for (const who of ["Fathan", "Ais", "Yahya"] as Person[]) {
  const rows = byPerson[who];
  out.push(`## ${who} — ${rows.length} klip`, "", "| File | Prompter | Scene | Durasi | Ucapkan | Arahan |", "|---|---|---|---|---|---|");
  for (const r of rows) {
    const kind = r.kind === "vo" ? " (suara saja)" : "";
    out.push(`| \`${r.file}\`${kind} | \`${who}/PROMPT_${r.file}.mp4\` | ${r.scene} | ±${r.target} dtk | ${r.text.replace(/\|/g, "\\|")} | ${r.direction} |`);
  }
  out.push("");
}
out.push(
  "## Untuk editor: memasukkan rekaman",
  "",
  "1. Taruh semua file di `judging/public/recordings/` (nama = nama klip, ekstensi bebas).",
  "2. `npm run sync` — menemukan file dari namanya, mengonversi HEVC/WebM ke MP4 (asli ke `_raw/`), dan mendeteksi",
  "   kapan bicara mulai & selesai (hitung mundur dan diam di awal/akhir terpotong sendiri). Butuh ffmpeg.",
  "3. `npm run dev` untuk cek di Remotion Studio, `npm run render` untuk hasil akhir (`out/judging.mp4`).",
  "",
  "Kalau deteksi meleset di satu klip, isi `TRIM_START` di `src/media.ts` (detik saat kata pertama diucapkan).",
  "Nama file berbeda? Tulis di `RECORDINGS` di `src/media.ts`.",
  "",
);
writeFileSync(new URL("../REKAMAN.md", import.meta.url), out.join("\n"));
console.log("REKAMAN.md written");

// Clip list for the browser recorder (scripts/rekam.mjs) and `npm run sync`: plain JSON, no TS needed there.
const clips = (["Fathan", "Ais", "Yahya"] as Person[]).flatMap((who) =>
  byPerson[who].map((r) => {
    const reaction = r.text.startsWith("(");
    const words = reaction ? [] : scheduleWords(r.text, r.target);
    const groups = phraseGroups(words).map((g) => g.map((w) => words.indexOf(w)));
    return {
      clip: r.file,
      who,
      scene: r.scene,
      kind: reaction ? "reaction" : r.kind,
      text: r.text,
      direction: r.direction,
      target: r.target,
      words: words.map((w) => ({ text: w.text, start: +w.start.toFixed(3), end: +w.end.toFixed(3) })),
      groups,
    };
  }),
);
writeFileSync(new URL("../src/generated/prompter.json", import.meta.url), JSON.stringify({ countdown: 3, hold: 2, clips }, null, 1) + "\n");
console.log(`src/generated/prompter.json: ${clips.length} klip`);
