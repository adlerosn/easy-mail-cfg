#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

from pathlib import Path
from .configurator import Configurator
from .postfix import PostfixConfigurator
from .opendkim import OpenDkimConfigurator
from .cloudflare import CloudFlareConfigurator


def main() -> None:
    inputfile: Path = Path('/srv/easymail.cfg')
    if not inputfile.is_file():
        raise FileNotFoundError(inputfile)
    cf_mail, cf_token, *domains = list(map(str.strip, inputfile.read_text().splitlines()))
    Configurator.configure_many(
        [
            CloudFlareConfigurator,
            OpenDkimConfigurator,
            PostfixConfigurator,
        ], {
            'domains': domains,
            'cf_api': (cf_mail, cf_token,),
        }
    )
