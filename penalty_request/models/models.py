# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PenaltyRequest(models.Model):
    _name = "penalty.request"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name", default="New", readonly=True, copy=False)

    @api.model
    def create(self, vals):
        vals['name'] = (self.env['ir.sequence'].next_by_code('penalty.request')) or 'New'
        return super(PenaltyRequest, self).create(vals)

    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee Name", required=False, )

    request_date = fields.Date(string="Today Date", required=False,  default=fields.Date.context_today)

    penalty_amount = fields.Float(string="Penalty Amount",  required=False, )

    reason = fields.Text(string="Reason", required=False, )