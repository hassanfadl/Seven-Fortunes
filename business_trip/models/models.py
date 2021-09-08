# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, datetime


class BusinessTrip(models.Model):
    _name = "business.trip"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name", default="New", readonly=True, copy=False)

    state = fields.Selection(string="", selection=[('draft', 'Draft'), ('confirm', 'Confirm'), ], required=False,
                             default='draft')

    @api.model
    def create(self, vals):
        vals['name'] = (self.env['ir.sequence'].next_by_code('business.trip')) or 'New'
        return super(BusinessTrip, self).create(vals)

    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee Name", required=False, )

    country_id = fields.Many2one(comodel_name="res.country.state", string="Country Name", required=False, )

    today_date = fields.Date(string="From Date", required=False, readonly=False, default=fields.Date.context_today)

    return_date = fields.Date(string="Return Date", required=False, )

    duration = fields.Float(string="Duration", store=False, compute="_get_contract_months")

    cost = fields.Float(string="Cost", required=False, related="country_id.cost")

    reason = fields.Text(string="Reason", required=False, )

    Total_price = fields.Float(string="Total Price", required=False, compute="_get_Total_price")

    @api.depends('return_date', 'today_date')
    def _get_contract_months(self):
        for i in self:
            if i.return_date and i.today_date:
                num_days = i.return_date - i.today_date
                num_days = num_days.days
                i.duration = num_days
            else:
                i.duration = 0.0
                
    @api.depends('return_date', 'today_date', 'duration', 'cost')
    def _get_Total_price(self):
        for i in self:
            if i.return_date and i.duration:
                i.Total_price = i.duration * i.cost
            else:
                i.Total_price = 0.0

    def confirm(self):
        for rec in self:
            date_from = datetime.strptime(rec.today_date.strftime('%Y%m%d'), '%Y%m%d')
            date_to = datetime.strptime(rec.return_date.strftime('%Y%m%d'), '%Y%m%d')
            vals = {
                'holiday_status_id': self.env['hr.leave.type'].search([('business_trip_holiday', '=', True)],
                                                                      limit=1).id,
                'name': 'business trip Holiday For Employee %s' % rec.employee_id.name,
                'holiday_type': 'employee',
                'employee_id': rec.employee_id.id,
                'request_date_from': rec.today_date,
                'date_from': date_from,
                'request_date_to': rec.return_date,
                'date_to': date_to,
                'number_of_days': rec.duration,
                'number_of_days_display': rec.duration,
            }
            print("vals", vals)
            hol = self.env['hr.leave'].create(vals)
            print("Ahmed Saber", hol)
            rec.state = 'confirm'


class CountryStateInherit(models.Model):
    _inherit = "res.country.state"

    cost = fields.Float(string="Cost", required=False, )
