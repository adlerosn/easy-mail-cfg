#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

from .config import update as cfg_update_applier
from ..configurator import Configurator
from typing import List


class PostfixConfigurator(Configurator):
    def _needs(self) -> List[str]:
        return [
            'domains',
        ]

    def _work(self, domains: List[str]) -> None:
        cfg_patch = {
            'milter_protocol': '2',
            'milter_default_action': 'accept',
            'smtpd_milters': 'inet:localhost:12301',
            'non_smtpd_milters': 'inet:localhost:12301',
        }
        cfg_update_applier(cfg_patch)
        cfg_update_applier({
            'mydestination': ', '.join([
                '$myhostname',
                'localhost',
                'localhost.$mydomain',
                *sorted(domains),
            ])
        })
