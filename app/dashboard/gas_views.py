# -*- coding: utf-8 -*-
'''
    Copyright (C) 2017 Gitcoin Core

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.

'''
from __future__ import print_function, unicode_literals

import logging

from django.conf import settings
from django.core.cache import cache
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _

from economy.utils import convert_amount
from gas.utils import conf_time_spread, gas_advisories, gas_history, recommend_min_gas_price_to_confirm_in_time

from .helpers import get_bounty_data_for_activity, handle_bounty_views

logging.basicConfig(level=logging.DEBUG)

confirm_time_minutes_target = 4


def get_history_cached(breakdown, i):
    timeout = 60 * 60 * 3
    key_salt = '0'
    key = f'get_history_cached_{breakdown}_{i}_{key_salt}'
    results = cache.get(key)
    if results and not settings.DEBUG:
        return results

    results = gas_history(breakdown, i)
    cache.set(key, results, timeout)

    return results


def gas(request):
    _cts = conf_time_spread()
    recommended_gas_price = recommend_min_gas_price_to_confirm_in_time(confirm_time_minutes_target)
    if recommended_gas_price < 2:
        _cts = conf_time_spread(recommended_gas_price)

    context = {
        'title': _('Live Gas Tool'),
        'card_desc': _('See the Live Network Conditions for the Ethereum Network'),
        'eth_to_usd': round(convert_amount(1, 'ETH', 'USDT'), 0),
        'start_gas_cost': recommended_gas_price,
        'gas_advisories': gas_advisories(),
        'conf_time_spread': _cts,
        'hide_send_tip': True,
        'title': 'Live Gas Usage => Predicted Conf Times'
    }
    return TemplateResponse(request, 'gas.html', context)


def gas_faq(request):

    context = {
        'title': _('Gas FAQ'),
        'card_desc': _('FAQ about Gas'),
        'hide_send_tip': True,
    }
    return TemplateResponse(request, 'gas_faq.html', context)


def gas_faucet_list(request):

    context = {
        'title': _('Gas Faucet List'),
        'card_desc': _('List of Gas Faucets'),
        'hide_send_tip': True,
    }
    return TemplateResponse(request, 'gas_faucet_list.html', context)


def gas_calculator(request):
    recommended_gas_price = recommend_min_gas_price_to_confirm_in_time(confirm_time_minutes_target)
    _cts = conf_time_spread()

    actions = [{
        'name': 'New Bounty',
        'target': '/new',
        'persona': 'funder',
        'product': 'bounties',
    }, {
        'name': 'Fulfill Bounty',
        'target': 'issue/fulfill',
        'persona': 'developer',
        'product': 'bounties',
    }, {
        'name': 'Increase Funding',
        'target': 'issue/increase',
        'persona': 'funder',
        'product': 'bounties',
    }, {
        'name': 'Accept Submission',
        'target': 'issue/accept',
        'persona': 'funder',
        'product': 'bounties',
    }, {
        'name': 'Cancel Funding',
        'target': 'issue/cancel',
        'persona': 'funder',
        'product': 'bounties',
    }, {
        'name': 'Send tip',
        'target': 'tip/send/2/',
        'persona': 'funder',
        'product': 'tips',
    }, {
        'name': 'Receive tip',
        'target': 'tip/receive',
        'persona': 'developer',
        'product': 'tips',
    }
    ]
    context = {
        'title': _('Gas Estimator'),
        'card_desc': _('See what popular Gitcoin methods cost at different Gas Prices'),
        'actions': actions,
        'conf_time_spread': _cts,
        'eth_to_usd': round(convert_amount(1, 'ETH', 'USDT'), 0),
        'start_gas_cost': recommended_gas_price,
        'title': 'Gas Calculator',
        'hide_send_tip': True,
    }
    return TemplateResponse(request, 'gas_calculator.html', context)


def gas_history_view(request):
    breakdown = request.GET.get('breakdown', 'hourly')
    gas_histories = {}
    max_y = 0
    lines = {
        1: 'red',
        5: 'orange',
        60: 'green',
        120: 'steelblue',
        180: 'purple',
    }
    for i in lines.keys():
        gas_histories[i] = get_history_cached(breakdown, i)
        for gh in gas_histories[i]:
            max_y = max(gh[0], max_y)
    breakdown_ui = breakdown.replace('ly', '') if breakdown != 'daily' else 'day'
    context = {
        'title': _('Gas History'),
        'card_desc': _('View the history of ethereum network gas prices'),
        'max': max_y,
        'lines': lines,
        'gas_histories': gas_histories,
        'breakdown': breakdown,
        'breakdown_ui': breakdown_ui,
        'granularity_options': ['hourly', 'daily', 'weekly'],
    }
    return TemplateResponse(request, 'gas_history.html', context)
