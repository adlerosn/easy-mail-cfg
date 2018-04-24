#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

from pathlib import Path
from .configurator import Configurator
from .postfix import PostfixConfigurator
from .opendkim import OpenDkimConfigurator
from .cloudflare import CloudFlareConfigurator


def main() -> None:
    cf_mail, cf_token, *domains = list(map(str.split, Path('/srv/easymail.cfg').read_text().splitlines()))
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
