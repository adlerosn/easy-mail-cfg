#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

from CloudFlare import CloudFlare
from ..configurator import Configurator
from typing import List, Optional
from typing import Dict
from typing import Tuple


class CloudFlareConfigurator(Configurator):
    def _needs(self) -> List[str]:
        return [
            'domains',
            'dkim_keys',
            'cf_api',
            'vm_ips',
            'dmarc_mail',
            'secondary',
        ]

    def _work(
        self,
        domains: List[str],
        dkim_keys: Dict[str, Dict[str, str]],
        cf_api: Tuple[str, str],
        vm_ips: Tuple[str, str],
        dmarc_mail: str,
        secondary: Tuple[str, Optional[str], Optional[str]],
    ) -> None:
        cf: CloudFlare = CloudFlare(email=cf_api[0], token=cf_api[1])
        zones: List[Dict[str, str]] = cf.zones.get(params={'per_page': 100})
        ip4, ip6 = vm_ips
        for zone in zones:
            zone_name: str = zone['name']
            if zone_name not in domains:
                continue
            zone_id: str = zone['id']
            dns_records: List[Dict[str, str]
                              ] = cf.zones.dns_records.get(zone_id)
            # print(zone_name)
            # for dns_record in dns_records:
            #     print(dns_record)
            # DKIM records
            dkim_key_dict: Dict[str, str] = dkim_keys[zone_name]
            needs_adding_key = [True, True]
            dkim_key: str = "v={0}; k={1}; p={2}".format(
                dkim_key_dict['v'], dkim_key_dict['k'], dkim_key_dict['p'])
            for wild in range(2):
                for dns_record in dns_records:
                    if dns_record['type'] != 'TXT' or not dns_record['name'].endswith('._domainkey.'+('*.'*wild)+zone_name):
                        continue
                    existing_key: str = dns_record['content']
                    if dkim_key == existing_key:
                        needs_adding_key[wild] = False
                    else:
                        dns_record_id: str = dns_record['id']
                        cf.zones.dns_records.delete(zone_id, dns_record_id)
                if needs_adding_key[wild]:
                    new_record: Dict[str, str] = {
                        'name': 'mail._domainkey.'+('*.'*wild)+zone_name,
                        'type': 'TXT',
                        'content': dkim_key,
                    }
                    cf.zones.dns_records.post(zone_id, data=new_record)
            # No CAAs or CNAMEs
            for dns_record in dns_records:
                if dns_record['type'] in ['CAA', 'CNAME']:
                    cf.zones.dns_records.delete(zone_id, dns_record['id'])
            # A and AAAA records
            sec_a_records_matrix = [[False, False], [False, False]]
            a_records_matrix = [[False, False], [False, False]]
            for dns_record in dns_records:
                if dns_record['type'] not in ['A', 'AAAA']:
                    continue
                expectedContent = ip4 if dns_record['type'] == 'A' else ip6
                expectedContentSecondary = secondary[1] if dns_record['type'] == 'A' else secondary[2]
                if dns_record['content'] == expectedContent:
                    a_records_matrix[int(dns_record['type'] == 'A')][int(
                        dns_record['name'].startswith('*.'))] = True
                elif dns_record['name'] in [zone_name, '*.'+zone_name]:
                    a_records_matrix[int(dns_record['type'] == 'A')][int(
                        dns_record['name'].startswith('*.'))] = True
                    new_record = {
                        'id': dns_record['id'],
                        'name': dns_record['name'],
                        'type': dns_record['type'],
                        'content': expectedContent,
                    }
                    cf.zones.dns_records.put(
                        zone_id, dns_record['id'], data=new_record)
                elif expectedContentSecondary is not None and dns_record['name'] in [f'{secondary[0]}.{zone_name}', f'*.{secondary[0]}.{zone_name}']:
                    sec_a_records_matrix[int(dns_record['type'] == 'A')][int(
                        dns_record['name'].startswith('*.'))] = True
                    if dns_record['content'] != expectedContentSecondary:
                        new_record = {
                            'id': dns_record['id'],
                            'name': dns_record['name'],
                            'type': dns_record['type'],
                            'content': expectedContent,
                        }
                        cf.zones.dns_records.put(
                            zone_id, dns_record['id'], data=new_record)
                else:
                    cf.zones.dns_records.delete(zone_id, dns_record['id'])
            for v4t_v6f, k in enumerate(a_records_matrix):
                v4t_v6f = bool(v4t_v6f)
                for wild, created in enumerate(k):
                    wild = bool(wild)
                    if not created:
                        cf.zones.dns_records.post(zone_id, data={
                            'name': (int(wild)*'*.')+zone_name,
                            'type': 'A' if v4t_v6f else 'AAAA',
                            'content': ip4 if v4t_v6f else ip6,
                        })
            for v4t_v6f, k in enumerate(sec_a_records_matrix):
                v4t_v6f = bool(v4t_v6f)
                for wild, created in enumerate(k):
                    wild = bool(wild)
                    expectedContentSecondary = secondary[1] if v4t_v6f else secondary[2]
                    if not created and expectedContentSecondary is not None:
                        cf.zones.dns_records.post(zone_id, data={
                            'name': (int(wild)*'*.')+secondary[0]+'.'+zone_name,
                            'type': 'A' if v4t_v6f else 'AAAA',
                            'content': expectedContentSecondary,
                        })
            # DMARC records
            dmarc_okays = [False, False]
            dmarc_value = 'v=DMARC1; p=reject; rua=mailto:' + dmarc_mail
            for wild, dmarc_okay in enumerate(dmarc_okays):
                for dns_record in dns_records:
                    if dns_record['type'] != 'TXT' or dns_record['name'] != '_dmarc.'+('*.'*wild)+zone_name:
                        continue
                    if dns_record['content'] == dmarc_value:
                        dmarc_okay = True
                    else:
                        dmarc_okay = True
                        new_record = {
                            'id': dns_record['id'],
                            'name': dns_record['name'],
                            'type': dns_record['type'],
                            'content': dmarc_value,
                        }
                        cf.zones.dns_records.put(
                            zone_id, dns_record['id'], data=new_record)
                if not dmarc_okay:
                    new_record: Dict[str, str] = {
                        'name': '_dmarc.'+('*.'*wild)+zone_name,
                        'type': 'TXT',
                        'content': dmarc_value,
                    }
                    cf.zones.dns_records.post(zone_id, data=new_record)
                # print(dmarc_value)
            # SPF records
            spf_okays = [False, False]
            spf_value = 'v=spf1 ip4:'+ip4+' ip6:'+ip6+' a mx -all'
            for wild, spf_okay in enumerate(spf_okays):
                for dns_record in dns_records:
                    if dns_record['type'] != 'TXT' or dns_record['name'] != ('*.'*wild)+zone_name:
                        continue
                    if dns_record['content'] == spf_value:
                        spf_okay = True
                    else:
                        spf_okay = True
                        new_record = {
                            'id': dns_record['id'],
                            'name': dns_record['name'],
                            'type': dns_record['type'],
                            'content': spf_value,
                        }
                        cf.zones.dns_records.put(
                            zone_id, dns_record['id'], data=new_record)
                if not spf_okay:
                    new_record: Dict[str, str] = {
                        'name': ('*.'*wild)+zone_name,
                        'type': 'TXT',
                        'content': spf_value,
                    }
                    cf.zones.dns_records.post(zone_id, data=new_record)
            # MX records
            mx_okays = [False, False]
            for dns_record in dns_records:
                if dns_record['type'] != 'MX':
                    continue
                if dns_record['name'] not in [zone_name, '*.'+zone_name]:
                    cf.zones.dns_records.delete(zone_id, dns_record['id'])
                    continue
                mx_okays[int(dns_record['name'].startswith('*.'))] = True
                if dns_record['content'] == zone_name:
                    continue
                new_record = {
                    'id': dns_record['id'],
                    'name': dns_record['name'],
                    'type': dns_record['type'],
                    'priority': 1,
                    'content': zone_name,
                }
                cf.zones.dns_records.put(
                    zone_id, dns_record['id'], data=new_record)
            for wild, is_okay in enumerate(mx_okays):
                wild = bool(wild)
                if not is_okay:
                    new_record: Dict[str, str] = {
                        'name': (int(wild)*'*.')+zone_name,
                        'type': 'MX',
                        'priority': 1,
                        'content': zone_name,
                    }
                    cf.zones.dns_records.post(zone_id, data=new_record)
