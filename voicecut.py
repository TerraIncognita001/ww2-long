"""Pauses in the narration shortened SAMPLE-EXACT (ww2-bot v2.33 + v2.42, Nov 11: captions ran ahead of the voice).
- v2.42: ffmpeg's aselect drops whole decoded frames while the word times move by the exact cut length -> the voice
  and the captions drift apart from pause to pause (up to 0.86 s on the runner's ffmpeg 8). Here the audio is
  decoded to PCM, the sample ranges are dropped in Python and the rest is encoded again (error ~0.04 s).
- v2.33: Edge gives a word's start ~0.1 s early, so the first word after a pause often 'starts' inside the cut
  silence; the old shift skipped that cut and every sentence's captions came late. A word that starts inside a cut
  now starts where the cut ends.
Edge's word times are right on their own: don't rescale them, don't speak sentence by sentence, don't use Whisper
(all tried in ww2-bot, all worse). Insert silence the same way (samples), never with ffmpeg filters."""
import re
import subprocess

SR = 24000


def cut_audio(path, cuts, sr=SR):
    """Removes the (start, end) ranges in seconds exactly, sample by sample."""
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(path), "-f", "s16le", "-ac", "1", "-ar", str(sr),
                          "-"], capture_output=True, check=True).stdout
    n, out, prev = len(raw) // 2, [], 0
    for a, b in sorted(cuts):
        ia, ib = max(prev, min(n, round(a * sr))), max(prev, min(n, round(b * sr)))
        out.append(raw[2 * prev:2 * ia])
        prev = ib
    out.append(raw[2 * prev:])
    tmp = path.with_name(path.stem + "_cut.mp3")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ac", "1", "-ar", str(sr), "-i", "-",
                    "-c:a", "libmp3lame", "-b:a", "128k", str(tmp)], input=b"".join(out), check=True)
    tmp.replace(path)


def calm_pauses(path, words, keep=0.75):
    """Removes the silence before the first word and shortens pauses longer than `keep` (a documentary keeps its
    breaths); words = [(text, start_s, ...)] from Edge's WordBoundary -> the same list on the new timeline."""
    log = subprocess.run(["ffmpeg", "-i", str(path), "-af", "silencedetect=noise=-40dB:d=0.05", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    pairs = list(zip([float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", log)],
                     [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]))
    cuts = [(a + keep / 2, b - keep / 2) for a, b in pairs if b - a > keep and a > 0.01]
    if pairs and pairs[0][0] <= 0.01 and pairs[0][1] > 0.04:       # silence at the start
        cuts.insert(0, (0.0, pairs[0][1] - 0.02))
    if not cuts:
        return words
    cut_audio(path, cuts)
    shift = lambda t: t - sum(b - a if b <= t + 0.001 else max(0.0, t - a) for a, b in cuts if a < t)
    return [(w[0], max(0.0, shift(w[1])), *w[2:]) for w in words]
