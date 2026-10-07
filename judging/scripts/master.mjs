// Loudness-master a render for YouTube: two-pass EBU R128 loudnorm to -14 LUFS, true peak -1 dB.
// The video stream is copied untouched.
// Usage: node scripts/master.mjs [in=out/judging.mp4] [out=out/judging-final.mp4]
import { execFileSync, spawnSync } from "node:child_process";

// flags meant for `remotion render` (npm run render -- --flag) land here too; ignore them
const [input = "out/judging.mp4", output = "out/judging-final.mp4"] = process.argv.slice(2).filter((a) => !a.startsWith("--"));
const TARGET = "I=-14:TP=-1.0:LRA=11";

// pass 1: measure
const measure = spawnSync("ffmpeg", ["-hide_banner", "-i", input, "-af", `loudnorm=${TARGET}:print_format=json`, "-f", "null", "-"], { encoding: "utf8", maxBuffer: 1 << 26 });
const json = JSON.parse(measure.stderr.slice(measure.stderr.lastIndexOf("{"), measure.stderr.lastIndexOf("}") + 1));
console.log(`terukur: ${json.input_i} LUFS, true peak ${json.input_tp} dB`);

// pass 2: apply with the measured values (linear when possible, so dynamics are kept)
const af =
  `loudnorm=${TARGET}:measured_I=${json.input_i}:measured_TP=${json.input_tp}:measured_LRA=${json.input_lra}` +
  `:measured_thresh=${json.input_thresh}:offset=${json.target_offset}:linear=true`;
execFileSync("ffmpeg", ["-v", "error", "-y", "-i", input, "-c:v", "copy", "-af", af, "-ar", "48000", "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart", output], { stdio: "inherit" });

const check = spawnSync("ffmpeg", ["-hide_banner", "-nostats", "-i", output, "-af", "ebur128=peak=true", "-f", "null", "-"], { encoding: "utf8", maxBuffer: 1 << 26 });
const tail = check.stderr.slice(check.stderr.lastIndexOf("Summary:"));
console.log(`${output}: ${tail.match(/I:\s+(-?[\d.]+) LUFS/)?.[1]} LUFS, true peak ${tail.match(/Peak:\s+(-?[\d.]+) dBFS/)?.[1]} dBFS`);
