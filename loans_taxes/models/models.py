# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime
from datetime import date


class Loans_config_payroll(models.Model):
    _name = 'loans.config'
    name = fields.Char()
    company_max_loans_checkbox = fields.Boolean(
        'Determine Maximum Company Loans')
    company_max_loans = fields.Float('Company Maximum Loans')
    max_schedule_loans = fields.Integer('Maximum Schedule Loans per month')
    max_valid_loans_checkbox = fields.Boolean(
        'Determine Maximum number of Months salary Loans')
    max_valid_loans = fields.Float('Maximum employee Loans per salary')
    active = fields.Boolean("Active")

    @api.constrains('active')
    def constrains_active(self):
        active = self.search([('active', '=', True)])
        print(len(active))
        if len(active) > 1:
            raise ValidationError(
                "You Can't active this loans configuration because there is another loans active")


class HR_employee(models.Model):
    _inherit = 'hr.employee'

    def get_loans_configuration(self):
        loans_configuration = self.env['loans.config'].search(
            [('active', '=', True)], limit=1)
        return loans_configuration

    loans_configuration_id = fields.Many2one('loans.config', string="Loans Configuration",
                                             default=get_loans_configuration)


class Loans_main_menu(models.Model):
    _name = 'loans.creation'

    name = fields.Many2one('hr.employee', string='Employee Name')
    loans_amount = fields.Float('Loans Amount')
    request_date = fields.Date('Request Date')
    start_dateOf_loans = fields.Date('Loans Payoff Start Date')
    loans_period = fields.Integer('Loans months Period')
    loans_end_date = fields.Date(
        'Loans End Date', compute="_compute_loans_end_date")
    loans_details = fields.One2many(
        'loans.details', 'loans_creation', string="Payoff Details", readonly=True)
    state = fields.Selection([('draft', 'Draft'), ('approved', 'Approved'), ('cancel', 'Cancelled')],
                             required=True, default='draft')

    def button_approve(self):
        self.write({'state': 'approved'})

    def button_cancel(self):
        self.state = 'cancel'

    @api.constrains('loans_period', 'loans_amount')
    def _create_loans_with_config(self):
        for rec in self:
            # loans_config = self.env['loans.config'].search([('active', '=', True)], limit=1)
            total_emp_loans = 0
            loans_config = rec.name.loans_configuration_id
            contracts = self.env['hr.contract'].search(
                [('employee_id', '=', rec.name.id)], limit=1)
            wage = contracts.wage
            # print(wage)
            # print(loans_config)

            # this if for payoff period

            if rec.loans_period > loans_config.max_schedule_loans:
                raise ValidationError(
                    "Your Payoff Period is bigger than the Standard")

                # this if for company budget

            if loans_config.company_max_loans_checkbox == True:
                for line in rec.name:
                    total_emp_loans = total_emp_loans + rec.loans_amount
                    if total_emp_loans > loans_config.company_max_loans:
                        raise ValidationError(
                            "Loans Amount is bigger than the company budget")

                        # this if for employee budget

            if loans_config.max_valid_loans_checkbox == True:
                if rec.loans_amount > (wage*loans_config.max_valid_loans):
                    raise ValidationError(
                        "Loans Amount is bigger than your budget")

    def _compute_loans_end_date(self):
        for rec in self:
            if rec.start_dateOf_loans and rec.loans_period:
                rec.loans_end_date = rec.start_dateOf_loans + \
                    relativedelta(months=rec.loans_period)
            else:
                rec.loans_end_date = False

    @api.model
    def schaduel_get_loan_details(self):
        records = self.search([])
        for rec in records:
            rec.get_loans_details()
        return True

    def get_loans_details(self):
        cur_date = self.start_dateOf_loans
        end = self.loans_end_date
        today = date.today()
        lst = []
        while cur_date < end:
            # print(cur_date)
            lst.append(cur_date)
            cur_date += relativedelta(months=1)
        # print(cur_date)
        id_lst = []
        for pay in lst:
            monthly_payOff_dates = pay
            # print(monthly_payOff_dates)
            monthly_payOff_amount = self.loans_amount / self.loans_period
            if pay <= today:
                loans_status = 'paidOff'
            else:
                loans_status = 'notPaid'
            loan_detail = self.env['loans.details'].create({'monthly_payOff_dates': monthly_payOff_dates,
                                                            'monthly_payOff_amount': monthly_payOff_amount,
                                                            'loans_status': loans_status,
                                                            'loans_creation': self.id
                                                            }).id
            id_lst.append(loan_detail)

        self.update({'loans_details': [(6, 0, id_lst)]})


class Loans_Details(models.Model):
    _name = 'loans.details'

    # loans details table

    loans_status = fields.Selection(
        [('paidOff', 'Paid off'), ('notPaid', 'Not Paid')])
    monthly_payOff_dates = fields.Date('Pay Off Dates', )
    monthly_payOff_amount = fields.Float('Pay Off Amount', )
    loans_creation = fields.Many2one('loans.creation')

    # def _create_payOff_Details(self):
    #     for rec in self:
    #         loans_creations = rec.loans_creations
    #         cur_date = loans_creations.start_dateOf_loans
    #         end = loans_creations.loans_end_date
    #         today = datetime.date().today()
    #
    #         while cur_date < end:
    #             print(cur_date)
    #             cur_date += relativedelta(months=1)
    #         rec.monthly_payOff_dates = cur_date
    #
    #                             # the below lines for how much money should payoff monthly
    #         rec.monthly_payOff_amount = loans_creations.loans_amount / loans_creations.loans_period
    #
    #                                 # the below lines for monthly paid or not paid field
    #         for pay in cur_date:
    #             if pay <= today:
    #                 rec.loans_status = 'paidOff'
    #             else:
    #                 rec.loans_status = 'notPaid'
