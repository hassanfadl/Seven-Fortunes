# -*- coding: utf-8 -*-

from odoo import models, fields, api


class BonusRequest(models.Model):
    _name = "bonus.request"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name", default="New", readonly=True, copy=False)

    @api.model
    def create(self, vals):
        vals['name'] = (self.env['ir.sequence'].next_by_code('bonus.request')) or 'New'
        return super(BonusRequest, self).create(vals)

    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee Name", required=False, )

    request_date = fields.Date(string="Today Date", required=False,  default=fields.Date.context_today)

    bonus_amount = fields.Float(string="Bonus Amount",  required=False, )

    reason = fields.Text(string="Reason", required=False, )

