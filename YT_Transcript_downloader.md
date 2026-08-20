### WSL Linux
```bash
yt-dlp --write-auto-sub --sub-lang de --skip-download "https://www.youtube.com/watch?v=5wQ3JU_IqzU"
```

```python
import re

with open("your_file.vtt", "r", encoding="utf-8") as f:
    content = f.read()

# Split into cue blocks
blocks = content.strip().split("\n\n")

lines_seen = []
last_clean = ""

for block in blocks:
    lines = block.strip().split("\n")
    # Skip WEBVTT header block
    if not lines or lines[0].startswith("WEBVTT") or lines[0].startswith("Kind"):
        continue
    for line in lines:
        # Skip timestamp lines and empty lines
        if "-->" in line or line.strip() == "" or line.strip() == " ":
            continue
        # Strip inline timing tags like <00:00:01.234><c>
        clean = re.sub(r'<[^>]+>', '', line).strip()
        if clean and clean != last_clean:
            lines_seen.append(clean)
            last_clean = clean

# Remove consecutive duplicates (artifact of rolling word-by-word captions)
deduped = []
for line in lines_seen:
    if not deduped or line != deduped[-1]:
        deduped.append(line)

# Join into single string and collapse multiple spaces
transcript = " ".join(deduped)
transcript = re.sub(r' +', ' ', transcript)

print(transcript)
```