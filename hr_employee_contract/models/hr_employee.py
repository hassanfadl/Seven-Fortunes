# -*- coding: utf-8 -*-
from datetime import date, datetime, timedelta
from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta


class HrEmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    residence_issuance_date = fields.Date(string="Residence Issuance Date", required=False, )
    residence_end_date = fields.Date(string="Residence End Date", required=False, )
    residence_number = fields.Char(string="Residence Number", required=False, )
    professional_license_number = fields.Char(string="professional license number", required=False, )
    border_number = fields.Char(string="Border Number", required=False, )

    job_in_office = fields.Many2one(comodel_name="hr.job", string="Job In Office", required=False, )


class HrDepartureWizardInherit(models.TransientModel):
    _inherit = 'hr.departure.wizard'

    departure_reason = fields.Selection([
        ('fired', 'Fired'),
        ('resigned', 'Resigned'),
        ('retired', 'Retired'),
        ('end_service', 'End Service'),
        ('contract_expiration', 'Contract expiration'),
        ('terminate', 'Terminate'),
        ('mutual_contract_termination', 'Mutual contract termination'),
        ('going_on_vacation', 'Going on vacation')
    ], string="Departure Reason", default="fired")
