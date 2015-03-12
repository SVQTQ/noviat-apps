# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    
#    Copyright (c) 2011 Noviat nv/sa (www.noviat.be). All rights reserved.
# 
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from datetime import datetime, date, timedelta
from osv import osv, fields
import netsvc
from tools.translate import _
logger=netsvc.Logger()

class account_cashflow_chart(osv.osv_memory):
    _name = 'account.cashflow.chart'
    _description = 'Cash Flow Chart'
    _columns = {
        'date_start': fields.date('Start Date', required=True),
        'date_stop': fields.date('End Date', required=True),
        'company_id': fields.many2one('res.company', 'Company', required=True),
    }

    def open_cashflow_chart(self, cr, uid, ids, context=None):
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')     
        balopen_obj = self.pool.get('account.cashflow.opening.balance')
        format_date = self.pool.get('account.cashflow.code').format_date   
        if context is None:
            context = {}

        try:            
            data = self.read(cr, uid, ids, [], context=context)[0]
        except:
            raise osv.except_osv(_('Error!'), _('Wizard in incorrect state. Please hit the Cancel button!'))
            return {}
        date_start = datetime.strptime(data['date_start'], '%Y-%m-%d').date()
        date_stop = datetime.strptime(data['date_stop'], '%Y-%m-%d').date()
        company_id = data['company_id']

        nbr_days = (date_stop - date_start).days + 1
        if nbr_days < 1 :
            raise osv.except_osv(_('Error!'), _('Invalid Date Range!'))
            return {}

        cr.execute("SELECT id FROM account_cashflow_code WHERE type='init' AND company_id = %s", (company_id,))
        res_init_id = cr.fetchall()
        if len(res_init_id) != 1:
            err_str = len(res_init_id) and 'Multiple' or 'No' 
            raise osv.except_osv('Configuration Error', 
                _("%s Cash Flow Codes of type='Initial Balance' defined for your Company !") % err_str)
        balance_init_id = res_init_id[0][0]

        # calculate opening balances for the date range of the chart 
        for x in range(0, nbr_days):
            date = (date_start + timedelta(days=x)).isoformat()
            balopen_obj.calc_opening_balance(cr, uid, date, balance_init_id, company_id)

        action = mod_obj.get_object_reference(cr, uid, 'account_cashflow', 'action_cashflow_chart_tree')
        action_id = action and action[1] or False
        result = act_obj.read(cr, uid, [action_id], context=context)[0]
        result['context'] = str({
            'date_start': data['date_start'], 'date_stop': data['date_stop'], 'nbr_days': nbr_days, 
            'company_id': company_id, 'balance_init_id': balance_init_id,
            })
        if nbr_days == 1:
            name = format_date(cr, uid, date_start, context)
        else:
            name = format_date(cr, uid, date_start, context) + '..' + format_date(cr, uid, date_stop, context)
        result['name'] += ': ' + name
        return result

    _defaults = {
        'date_start': lambda *a: (date.today() - timedelta(1)).isoformat(),
        'date_stop': lambda *a: time.strftime('%Y-%m-%d'),
        'company_id': lambda self,cr,uid,c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
    }

account_cashflow_chart()
