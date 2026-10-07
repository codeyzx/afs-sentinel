import type { ClipId } from "./media";

export type Person = "Ais" | "Yahya" | "Fathan";

export const PEOPLE: Record<Person, { role: string; full: string }> = {
  Fathan: { role: "Business Analyst", full: "Fathan" },
  Yahya: { role: "Developer", full: "Yahya" },
  Ais: { role: "Researcher", full: "Ais" },
};

export type Line = {
  /** Clips that play together for this line (more than one only for the group line). */
  clips: ClipId[];
  who: Person | "Bertiga";
  kind: "cam" | "vo";
  text: string;
  /** Target length in seconds; used until the real recording exists. */
  target: number;
  direction: string;
  /** Silence before this line starts (seconds). */
  gap?: number;
};

export type Reaction = { clip: ClipId; who: Person; text: string; target: number; direction: string };

export type SceneDef = {
  id: string;
  chapter: string;
  title: string;
  /** Seconds of visuals before the first line. */
  lead: number;
  /** Seconds held after the last line. */
  tail: number;
  lines: Line[];
  reactions?: Reaction[];
  proof?: string;
};

export const SCENES: SceneDef[] = [
  {
    id: "SC01",
    chapter: "Hook",
    title: "Hook",
    lead: 1.4,
    tail: 0.5,
    lines: [
      {
        clips: ["SC01_VO_Ais"],
        who: "Ais",
        kind: "vo",
        text: "Delapan Mei 2023. Bursa menghentikan perdagangan saham Waskita Karya. Sistem kami… sudah menandainya dua puluh lima bulan sebelumnya.",
        target: 10.8,
        direction: "Suara saja. Pelan, berat. Jeda panjang setelah “Waskita Karya”.",
      },
    ],
  },
  {
    id: "SC02",
    chapter: "Masalah",
    title: "Perkenalan & masalah",
    lead: 0.6,
    tail: 0.4,
    lines: [
      {
        clips: ["SC02_CAM_Fathan"],
        who: "Fathan",
        kind: "cam",
        text: "Halo, Juri! Kami JTKTOP10. Saya Fathan, ini Yahya, developer kami, dan Ais, researcher. Masalahnya: tanda bahaya itu sudah ada di laporan keuangan, tapi tidak ada analis yang sempat membedah ratusan laporan setiap kuartal.",
        target: 16,
        direction: "Energik di awal, serius mulai “Masalahnya:”. Beri jeda kecil setelah “Yahya” dan “Ais”.",
      },
    ],
    reactions: [
      { clip: "SC02_CAM_Yahya", who: "Yahya", text: "(melambai ke kamera)", target: 3, direction: "Diam, senyum, lalu melambai. Santai." },
      { clip: "SC02_CAM_Ais", who: "Ais", text: "(mengangguk ke kamera)", target: 3, direction: "Diam, senyum, lalu mengangguk." },
    ],
  },
  {
    id: "SC03",
    chapter: "Solusi",
    title: "Solusi & target audiens",
    lead: 0.4,
    tail: 0.6,
    lines: [
      {
        clips: ["SC03_CAM_Fathan"],
        who: "Fathan",
        kind: "cam",
        text: "AFS Sentinel kami bangun untuk analis riset dan investor saham BEI. Ia memindai 33 emiten non-keuangan secara otomatis, lalu hanya melaporkan yang perlu diperiksa. Analis tidak perlu lagi mencari, tinggal memutuskan.",
        target: 14.8,
        direction: "Persuasif.",
      },
    ],
  },
  {
    id: "SC04",
    chapter: "Otomasi",
    title: "Otomasi",
    proof: "Bukti wajib #1",
    lead: 0.6,
    tail: 0.4,
    lines: [
      {
        clips: ["SC04_CAM_Yahya"],
        who: "Yahya",
        kind: "cam",
        text: "Ini jantung otomasinya. Heroku Scheduler memicu pipeline setiap pagi jam delapan WIB, dan pipeline sendiri yang menentukan kapan jatuh tempo: tiga hari sejak run sukses terakhir. Tanpa tombol, tanpa manusia. Data Sectors API disimpan permanen di Postgres, jadi kuartal yang sama tidak pernah dibayar dua kali.",
        target: 21,
        direction: "Tenang, jelas. Tekankan “tanpa tombol, tanpa manusia”.",
      },
    ],
  },
  {
    id: "SC05",
    chapter: "Mesin",
    title: "Mesin forensik",
    lead: 0.5,
    tail: 0.5,
    lines: [
      {
        clips: ["SC05_CAM_Ais"],
        who: "Ais",
        kind: "cam",
        text: "Mesinnya enam Forensic Rule yang deterministik. Tiga inti: Sloan Accrual, divergensi laba dan kas, dan Altman Z. Ditambah Beneish, penjualan orang dalam, dan laba tanpa dividen. Semuanya digabung menjadi satu skor risiko, nol sampai seratus.",
        target: 16.8,
        direction: "Yakin. Hitung pakai jari (jari masuk frame).",
      },
    ],
  },
  {
    id: "SC06",
    chapter: "Alert",
    title: "Alert Telegram",
    lead: 1.0,
    tail: 0.7,
    lines: [
      {
        clips: ["SC06_CAM_Yahya"],
        who: "Yahya",
        kind: "cam",
        text: "Begitu skor menembus ambang, Analyst langsung menerima ini di Telegram: tingkat keparahan, skor, dan tiga temuan teratas dalam bahasa awam. Satu klik di ‘Buka Incident’…",
        target: 11.5,
        direction: "Sedikit mendesak. Akhir kalimat menggantung (dioper ke Fathan).",
      },
    ],
  },
  {
    id: "SC07",
    chapter: "Incident",
    title: "Halaman incident",
    lead: 0.3,
    tail: 0.5,
    lines: [
      {
        clips: ["SC07a_CAM_Fathan"],
        who: "Fathan",
        kind: "cam",
        text: "…dan kita langsung masuk ke halaman bukti. Vonisnya di atas. Setiap kartu bukti bisa dibuka: rumusnya, angka mentahnya, sampai endpoint Sectors asalnya. Grafik ini menunjukkan laba naik, tapi kas operasi tertinggal.",
        target: 14.5,
        direction: "Menyambung kalimat Yahya. Lancar, menunjukkan.",
      },
      {
        clips: ["SC07_CAM_Ais"],
        who: "Ais",
        kind: "cam",
        text: "Ringkasan AI hanya menceritakan angka yang sudah dihitung. AI tidak pernah mengubah skor.",
        target: 5.5,
        direction: "Menekankan “tidak pernah”.",
        gap: 0.4,
      },
      {
        clips: ["SC07b_CAM_Fathan"],
        who: "Fathan",
        kind: "cam",
        text: "Setelah ditelaah, analis tinggal menandai: sedang diperiksa.",
        target: 4.2,
        direction: "Datar, yakin.",
        gap: 0.4,
      },
    ],
  },
  {
    id: "SC08",
    chapter: "Backtest",
    title: "Backtest",
    lead: 0.4,
    tail: 0.5,
    lines: [
      {
        clips: ["SC08_CAM_Ais"],
        who: "Ais",
        kind: "cam",
        text: "Tapi apakah ini benar-benar bekerja? Kami putar ulang keenam rule ke kuartal historis. Waskita: pertama kali level Sedang di 2021-Q1, dua puluh lima bulan sebelum suspensi. Sritex: empat puluh dua bulan sebelum pailit. Kalimat klaim ini dihasilkan oleh sistem, bukan kami tulis tangan.",
        target: 20,
        direction: "Retoris di awal, tegas di angka 25 dan 42.",
      },
    ],
  },
  {
    id: "SC09",
    chapter: "Log",
    title: "Log run",
    proof: "Bukti wajib #2",
    lead: 0.4,
    tail: 0.5,
    lines: [
      {
        clips: ["SC09_CAM_Yahya"],
        who: "Yahya",
        kind: "cam",
        text: "Dan ini bukti eksekusi tanpa pengawasan: riwayat Audit Run. Label ‘Otomatis · sistem’ berarti dipicu scheduler, tidak disentuh siapa pun, lengkap dengan timestamp, jumlah emiten, dan kredit API. Setiap run juga melapor ke Telegram, termasuk saat hasilnya nol.",
        target: 17.5,
        direction: "Mantap.",
      },
    ],
  },
  {
    id: "SC10",
    chapter: "Penutup",
    title: "Penutup",
    lead: 0.3,
    tail: 1.0,
    lines: [
      {
        clips: ["SC10_CAM_Fathan"],
        who: "Fathan",
        kind: "cam",
        text: "Laporan keuangan sudah memberi peringatan. AFS Sentinel memastikan ada yang membacanya, tepat waktu.",
        target: 6.8,
        direction: "Pelan, meyakinkan.",
      },
      { clips: ["SC10_CAM_Ais"], who: "Ais", kind: "cam", text: "Terukur, bisa dilacak…", target: 2, direction: "Menggantung, oper ke Yahya.", gap: 0.2 },
      { clips: ["SC10_CAM_Yahya"], who: "Yahya", kind: "cam", text: "…dan berjalan sendiri.", target: 2, direction: "Menutup kalimat Ais.", gap: 0.1 },
      {
        clips: ["SC10_ALL_Fathan", "SC10_ALL_Yahya", "SC10_ALL_Ais"],
        who: "Bertiga",
        kind: "cam",
        text: "AFS Sentinel. Peringatan dini, sebelum terlambat.",
        target: 3.5,
        direction: "Tatap kamera, ucapkan serempak sambil senyum. Mulai bicara 1 detik setelah tombol rekam.",
        gap: 0.3,
      },
    ],
  },
];
