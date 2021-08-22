# -*- coding: utf-8 -*-
from datetime import date, datetime, timedelta
from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta


class HrContract(models.Model):
    _inherit = 'hr.contract'

    is_saudi = fields.Boolean(string="Is Saudi ?", )
    adding_allowances = fields.Boolean(string="Add trans/house Allowance ?", )
    total_yearly_leave_days = fields.Integer(string="Number of annual vacation days", required=False,
                                             compute="get_total_yearly_leave_days", readonly=False)

    employee_type = fields.Selection(string="", selection=[('doctors_administrators', 'Doctors & Administrators'),
                                                           ('Workers', 'Workers'), ], required=False, )

    @api.onchange('employee_type')
    def get_total_yearly_leave_days(self):
        if self.employee_type == 'doctors_administrators':
            self.total_yearly_leave_days = 30
        elif self.employee_type == 'Workers':
            self.total_yearly_leave_days = 21
        else:
            return

    @api.depends('employee_type')
    def get_total_yearly_leave_days(self):
        if self.employee_type == 'doctors_administrators':
            self.total_yearly_leave_days = 30
        elif self.employee_type == 'Workers':
            self.total_yearly_leave_days = 21
        else:
            self.total_yearly_leave_days = 0

    # TODO Social Insurance fields
    insurance_date = fields.Date()
    insurance_salary = fields.Float()
    employee_percentage = fields.Float()
    company_percentage = fields.Float()
    employee_amount = fields.Float(compute='get_employee_percentage')
    company_amount = fields.Float(compute='get_employee_percentage')
    employee_gosi = fields.Float(string="Employee Gosi", required=False, compute='get_employee_percentage')
    company_gosi = fields.Float(string="Company Gosi", required=False, compute='get_employee_percentage')

    # TODO Social Medical fields
    medical_date = fields.Date()
    medical_insurance_employee = fields.Float()
    medical_insurance_family_check = fields.Boolean()
    medical_insurance_family = fields.Float()

    # TODO Allowances And Deductions fields
    house_allowances = fields.Float()
    transport_allowances = fields.Float()
    other_allowances = fields.Float()
    general_deductions = fields.Float()
    new_wage = fields.Float(string="", required=False, compute="get_new_wage")

    @api.depends('wage', 'adding_allowances', 'house_allowances', 'transport_allowances')
    def get_new_wage(self):
        if self.wage:
            if self.adding_allowances == True:
                self.new_wage = self.wage + self.house_allowances + self.transport_allowances
            else:
                self.new_wage = self.wage
        else:
            self.new_wage = 0.0

    @api.depends('employee_percentage', 'company_percentage', 'insurance_salary', 'is_saudi')
    def get_employee_percentage(self):
        if self.is_saudi == False:
            print("aaaaaa")
            self.employee_amount = self.get_amount_insurance(self.insurance_salary, self.employee_percentage)
            self.company_amount = self.get_amount_insurance(self.insurance_salary, self.company_percentage)
            self.employee_gosi = 0.0
            self.company_gosi = 0.0
        elif self.is_saudi == True:
            print("bbbbbb")
            self.employee_gosi = self.get_amount_insurance(self.insurance_salary, self.employee_percentage)
            self.company_gosi = self.get_amount_insurance(self.insurance_salary, self.company_percentage)
            self.employee_amount = 0.0
            self.company_amount = 0.0
        else:
            self.employee_gosi = 0.0
            self.company_gosi = 0.0
            self.employee_amount = 0.0
            self.company_amount = 0.0

    def get_amount_insurance(self, insurance_salary, insurance_percentage):
        return insurance_salary * (insurance_percentage / 100)

    @api.onchange('is_saudi')
    def set_insurance_salary(self):
        print("11111")
        for rec in self:
            if rec.is_saudi == True:
                rec.insurance_salary = rec.wage + rec.house_allowances
            elif rec.is_saudi == False:
                rec.insurance_salary = rec.wage
            else:
                return

    @api.onchange('adding_allowances')
    def set_insurance_salary(self):
        print("11111")
        for rec in self:
            if rec.adding_allowances == True:
                rec.new_wage = rec.wage + rec.house_allowances + rec.transport_allowances
            elif rec.adding_allowances == False:
                rec.new_wage = rec.wage
            else:
                return

    @api.onchange('house_allowances')
    def set_insurance_salaryy(self):
        print("22222")
        for rec in self:
            if rec.is_saudi == True:
                rec.insurance_salary = rec.wage + rec.house_allowances
            elif rec.is_saudi == False:
                rec.insurance_salary = rec.wage
            else:
                return

    def write(self, values):
        res = super(HrContract, self).write(values)
        if 'house_allowances' in values or 'wage' in values:
            self.insurance_salary = self.wage + self.house_allowances
        return res

    @api.model
    def _cron_refundable_advance_update_cron(self):
        print("ahmed saber in cron job")
