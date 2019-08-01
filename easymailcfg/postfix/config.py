#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

from pathlib import Path
from typing import List
from typing import Dict
from typing import Tuple
from typing import Union

locations: List[Path] = [
    Path('/etc/postfix/main.cf'),
]


def get_config_location() -> Path:
    for location in locations:
        if location.is_file():
            return location
    raise OSError(2, 'No such file or directory', 'main.cf')


def get_config_contents() -> List[str]:
    with open(get_config_location().resolve()) as f:
        return f.read().splitlines()


def put_config_contents(cont: Union[str, List[str]]) -> None:
    if not isinstance(cont, str):
        cont = '\n'.join(cont)
    while '\n\n\n' in cont:
        cont = cont.replace('\n\n\n', '\n\n')
    get_config_location().resolve().write_text(cont.strip()+'\n')


def _parse() -> Dict[str, Tuple[int, str]]:
    config_fl: List[str] = get_config_contents()
    config: Dict[str, Tuple[int, str]] = dict()
    for lineno, expression in enumerate(config_fl):
        if expression.startswith('#'):
            continue
        if len(expression.strip()) < 1:
            continue
        setting, value = list(map(str.strip, expression.split('=', maxsplit=1)))
        if setting == '' or value == '':
            continue
        config[setting] = (lineno, value)
    return config


def parse() -> Dict[str, str]:
    return dict(map(lambda entry: (entry[0], entry[1][1]), _parse().items()))


def update(new_config: Dict[str, str]) -> None:
    old_config: Dict[str, Tuple[int, str]] = dict()
    try:
        old_config = _parse()
    except BaseException:
        pass
    config_raw: List[str] = get_config_contents()
    for key, val in new_config.items():
        old_line, old_val = old_config.get(key, (None, '',))
        line_fmtd = ""
        if val is not None or val != '':
            line_fmtd = "{0} = {1}".format(key, val)
        if val != old_val[1]:
            if old_line is not None:
                config_raw[old_line] = line_fmtd
            else:
                config_raw.append(line_fmtd)
    put_config_contents(config_raw)
