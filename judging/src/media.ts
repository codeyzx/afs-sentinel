// ─────────────────────────────────────────────────────────────────────────────
//  REKAMAN TIM
//
//  Biasanya TIDAK perlu diubah: taruh file bernama sesuai klip (SC04_CAM_Yahya.mp4)
//  di judging/public/recordings/ lalu `npm run sync` — file ditemukan otomatis.
//  (`npm run rekam` bahkan menyimpan & men-sync sendiri.)
//
//  Isi di sini hanya kalau nama filenya beda, contoh:  SC04_CAM_Yahya: "yahya-take3.mov",
//  null = pakai file yang ditemukan sync, atau placeholder kalau belum ada.
// ─────────────────────────────────────────────────────────────────────────────
export const RECORDINGS = {
  // Ais
  SC01_VO_Ais: null,
  SC02_CAM_Ais: null,
  SC05_CAM_Ais: null,
  SC07_CAM_Ais: null,
  SC08_CAM_Ais: null,
  SC10_CAM_Ais: null,
  SC10_ALL_Ais: null,

  // Yahya
  SC02_CAM_Yahya: null,
  SC04_CAM_Yahya: null,
  SC06_CAM_Yahya: null,
  SC09_CAM_Yahya: null,
  SC10_CAM_Yahya: null,
  SC10_ALL_Yahya: null,

  // Fathan
  SC02_CAM_Fathan: null,
  SC03_CAM_Fathan: null,
  SC07a_CAM_Fathan: null,
  SC07b_CAM_Fathan: null,
  SC10_CAM_Fathan: null,
  SC10_ALL_Fathan: null,
} satisfies Record<string, string | null>;

/** Optional: where the first word starts in a clip (seconds); overrides the detection of `npm run sync`. */
export const TRIM_START: Partial<Record<ClipId, number>> = {};

export type ClipId = keyof typeof RECORDINGS;

/** End card details. null = placeholder shown in the video. */
export const END_CARD = {
  github: null as string | null, // contoh: "github.com/jtktop10/afs-sentinel"
  app: "afs-sentinel-ee5d2e28af17.herokuapp.com",
};
