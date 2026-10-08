// Extends the music bed so its natural ending lands on the last frame of the outro.
// The bed moves in 4 s phrases; we repeat SHIFT seconds of it (a multiple of 4, so the beat
// stays on phase) with a short crossfade in the middle of a phrase.
// Usage: node scripts/bed-long.mjs   (re-run when INTRO/OUTRO or the scene lengths change)
import { execFileSync } from "node:child_process";

const SRC = "public/audio/bgm/bed.mp3";
const OUT = "public/audio/bgm/bed-long.mp3";
const SPLICE = 127.1; // seconds into the bed, between two phrase peaks
const SHIFT = 16; // seconds repeated; the music's fade (orig. ~169–173 s) now lands at the end of the outro
const X = 0.25; // half the crossfade

const a = `[0]atrim=0:${SPLICE + X},afade=t=out:st=${SPLICE - X}:d=${2 * X}[a]`;
const b = `[0]atrim=start=${SPLICE - SHIFT - X},asetpts=PTS-STARTPTS,afade=t=in:d=${2 * X},adelay=${Math.round((SPLICE - X) * 1000)}:all=1[b]`;
execFileSync("ffmpeg", ["-v", "error", "-y", "-i", SRC, "-filter_complex", `${a};${b};[a][b]amix=inputs=2:normalize=0:duration=longest`, "-c:a", "libmp3lame", "-b:a", "192k", OUT], { stdio: "inherit" });
console.log(`${OUT} siap`);
