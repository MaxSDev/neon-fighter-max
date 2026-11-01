"""Audio preferences only. No training or gameplay progress is persisted."""

import configparser
import math
from pathlib import Path

DEFAULT_PREFERENCES = Path(__file__).resolve().parents[1] / 'settings' / 'audio.ini'


def load_audio_preferences(path):
    values = {'music_volume': 0.30, 'effects_volume': 0.65, 'muted': False}
    if path is None:
        return values
    parser = configparser.ConfigParser()
    try:
        path = Path(path)
        if not path.exists() or path.stat().st_size > 8192:
            return values
        parser.read_string(path.read_text(encoding='utf-8'))
        for key in ('music_volume', 'effects_volume'):
            number = parser.getfloat('audio', key, fallback=values[key])
            if math.isfinite(number):
                values[key] = max(0, min(1, number))
        values['muted'] = parser.getboolean('audio', 'muted', fallback=False)
    except (OSError, ValueError, UnicodeError, configparser.Error):
        pass
    return values


def save_audio_preferences(path, music, effects, muted):
    if path is None:
        return True
    parser = configparser.ConfigParser()
    parser['audio'] = {'music_volume': f'{music:.3f}', 'effects_volume': f'{effects:.3f}', 'muted': str(muted)}
    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix('.ini.tmp')
        with temporary.open('w', encoding='utf-8') as output:
            parser.write(output)
        temporary.replace(path)
        return True
    except OSError:
        return False
