#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

from .config import update as cfg_update_applier
from .config import update_default as cfg_overrided_update_applier
from ..configurator import Configurator
from typing import List
from typing import Dict
from typing import Tuple
from typing import Match
from typing import Optional
from pathlib import Path
import subprocess
import shutil
import re
import os


class OpenDkimConfigurator(Configurator):
    def _needs(self) -> List[str]:
        return [
            'domains',
        ]

    def _provides(self) -> List[str]:
        return [
            'dkim_keys',
        ]

    def _work(self, domains: List[str]) -> Dict[str, Dict[str, Dict[str, str]]]:
        domains = sorted(domains)
        cfg_patch = {
            'AutoRestart': 'Yes',
            'AutoRestartRate': '10/1h',
            'UMask': '002',
            'Syslog': 'yes',
            'SyslogSuccess': 'Yes',
            'LogWhy': 'Yes',
            'Canonicalization': 'relaxed/simple',
            'ExternalIgnoreList': 'refile:/etc/opendkim/TrustedHosts',
            'InternalHosts': 'refile:/etc/opendkim/TrustedHosts',
            'KeyTable': 'refile:/etc/opendkim/KeyTable',
            'SigningTable': 'refile:/etc/opendkim/SigningTable',
            'Mode': 'sv',
            'PidFile': '/var/run/opendkim/opendkim.pid',
            'SignatureAlgorithm': 'rsa-sha256',
            'UserID': 'opendkim:opendkim',
            'Socket': 'inet:12301@localhost',
        }
        cfg_update_applier(cfg_patch)
        cfg_update_applier({'SubDomains': 'yes'})
        cfg_overrided_update_applier({'SOCKET': '"{0}"'.format(cfg_patch['Socket'])})
        odkim_path = Path('/etc/opendkim')
        if odkim_path.is_dir():
            shutil.rmtree(str(odkim_path))
        os.symlink('/etc/opendkim.conf', '/etc/opendkim/opendkim.conf')
        keys_path = Path(odkim_path, 'keys')
        keys_path.mkdir(parents=True, exist_ok=True)
        trusted_hosts_file = Path(odkim_path, 'TrustedHosts')
        key_table_file = Path(odkim_path, 'KeyTable')
        signing_table_file = Path(odkim_path, 'SigningTable')
        trusted_hosts_file.write_text('\n'.join([
            '127.0.0.1', 'localhost', '192.168.0.1/24',
            *['*.{0}'.format(domain)
              for domain in domains
              ],
        ])+'\n')
        key_table_file.write_text('\n'.join([
            'mail._domainkey.{0} {0}:mail:/etc/opendkim/keys/{0}/mail.private'.format(domain)
            for domain in domains
        ])+'\n')
        signing_table_file.write_text('\n'.join([
            *['*@{0} mail._domainkey.{0}'.format(domain)
                for domain in domains
              ],
            *['*@*.{0} mail._domainkey.{0}'.format(domain)
                for domain in domains
              ],
        ])+'\n')
        dkim_keys: Dict[str, Dict[str, str]] = dict()
        for domain in domains:
            domainkeys_path = Path(keys_path, domain)
            domainkeys_path.mkdir(parents=True, exist_ok=True)
            command: List[str] = [
                'opendkim-genkey',
                '--selector=mail',
                '--directory='+str(domainkeys_path),
                '--domain='+str(domain),
                '--subdomains',
            ]
            subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            dns_record = Path(domainkeys_path, 'mail.txt').read_text().replace('\n', '').replace('\t', '')
            dns_optional_match: Optional[Match[str]] = re.search(r'"v=(\w+);.*k=(\w+);.*p=(.*)"', dns_record)
            if dns_optional_match is None:
                continue
            dns_match: Match[str] = dns_optional_match
            dns_parts: Tuple[str, ...] = tuple(dns_match.group(1, 2, 3))
            dns_dict: Dict[str, str] = {
                'v': dns_parts[0],
                'k': dns_parts[1],
                'p': dns_parts[2],
            }
            dkim_keys[domain] = dns_dict
        command = [
            'chown',
            'opendkim:opendkim',
            '-R',
            str(Path(odkim_path))
        ]
        subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        for domain in domains:
            domainkeys_path = Path(keys_path, domain)
            command = [
                'chmod',
                '0400',
                str(Path(domainkeys_path, 'mail.private'))
            ]
            subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        return {'dkim_keys': dkim_keys}
