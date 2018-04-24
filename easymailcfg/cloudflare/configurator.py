#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

from CloudFlare import CloudFlare
from ..configurator import Configurator
from typing import List
from typing import Dict
from typing import Tuple


class CloudFlareConfigurator(Configurator):
    def _needs(self) -> List[str]:
        return [
            'domains',
            'dkim_keys',
            'cf_api',
        ]

    def _work(self, domains: List[str], dkim_keys: Dict[str, Dict[str, str]], cf_api: Tuple[str, str]) -> None:
        cf: CloudFlare = CloudFlare(email=cf_api[0], token=cf_api[1])
        zones: List[Dict[str, str]] = cf.zones.get(params={'per_page': 100})
        for zone in zones:
            zone_name: str = zone['name']
            if zone_name not in domains:
                continue
            zone_id: str = zone['id']
            dns_records: List[Dict[str, str]] = cf.zones.dns_records.get(zone_id)
            dkim_key_dict: Dict[str, str] = dkim_keys[zone_name]
            dkim_key: str = "v={0}; k={1}; p={2}".format(dkim_key_dict['v'], dkim_key_dict['k'], dkim_key_dict['p'])
            needs_adding_key = True
            for dns_record in dns_records:
                if dns_record['type'] != 'TXT' or not dns_record['name'].endswith('._domainkey.'+zone_name):
                    continue
                existing_key: str = dns_record['content']
                if dkim_key == existing_key:
                    needs_adding_key = False
                else:
                    dns_record_id: str = dns_record['id']
                    cf.zones.dns_records.delete(zone_id, dns_record_id)
            if needs_adding_key:
                new_record: Dict[str, str] = {
                    'name': 'mail._domainkey.'+zone_name,
                    'type': 'TXT',
                    'content': dkim_key,
                }
                cf.zones.dns_records.post(zone_id, data=new_record)
