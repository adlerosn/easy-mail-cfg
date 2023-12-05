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
    (cf_mail,
     cf_token,
     dmarc_mail,
     vm_ip4,
     vm_ip6,
     *domains) = list(map(str.strip, inputfile.read_text().splitlines()))
    sec4file = Path('/srv/secondary.4.cfg')
    sec6file = Path('/srv/secondary.6.cfg')
    sec4, sec6 = None, None
    if sec4file.is_file() and sec6file.is_file():
        sec4 = sec4file.read_text().strip().split(' ')[0].strip()
        sec6 = sec6file.read_text().strip().split(' ')[0].strip()
    Configurator.configure_many(
        [
            CloudFlareConfigurator,
            OpenDkimConfigurator,
            PostfixConfigurator,
        ], {
            'domains': domains,
            'cf_api': (cf_mail, cf_token,),
            'dmarc_mail': dmarc_mail,
            'vm_ips': (vm_ip4, vm_ip6),
            'secondary': ('secondary', sec4, sec6),
        }
    )
