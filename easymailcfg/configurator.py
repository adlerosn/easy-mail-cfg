#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

from typing import List
from typing import Dict
from typing import Type
from typing import Tuple
from typing import Union
from typing import Optional

given_data_type = Dict[str, Union[List[str], Tuple[str, str], Dict[str, str]]]


def get_configuration_sequence(configurators_to_allocate: List['Configurator'], configurators_namespace: List[str]) -> List['Configurator']:
    configurators_in_sequence: List['Configurator'] = list()
    while len(configurators_to_allocate) > 0:
        found = False
        for cta in range(len(configurators_to_allocate)):
            cfgtr = configurators_to_allocate[cta]
            will_run = all(list(map(lambda need: need in configurators_namespace, cfgtr._needs())))
            if will_run:
                found = True
                configurators_to_allocate.remove(cfgtr)
                configurators_in_sequence.append(cfgtr)
                configurators_namespace = list(set([*configurators_namespace, *cfgtr._provides()]))
                break
        if not found:
            raise NotImplementedError('There is an unmet dependency at classes: %r' % configurators_to_allocate)
    return configurators_in_sequence


class Configurator:
    @classmethod
    def configure_many(self, configurators_classes: List[Type['Configurator']], given_data: given_data_type) -> None:
        configurators: List['Configurator'] = get_configuration_sequence(list(map(lambda cfgtrs: cfgtrs(), configurators_classes)), list(given_data.keys()))
        for configurator in configurators:
            newdata: Optional[given_data_type] = configurator._work(**{cn: given_data[cn] for cn in configurator._needs()})
            if newdata is not None:
                for k, v in newdata.items():
                    given_data[k] = v

    def _work(self, **data: given_data_type) -> Optional[given_data_type]:
        pass

    def _needs(self) -> List[str]:
        return []

    def _provides(self) -> List[str]:
        return []
