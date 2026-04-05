import pathlib
import wave

_wave_open = wave.open


def _path_supporting_wave_open(path, mode="rb", *args, **kwargs):
    if isinstance(path, pathlib.Path):
        path = str(path)
    return _wave_open(path, mode, *args, **kwargs)


wave.open = _path_supporting_wave_open
