import os

def ljspeech(root_path, meta_file, **kwargs):
    """Normalizes the LJSpeech metadata file to TTS format."""
    txt_file = os.path.join(root_path, meta_file)
    items = []
    speaker_name = "ljspeech"
    with open(txt_file, "r", encoding="utf-8") as ttf:
        for line in ttf:
            cols = line.split("|")
            if len(cols) < 3:
                print(f"Skipping row due to insufficient columns: {line.strip()}")
                continue
            wav_file = os.path.join(root_path, "wavs", cols[0] + ".wav")
            text = cols[2]
            items.append({"text": text, "audio_file": wav_file, "speaker_name": speaker_name, "root_path": root_path})
    return items