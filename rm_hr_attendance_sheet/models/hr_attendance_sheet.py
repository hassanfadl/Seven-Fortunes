# -*- coding: utf-8 -*-

##############################################################################
#
#
#    Copyright (C) 2020-TODAY .
#    Author: Eng.Ramadan Khalil (<rkhalil1990@gmail.com>)
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
##############################################################################

import pytz
from datetime import datetime, date, timedelta, time
from dateutil.relativedelta import relativedelta
from odoo import models, fields, tools, api, exceptions, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import format_date
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY, \
    make_aware, datetime_to_string, string_to_datetime

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TIME_FORMAT = "%H:%M:%S"


class AttendanceSheet(models.Model):
    _name = 'attendance.sheet'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _description = 'Hr Attendance Sheet'

    name = fields.Char("name")
    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee',
                                  required=True)

    batch_id = fields.Many2one(comodel_name='attendance.sheet.batch',
                               string='Attendance Sheet Batch')
    department_id = fields.Many2one(related='employee_id.department_id',
                                    string='Department', store=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True,
                                 copy=False, required=True,
                                 default=lambda self: self.env.company,
                                 states={'draft': [('readonly', False)]})
    date_from = fields.Date(string='Date From', readonly=True, required=True,
                            default=lambda self: fields.Date.to_string(
                                date.today().replace(day=1)), )
    date_to = fields.Date(string='Date To', readonly=True, required=True,
                          default=lambda self: fields.Date.to_string(
                              (datetime.now() + relativedelta(months=+1, day=1,
                                                              days=-1)).date()))
    line_ids = fields.One2many(comodel_name='attendance.sheet.line',
                               string='Attendances', readonly=True,
                               inverse_name='att_sheet_id')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('done', 'Approved')], default='draft', track_visibility='onchange',
        string='Status', required=True, readonly=True, index=True,
        help=' * The \'Draft\' status is used when a HR user is creating a new  attendance sheet. '
             '\n* The \'Confirmed\' status is used when  attendance sheet is confirmed by HR user.'
             '\n* The \'Approved\' status is used when  attendance sheet is accepted by the HR Manager.')
    no_overtime = fields.Integer(compute="_compute_sheet_total",
                                 string="No of overtimes", readonly=True,
                                 store=True)
    tot_overtime = fields.Float(compute="_compute_sheet_total",
                                string="Total Over Time", readonly=True,
                                store=True)
    tot_difftime = fields.Float(compute="_compute_sheet_total",
                                string="Total Diff time Hours", readonly=True,
                                store=True)
    no_difftime = fields.Integer(compute="_compute_sheet_total",
                                 string="No of Diff Times", readonly=True,
                                 store=True)
    tot_late = fields.Float(compute="_compute_sheet_total",
                            string="Total Late In", readonly=True, store=True)
    no_late = fields.Integer(compute="_compute_sheet_total",
                             string="No of Lates",
                             readonly=True, store=True)
    no_absence = fields.Integer(compute="_compute_sheet_total",
                                string="No of Absence Days", readonly=True,
                                store=True)
    tot_absence = fields.Float(compute="_compute_sheet_total",
                               string="Total absence Hours", readonly=True,
                               store=True)
    tot_worked_hour = fields.Float(compute="_compute_sheet_total",
                                   string="Total Late In", readonly=True,
                                   store=True)
    att_policy_id = fields.Many2one(comodel_name='hr.attendance.policy',
                                    string="Attendance Policy ", required=True)
    payslip_id = fields.Many2one(comodel_name='hr.payslip', string='PaySlip')

    contract_id = fields.Many2one('hr.contract', string='Contract',
                                  readonly=True,
                                  states={'draft': [('readonly', False)]})

    termination_indemnity = fields.Float(string="", required=False, )
    penalty = fields.Float('Total Penalty')

    # TODO Insurance fields
    employee_insurance_amount = fields.Float()
    employee_gosi = fields.Float(string="Employee Gosi", required=False, )
    medical_insurance_employee = fields.Float()
    medical_insurance_family = fields.Float()

    # TODO allowances fields
    house_allowances = fields.Float()
    transport_allowances = fields.Float()
    # living_allowances = fields.Float()
    other_allowances = fields.Float()
    # internal_travel_allowances = fields.Float()
    ###########################################################################
    # nature_of_work_allowances = fields.Float()
    # food_allowances = fields.Float()
    # end_of_service_allowance = fields.Float()
    # telephone_allowance = fields.Float()
    # contract_extension = fields.Float()
    # constant_refundable_advance = fields.Float(string="Refundable Advance")

    # TODO deductions fields
    general_deductions = fields.Float()

    business_trip = fields.Float()
    # residency_issuance_and_renewal_costs = fields.Float()

    # TODO _____________ AHMED SABER START CUSTOM FUNCTIONS FOR CUSTOM SALARY ROLES _____________

    def update_current_penalty_to_paid(self):
        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to
        total_amount = 0
        domain = [('employee_id', '=', employee.id), ('request_date', '>=', date_from), ('request_date', '<=', date_to),
                  ('state', '=', 'approved')]
        loans_for_emp = self.env['penalty.request'].search(domain)
        print('loans_for_emp >>>>>>>>>>>', loans_for_emp)
        for loan in loans_for_emp:
            penalty_ids = loan.penalty_ids.filtered(lambda x: not x.paid and x.date >= date_from and x.date <= date_to)
            print('penalty_ids >>>>>>>>>>>>>>>>>>', penalty_ids)
            for pay in penalty_ids:
                total_amount += pay.amount
                pay.write({'paid': True})
        print('total_amount', total_amount)
        self.penalty = total_amount

    def update_termination_indemnity_allowance(self):
        employee = self.employee_id
        total_amount = 0
        domain = [('employee_id', '=', employee.id), ('state', '=', 'open') ]
        contract_object = self.env['hr.contract'].search(domain)
        print("contract_object >>>>>>>>>>>>>>", contract_object)
        if contract_object:
            domain = [('employee_id', '=', employee.id), ('accounting_method', '=', False), ('state', '=', 'approved')]
            termination_object = self.env['hr.termination'].search(domain)
            print("termination_object[0].indemnity >>>>>>>>>>>", termination_object.indemnity)
            total_amount = termination_object.indemnity
        self.termination_indemnity = total_amount

    def update_all_allowance_and_deduction_fields(self):
        employee = self.employee_id
        domain = [('employee_id', '=', employee.id), ('state', '=', 'open'), ]
        contract_object = self.env['hr.contract'].search(domain)
        print("contract_object >>>>>>>>>>>>>>", contract_object)
        if contract_object:
            self.house_allowances = contract_object[0].house_allowances
            self.transport_allowances = contract_object[0].transport_allowances
            # self.living_allowances = contract_object[0].living_allowances
            self.other_allowances = contract_object[0].other_allowances
            # self.internal_travel_allowances = contract_object[0].internal_travel_allowances
            self.general_deductions = contract_object[0].general_deductions
            self.medical_insurance_employee = contract_object[0].medical_insurance_employee
            self.medical_insurance_family = contract_object[0].medical_insurance_family
            # self.residency_issuance_and_renewal_costs = contract_object[0].residency_issuance_and_renewal_costs
            # self.nature_of_work_allowances = contract_object[0].nature_of_work_allowances
            # self.food_allowances = contract_object[0].food_allowances
            # self.end_of_service_allowance = contract_object[0].end_of_service_allowance
            # self.telephone_allowance = contract_object[0].telephone_allowance
            # self.contract_extension = contract_object[0].contract_extension
            # self.constant_refundable_advance = contract_object[0].constant_refundable_advance
            if contract_object.type_of_company_offices == 'saudi_office':
                self.employee_insurance_amount = 0.0
                self.employee_gosi = contract_object[0].employee_gosi
            elif contract_object.type_of_company_offices == 'egyptian_office':
                self.employee_insurance_amount = contract_object[0].employee_amount
                self.employee_gosi = 0.0
            else:
                self.employee_insurance_amount = 0.0
                self.employee_gosi = 0.0
        else:
            self.house_allowances = 0.0
            self.transport_allowances = 0.0
            # self.living_allowances = 0.0
            self.other_allowances = 0.0
            # self.internal_travel_allowances = 0.0
            self.general_deductions = 0.0
            self.medical_insurance_employee = 0.0
            self.medical_insurance_family = 0.0
            self.employee_insurance_amount = 0.0
            self.employee_gosi = 0.0
            # self.residency_issuance_and_renewal_costs = 0.0

            # self.nature_of_work_allowances = 0.0
            # self.food_allowances = 0.0
            # self.end_of_service_allowance = 0.0
            # self.telephone_allowance = 0.0
            # self.contract_extension = 0.0
            # self.constant_refundable_advance = 0.0

    def update_current_business_trip_cost_deduction(self):
        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to
        total_amount = 0
        domain = [('employee_id', '=', employee.id), ('today_date', '>=', date_from),
                  ('today_date', '<=', date_to),
                  ('state', '=', 'confirm')]
        business_object = self.env['business.trip'].search(domain)
        for trip in business_object:
            if trip.Total_price > 0:
                total_amount += trip.Total_price
        self.business_trip = total_amount

    # TODO _____________ AHMED SABER END CUSTOM FUNCTIONS FOR CUSTOM SALARY ROLES _____________

    def unlink(self):
        if any(self.filtered(
                lambda att: att.state not in ('draft', 'confirm'))):
            # TODO:un comment validation in case on non testing
            pass
            # raise UserError(_(
            #     'You cannot delete an attendance sheet which is '
            #     'not draft or confirmed!'))
        return super(AttendanceSheet, self).unlink()

    @api.constrains('date_from', 'date_to')
    def check_date(self):
        for sheet in self:
            emp_sheets = self.env['attendance.sheet'].search(
                [('employee_id', '=', sheet.employee_id.id),
                 ('id', '!=', sheet.id)])
            for emp_sheet in emp_sheets:
                if max(sheet.date_from, emp_sheet.date_from) < min(
                        sheet.date_to, emp_sheet.date_to):
                    raise UserError(_(
                        'You Have Already Attendance Sheet For That '
                        'Period  Please pick another date !'))

    def action_confirm(self):
        self.write({'state': 'confirm'})
        self.update_termination_indemnity_allowance()
        self.update_all_allowance_and_deduction_fields()
        self.update_current_penalty_to_paid()
        self.update_current_business_trip_cost_deduction()

    def action_approve(self):
        self.action_create_payslip()
        self.write({'state': 'done'})

    def action_draft(self):
        self.write({'state': 'draft'})

    @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_employee(self):
        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return
        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to
        self.name = 'Attendance Sheet - %s - %s' % (self.employee_id.name or '',
                                                    format_date(self.env,
                                                                self.date_from,
                                                                date_format="MMMM y"))
        self.company_id = employee.company_id
        contracts = employee._get_contracts(date_from, date_to)
        if not contracts:
            raise ValidationError(
                _('There Is No Valid Contract For Employee %s' % employee.name))
        self.contract_id = contracts[0]
        if not self.contract_id.att_policy_id:
            raise ValidationError(_(
                "Employee %s does not have attendance policy" % employee.name))
        self.att_policy_id = self.contract_id.att_policy_id

    @api.depends('line_ids.overtime', 'line_ids.diff_time', 'line_ids.late_in')
    def _compute_sheet_total(self):
        """
        Compute Total overtime,late ,absence,diff time and worked hours
        :return:
        """
        for sheet in self:
            # Compute Total Overtime
            overtime_lines = sheet.line_ids.filtered(lambda l: l.overtime > 0)
            sheet.tot_overtime = sum([l.overtime for l in overtime_lines])
            sheet.no_overtime = len(overtime_lines)
            # Compute Total Late In
            late_lines = sheet.line_ids.filtered(lambda l: l.late_in > 0)
            the_total = sum([l.late_in for l in late_lines])
            sheet.no_late = len(late_lines)
            if the_total > 240:
                the_rest = the_total - 240
                sheet.tot_late = 240 + the_rest * 2
            else:
                sheet.tot_late = the_total
            # Compute Absence
            absence_lines = sheet.line_ids.filtered(
                lambda l: l.diff_time > 0 and l.status == "ab")
            sheet.tot_absence = sum([l.diff_time for l in absence_lines])
            sheet.no_absence = len(absence_lines)
            # conmpute earlyout
            diff_lines = sheet.line_ids.filtered(
                lambda l: l.diff_time > 0 and l.status != "ab")
            sheet.tot_difftime = sum([l.diff_time for l in diff_lines])
            sheet.no_difftime = len(diff_lines)

    def _get_float_from_time(self, time):
        str_time = datetime.strftime(time, "%H:%M")
        split_time = [int(n) for n in str_time.split(":")]
        float_time = split_time[0] + split_time[1] / 60.0
        return float_time

    def get_attendance_intervals(self, employee, day_start, day_end, tz):
        """

        :param employee:
        :param day_start:datetime the start of the day in datetime format
        :param day_end: datetime the end of the day in datetime format
        :return:
        """
        day_start_native = day_start.replace(tzinfo=tz).astimezone(
            pytz.utc).replace(tzinfo=None)
        day_end_native = day_end.replace(tzinfo=tz).astimezone(
            pytz.utc).replace(tzinfo=None)
        res = []
        attendances = self.env['hr.attendance'].sudo().search(
            [('employee_id', '=', employee.id),
             ('check_in', '>=', day_start_native),
             ('check_in', '<=', day_end_native)],
            order="check_in")
        for att in attendances:
            check_in = att.check_in
            check_out = att.check_out
            if not check_out:
                continue
            res.append((check_in, check_out))
        return res

    def _get_emp_leave_intervals(self, emp, start_datetime=None,
                                 end_datetime=None):
        leaves = []
        leave_obj = self.env['hr.leave']
        leave_ids = leave_obj.search([
            ('employee_id', '=', emp.id),
            ('state', '=', 'validate')])

        for leave in leave_ids:
            date_from = leave.date_from
            if end_datetime and date_from > end_datetime:
                continue
            date_to = leave.date_to
            if start_datetime and date_to < start_datetime:
                continue
            leaves.append((date_from, date_to))
        return leaves

    def get_public_holiday(self, date, emp):
        public_holiday = []
        public_holidays = self.env['hr.public.holiday'].sudo().search(
            [('date_from', '<=', date), ('date_to', '>=', date),
             ('state', '=', 'active')])
        for ph in public_holidays:
            print('ph is', ph.name, [e.name for e in ph.emp_ids])
            if not ph.emp_ids:
                return public_holidays
            if emp.id in ph.emp_ids.ids:
                public_holiday.append(ph.id)
        return public_holiday

    def get_attendances(self):
        for att_sheet in self:
            att_sheet.line_ids.unlink()
            att_line = self.env["attendance.sheet.line"]
            from_date = att_sheet.date_from
            to_date = att_sheet.date_to
            emp = att_sheet.employee_id
            tz = pytz.timezone(emp.tz)
            if not tz:
                raise exceptions.Warning(
                    "Please add time zone for employee : %s" % emp.name)
            calendar_id = emp.contract_id.resource_calendar_id
            if not calendar_id:
                raise ValidationError(_(
                    'Please add working hours to the %s `s contract ' % emp.name))
            policy_id = att_sheet.att_policy_id
            if not policy_id:
                raise ValidationError(_(
                    'Please add Attendance Policy to the %s `s contract ' % emp.name))

            all_dates = [(from_date + timedelta(days=x)) for x in
                         range((to_date - from_date).days + 1)]
            abs_cnt = 0
            late_cnt = []
            for day in all_dates:
                day_start = datetime(day.year, day.month, day.day)
                day_end = day_start.replace(hour=23, minute=59,
                                            second=59)
                day_str = str(day.weekday())
                date = day.strftime('%Y-%m-%d')
                work_intervals = att_sheet._get_work_intervals(calendar_id, day_start, day_end, tz)
                attendance_intervals = self.get_attendance_intervals(emp,
                                                                     day_start,
                                                                     day_end,
                                                                     tz)
                leaves = self._get_emp_leave_intervals(emp, day_start, day_end)
                public_holiday = self.get_public_holiday(date, emp)
                reserved_intervals = []
                overtime_policy = policy_id.get_overtime()
                abs_flag = False
                if work_intervals:
                    if public_holiday:
                        if attendance_intervals:
                            for attendance_interval in attendance_intervals:
                                overtime = attendance_interval[1] - \
                                           attendance_interval[0]
                                float_overtime = overtime.total_seconds() / 3600
                                if float_overtime <= overtime_policy[
                                    'ph_after']:
                                    act_float_overtime = float_overtime = 0
                                else:
                                    act_float_overtime = (float_overtime -
                                                          overtime_policy[
                                                              'ph_after'])
                                    float_overtime = (float_overtime -
                                                      overtime_policy[
                                                          'ph_after']) * \
                                                     overtime_policy['ph_rate']
                                ac_sign_in = pytz.utc.localize(
                                    attendance_interval[0]).astimezone(tz)
                                float_ac_sign_in = self._get_float_from_time(
                                    ac_sign_in)
                                ac_sign_out = pytz.utc.localize(
                                    attendance_interval[1]).astimezone(tz)
                                worked_hours = attendance_interval[1] - \
                                               attendance_interval[0]
                                float_worked_hours = worked_hours.total_seconds() / 3600
                                float_ac_sign_out = float_ac_sign_in + float_worked_hours
                                values = {
                                    'date': date,
                                    'day': day_str,
                                    'ac_sign_in': float_ac_sign_in,
                                    'ac_sign_out': float_ac_sign_out,
                                    'worked_hours': float_worked_hours,
                                    'overtime': float_overtime,
                                    'act_overtime': act_float_overtime,
                                    'att_sheet_id': self.id,
                                    'status': 'ph',
                                    'note': _("working on Public Holiday")
                                }
                                att_line.create(values)
                        else:
                            values = {
                                'date': date,
                                'day': day_str,
                                'att_sheet_id': self.id,
                                'status': 'ph',
                            }
                            att_line.create(values)
                    else:
                        for i, work_interval in enumerate(work_intervals):
                            float_worked_hours = 0
                            att_work_intervals = []
                            diff_intervals = []
                            late_in_interval = []
                            diff_time = timedelta(hours=00, minutes=00,
                                                  seconds=00)
                            late_in = timedelta(hours=00, minutes=00,
                                                seconds=00)
                            overtime = timedelta(hours=00, minutes=00,
                                                 seconds=00)
                            for j, att_interval in enumerate(
                                    attendance_intervals):
                                if max(work_interval[0], att_interval[0]) < min(
                                        work_interval[1], att_interval[1]):
                                    current_att_interval = att_interval
                                    if i + 1 < len(work_intervals):
                                        next_work_interval = work_intervals[
                                            i + 1]
                                        if max(next_work_interval[0],
                                               current_att_interval[0]) < min(
                                            next_work_interval[1],
                                            current_att_interval[1]):
                                            split_att_interval = (
                                                next_work_interval[0],
                                                current_att_interval[1])
                                            current_att_interval = (
                                                current_att_interval[0],
                                                next_work_interval[0])
                                            attendance_intervals[
                                                j] = current_att_interval
                                            attendance_intervals.insert(j + 1,
                                                                        split_att_interval)
                                    att_work_intervals.append(
                                        current_att_interval)
                            reserved_intervals += att_work_intervals
                            pl_sign_in = self._get_float_from_time(
                                pytz.utc.localize(work_interval[0]).astimezone(
                                    tz))
                            pl_sign_out = self._get_float_from_time(
                                pytz.utc.localize(work_interval[1]).astimezone(
                                    tz))
                            pl_sign_in_time = pytz.utc.localize(
                                work_interval[0]).astimezone(tz)
                            pl_sign_out_time = pytz.utc.localize(
                                work_interval[1]).astimezone(tz)
                            ac_sign_in = 0
                            ac_sign_out = 0
                            status = ""
                            note = ""
                            if att_work_intervals:
                                if len(att_work_intervals) > 1:
                                    # print("there is more than one interval for that work interval")
                                    late_in_interval = (
                                        work_interval[0],
                                        att_work_intervals[0][0])
                                    overtime_interval = (
                                        work_interval[1],
                                        att_work_intervals[-1][1])
                                    if overtime_interval[1] < overtime_interval[
                                        0]:
                                        overtime = timedelta(hours=0, minutes=0,
                                                             seconds=0)
                                    else:
                                        overtime = overtime_interval[1] - \
                                                   overtime_interval[0]
                                    remain_interval = (
                                        att_work_intervals[0][1],
                                        work_interval[1])
                                    # print'first remain intervals is',remain_interval
                                    for att_work_interval in att_work_intervals:
                                        float_worked_hours += (
                                                                      att_work_interval[
                                                                          1] -
                                                                      att_work_interval[
                                                                          0]).total_seconds() / 3600
                                        # print'float worked hors is', float_worked_hours
                                        if att_work_interval[1] <= \
                                                remain_interval[0]:
                                            continue
                                        if att_work_interval[0] >= \
                                                remain_interval[1]:
                                            break
                                        if remain_interval[0] < \
                                                att_work_interval[0] < \
                                                remain_interval[1]:
                                            diff_intervals.append((
                                                remain_interval[
                                                    0],
                                                att_work_interval[
                                                    0]))
                                            remain_interval = (
                                                att_work_interval[1],
                                                remain_interval[1])
                                    if remain_interval and remain_interval[0] <= \
                                            work_interval[1]:
                                        diff_intervals.append((remain_interval[
                                                                   0],
                                                               work_interval[
                                                                   1]))
                                    ac_sign_in = self._get_float_from_time(
                                        pytz.utc.localize(att_work_intervals[0][
                                                              0]).astimezone(
                                            tz))
                                    ac_sign_out = self._get_float_from_time(
                                        pytz.utc.localize(
                                            att_work_intervals[-1][
                                                1]).astimezone(tz))
                                    ac_sign_out = ac_sign_in + ((
                                                                        att_work_intervals[
                                                                            -1][
                                                                            1] -
                                                                        att_work_intervals[
                                                                            0][
                                                                            0]).total_seconds() / 3600)
                                else:
                                    late_in_interval = (
                                        work_interval[0],
                                        att_work_intervals[0][0])
                                    overtime_interval = (
                                        work_interval[1],
                                        att_work_intervals[-1][1])
                                    if overtime_interval[1] < overtime_interval[
                                        0]:
                                        overtime = timedelta(hours=0, minutes=0,
                                                             seconds=0)
                                        diff_intervals.append((
                                            overtime_interval[
                                                1],
                                            overtime_interval[
                                                0]))
                                    else:
                                        overtime = overtime_interval[1] - \
                                                   overtime_interval[0]
                                    ac_sign_in = self._get_float_from_time(
                                        pytz.utc.localize(att_work_intervals[0][
                                                              0]).astimezone(
                                            tz))
                                    ac_sign_out = self._get_float_from_time(
                                        pytz.utc.localize(att_work_intervals[0][
                                                              1]).astimezone(
                                            tz))
                                    worked_hours = att_work_intervals[0][1] - \
                                                   att_work_intervals[0][0]
                                    float_worked_hours = worked_hours.total_seconds() / 3600
                                    ac_sign_out = ac_sign_in + float_worked_hours
                            else:
                                late_in_interval = []
                                diff_intervals.append(
                                    (work_interval[0], work_interval[1]))

                                status = "ab"
                            if diff_intervals:
                                for diff_in in diff_intervals:
                                    if leaves:
                                        status = "leave"
                                        diff_clean_intervals = calendar_id.att_interval_without_leaves(
                                            diff_in, leaves)
                                        for diff_clean in diff_clean_intervals:
                                            diff_time += diff_clean[1] - \
                                                         diff_clean[0]
                                    else:
                                        diff_time += diff_in[1] - diff_in[0]
                            if late_in_interval:
                                if late_in_interval[1] < late_in_interval[0]:
                                    late_in = timedelta(hours=0, minutes=0,
                                                        seconds=0)
                                else:
                                    if leaves:
                                        late_clean_intervals = calendar_id.att_interval_without_leaves(
                                            late_in_interval, leaves)
                                        for late_clean in late_clean_intervals:
                                            late_in += late_clean[1] - \
                                                       late_clean[0]
                                    else:
                                        late_in = late_in_interval[1] - \
                                                  late_in_interval[0]
                            float_overtime = overtime.total_seconds() / 3600
                            if float_overtime <= overtime_policy['wd_after']:
                                act_float_overtime = float_overtime = 0
                            else:
                                act_float_overtime = float_overtime
                                float_overtime = float_overtime * \
                                                 overtime_policy[
                                                     'wd_rate']
                            float_late = late_in.total_seconds() / 3600
                            act_float_late = late_in.total_seconds() / 3600
                            policy_late, late_cnt = policy_id.get_late(
                                float_late,
                                late_cnt)
                            float_diff = diff_time.total_seconds() / 3600
                            if status == 'ab':
                                if not abs_flag:
                                    abs_cnt += 1
                                abs_flag = True

                                act_float_diff = float_diff
                                float_diff = policy_id.get_absence(float_diff,
                                                                   abs_cnt)
                            else:
                                act_float_diff = float_diff
                                float_diff = policy_id.get_diff(float_diff)
                            values = {
                                'date': date,
                                'day': day_str,
                                'pl_sign_in': pl_sign_in,
                                'pl_sign_out': pl_sign_out,
                                'ac_sign_in': ac_sign_in,
                                'ac_sign_out': ac_sign_out,
                                'late_in': policy_late,
                                'act_late_in': act_float_late,
                                'worked_hours': float_worked_hours,
                                'overtime': float_overtime,
                                'act_overtime': act_float_overtime,
                                'diff_time': float_diff,
                                'act_diff_time': act_float_diff,
                                'status': status,
                                'att_sheet_id': self.id
                            }
                            att_line.create(values)
                        out_work_intervals = [x for x in attendance_intervals if
                                              x not in reserved_intervals]
                        if out_work_intervals:
                            for att_out in out_work_intervals:
                                overtime = att_out[1] - att_out[0]
                                ac_sign_in = self._get_float_from_time(
                                    pytz.utc.localize(att_out[0]).astimezone(
                                        tz))
                                ac_sign_out = self._get_float_from_time(
                                    pytz.utc.localize(att_out[1]).astimezone(
                                        tz))
                                float_worked_hours = overtime.total_seconds() / 3600
                                ac_sign_out = ac_sign_in + float_worked_hours
                                float_overtime = overtime.total_seconds() / 3600
                                if float_overtime <= overtime_policy[
                                    'wd_after']:
                                    float_overtime = act_float_overtime = 0
                                else:
                                    act_float_overtime = float_overtime
                                    float_overtime = act_float_overtime * \
                                                     overtime_policy['wd_rate']
                                values = {
                                    'date': date,
                                    'day': day_str,
                                    'pl_sign_in': 0,
                                    'pl_sign_out': 0,
                                    'ac_sign_in': ac_sign_in,
                                    'ac_sign_out': ac_sign_out,
                                    'overtime': float_overtime,
                                    'worked_hours': float_worked_hours,
                                    'act_overtime': act_float_overtime,
                                    'note': _("overtime out of work intervals"),
                                    'att_sheet_id': self.id
                                }
                                att_line.create(values)
                else:
                    if attendance_intervals:
                        # print "thats weekend be over time "
                        for attendance_interval in attendance_intervals:
                            overtime = attendance_interval[1] - \
                                       attendance_interval[0]
                            ac_sign_in = pytz.utc.localize(
                                attendance_interval[0]).astimezone(tz)
                            ac_sign_out = pytz.utc.localize(
                                attendance_interval[1]).astimezone(tz)
                            float_overtime = overtime.total_seconds() / 3600
                            if float_overtime <= overtime_policy['we_after']:
                                float_overtime = 0
                                act_float_overtime = 0
                            else:
                                act_float_overtime = float_overtime
                                float_overtime = act_float_overtime * \
                                                 overtime_policy['we_rate']
                            ac_sign_in = pytz.utc.localize(
                                attendance_interval[0]).astimezone(tz)
                            ac_sign_out = pytz.utc.localize(
                                attendance_interval[1]).astimezone(tz)
                            worked_hours = attendance_interval[1] - \
                                           attendance_interval[0]
                            float_worked_hours = worked_hours.total_seconds() / 3600
                            values = {
                                'date': date,
                                'day': day_str,
                                'ac_sign_in': self._get_float_from_time(
                                    ac_sign_in),
                                'ac_sign_out': self._get_float_from_time(
                                    ac_sign_out),
                                'overtime': float_overtime,
                                'act_overtime': act_float_overtime,
                                'worked_hours': float_worked_hours,
                                'att_sheet_id': self.id,
                                'status': 'weekend',
                                'note': _("working in weekend")
                            }
                            att_line.create(values)
                    else:
                        values = {
                            'date': date,
                            'day': day_str,
                            'att_sheet_id': self.id,
                            'status': 'weekend',
                            'note': ""
                        }
                        att_line.create(values)

    def _get_work_intervals(self, calendar, day_start, day_end, tz):
        self.ensure_one()
        return calendar.att_get_work_intervals(day_start, day_end, tz)

    def action_payslip(self):
        self.ensure_one()
        payslip_id = self.payslip_id
        if not payslip_id:
            payslip_id = self.action_create_payslip()[0]
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payslip',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': payslip_id.id,
            'views': [(False, 'form')],
        }

    def action_create_payslip(self):
        payslip_obj = self.env['hr.payslip']
        payslips = payslip_obj
        for sheet in self:
            contracts = sheet.employee_id._get_contracts(sheet.date_from,
                                                         sheet.date_to)
            if not contracts:
                raise ValidationError(_('There is no active contract for current employee'))
            if sheet.payslip_id:
                raise ValidationError(_('Payslip Has Been Created Before'))
            new_payslip = payslip_obj.new({
                'employee_id': sheet.employee_id.id,
                'date_from': sheet.date_from,
                'date_to': sheet.date_to,
                'contract_id': contracts[0].id,
                'struct_id': contracts[0].structure_type_id.default_struct_id.id
            })
            new_payslip._onchange_employee()
            payslip_dict = new_payslip._convert_to_write({
                name: new_payslip[name] for name in new_payslip._cache})

            payslip_id = payslip_obj.create(payslip_dict)
            worked_day_lines = self._get_workday_lines()
            payslip_id.worked_days_line_ids = [(0, 0, x) for x in
                                               worked_day_lines]
            payslip_id.compute_sheet()
            sheet.payslip_id = payslip_id
            payslips += payslip_id
        return payslips

    def _get_workday_lines(self):
        self.ensure_one()

        work_entry_obj = self.env['hr.work.entry.type']
        overtime_work_entry = work_entry_obj.search([('code', '=', 'ATTSHOT')])
        latin_work_entry = work_entry_obj.search([('code', '=', 'ATTSHLI')])
        absence_work_entry = work_entry_obj.search([('code', '=', 'ATTSHAB')])
        difftime_work_entry = work_entry_obj.search([('code', '=', 'ATTSHDT')])
        termination_indemnity_work_entry = work_entry_obj.search([('code', '=', 'ATTSHTERM')])

        house_allowances_work_entry = work_entry_obj.search([('code', '=', 'ATTSHTHOUSAL')])
        transport_allowances_work_entry = work_entry_obj.search([('code', '=', 'ATTSHTTARNSAL')])
        # living_allowances_work_entry = work_entry_obj.search([('code', '=', 'ATTSHTLIVAL')])
        other_allowances_work_entry = work_entry_obj.search([('code', '=', 'ATTSHTOTHAL')])
        # internal_travel_allowances_work_entry = work_entry_obj.search([('code', '=', 'ATTSHTINTAL')])
        general_deductions_work_entry = work_entry_obj.search([('code', '=', 'ATTSHTGENAL')])

        medical_insurance_employee_work_entry = work_entry_obj.search([('code', '=', 'ATTSHTEMPDED')])
        medical_insurance_family_work_entry = work_entry_obj.search([('code', '=', 'ATTSHTFAMDED')])
        employee_insurance_amount_work_entry = work_entry_obj.search([('code', '=', 'ATTSHTEMPINSDED')])
        employee_gosi_work_entry = work_entry_obj.search([('code', '=', 'ATTSHTEMPGOSIDED')])
        employee_penalty_work_entry = work_entry_obj.search([('code', '=', 'ATTSHTPENDED')])
        business_trip_work_entry = work_entry_obj.search([('code', '=', 'ATTSHTBUSTR')])
        # residency_issuance_and_renewal_costs_work_entry = work_entry_obj.search([('code', '=', 'ATTSHTRESESSCOST')])

        # nature_of_work_allowances_work_entry = work_entry_obj.search([('code', '=', 'ATTSHTNATWORK')])
        # food_allowances_work_entry = work_entry_obj.search([('code', '=', 'ATTSHTFOODALOW')])
        # end_of_service_allowance_work_entry = work_entry_obj.search([('code', '=', 'ATTSHTENDSER')])
        # telephone_allowance_work_entry = work_entry_obj.search([('code', '=', 'ATTSHTTEL')])
        # contract_extension_work_entry = work_entry_obj.search([('code', '=', 'ATTSHTCONTALW')])
        # constant_refundable_advance_work_entry = work_entry_obj.search([('code', '=', 'ATTSHTCONTREFALW')])

        if not overtime_work_entry:
            raise ValidationError(_(
                'Please Add Work Entry Type For Attendance Sheet Overtime With Code ATTSHOT'))
        if not latin_work_entry:
            raise ValidationError(_(
                'Please Add Work Entry Type For Attendance Sheet Late In With Code ATTSHLI'))
        if not absence_work_entry:
            raise ValidationError(_(
                'Please Add Work Entry Type For Attendance Sheet Absence With Code ATTSHAB'))
        if not difftime_work_entry:
            raise ValidationError(_(
                'Please Add Work Entry Type For Attendance Sheet Diff Time With Code ATTSHDT'))

        # TODO _____________ AHMED SABER START CUSTOM work_entry _____________
        if not termination_indemnity_work_entry:
            raise ValidationError(_(
                'Please Add Work Entry Type For Attendance Sheet Diff Time With Code ATTSHTERM'))
        if not house_allowances_work_entry:
            raise ValidationError(_(
                'Please Add Work Entry Type For Attendance Sheet Diff Time With Code ATTSHTHOUSAL'))
        if not transport_allowances_work_entry:
            raise ValidationError(_(
                'Please Add Work Entry Type For Attendance Sheet Diff Time With Code ATTSHTTARNSAL'))
        # if not living_allowances_work_entry:
        #     raise ValidationError(_(
        #         'Please Add Work Entry Type For Attendance Sheet Diff Time With Code ATTSHTLIVAL'))
        if not other_allowances_work_entry:
            raise ValidationError(_(
                'Please Add Work Entry Type For Attendance Sheet Diff Time With Code ATTSHTOTHAL'))
        # if not internal_travel_allowances_work_entry:
        #     raise ValidationError(_(
        #         'Please Add Work Entry Type For Attendance Sheet Diff Time With Code ATTSHTINTAL'))
        if not general_deductions_work_entry:
            raise ValidationError(_(
                'Please Add Work Entry Type For Attendance Sheet Diff Time With Code ATTSHTGENAL'))
        if not medical_insurance_employee_work_entry:
            raise ValidationError(_(
                'Please Add Work Entry Type For Attendance Sheet Diff Time With Code ATTSHTEMPDED'))
        if not medical_insurance_family_work_entry:
            raise ValidationError(_(
                'Please Add Work Entry Type For Attendance Sheet Diff Time With Code ATTSHTFAMDED'))
        if not employee_insurance_amount_work_entry:
            raise ValidationError(_(
                'Please Add Work Entry Type For Attendance Sheet Diff Time With Code ATTSHTEMPINSDED'))
        if not employee_gosi_work_entry:
            raise ValidationError(_(
                'Please Add Work Entry Type For Attendance Sheet Diff Time With Code ATTSHTEMPGOSIDED'))
        if not employee_penalty_work_entry:
            raise ValidationError(_(
                'Please Add Work Entry Type For Attendance Sheet Diff Time With Code ATTSHTPENDED'))
        if not business_trip_work_entry:
            raise ValidationError(_(
                'Please Add Work Entry Type For Attendance Sheet Diff Time With Code ATTSHTBUSTR'))
        # if not residency_issuance_and_renewal_costs_work_entry:
        #     raise ValidationError(_(
        #         'Please Add Work Entry Type For Attendance Sheet Diff Time With Code ATTSHTRESESSCOST'))

        # if not nature_of_work_allowances_work_entry:
        #     raise ValidationError(_(
        #         'Please Add Work Entry Type For Attendance Sheet Diff Time With Code ATTSHTNATWORK'))
        # if not food_allowances_work_entry:
        #     raise ValidationError(_(
        #         'Please Add Work Entry Type For Attendance Sheet Diff Time With Code ATTSHTFOODALOW'))
        # if not end_of_service_allowance_work_entry:
        #     raise ValidationError(_(
        #         'Please Add Work Entry Type For Attendance Sheet Diff Time With Code ATTSHTENDSER'))
        # if not telephone_allowance_work_entry:
        #     raise ValidationError(_(
        #         'Please Add Work Entry Type For Attendance Sheet Diff Time With Code ATTSHTTEL'))
        # if not contract_extension_work_entry:
        #     raise ValidationError(_(
        #         'Please Add Work Entry Type For Attendance Sheet Diff Time With Code ATTSHTCONTALW'))
        # if not constant_refundable_advance_work_entry:
        #     raise ValidationError(_(
        #         'Please Add Work Entry Type For Attendance Sheet Diff Time With Code ATTSHTCONTREFALW'))

        # TODO _____________ AHMED SABER END CUSTOM work_entry _____________

        # TODO _____________ AHMED SABER START CUSTOM SALARY ROLES _____________
        termination_indemnity_allowance = [{
            'name': "TERMINATION ALLOWANCE",
            'code': 'TERMINATION',
            'work_entry_type_id': termination_indemnity_work_entry[0].id,
            'sequence': 50,
            'number_of_days': 0,
            'number_of_hours': self.termination_indemnity,
        }]
        house_allowances = [{
            'name': "House Allowance",
            'code': 'HouseAllowance',
            'work_entry_type_id': house_allowances_work_entry[0].id,
            'sequence': 55,
            'number_of_days': 0,
            'number_of_hours': self.house_allowances,
        }]
        transport_allowances = [{
            'name': "Transport ALLOWANCE",
            'code': 'TransportALLOWANCE',
            'work_entry_type_id': transport_allowances_work_entry[0].id,
            'sequence': 60,
            'number_of_days': 0,
            'number_of_hours': self.transport_allowances,
        }]
        # living_allowances = [{
        #     'name': "living ALLOWANCE",
        #     'code': 'livingALLOWANCE',
        #     'work_entry_type_id': living_allowances_work_entry[0].id,
        #     'sequence': 65,
        #     'number_of_days': 0,
        #     'number_of_hours': self.living_allowances,
        # }]
        other_allowances = [{
            'name': "Other ALLOWANCE",
            'code': 'OtherALLOWANCE',
            'work_entry_type_id': other_allowances_work_entry[0].id,
            'sequence': 70,
            'number_of_days': 0,
            'number_of_hours': self.other_allowances,
        }]
        # internal_travel_allowance = [{
        #     'name': "Internal Travel ALLOWANCE",
        #     'code': 'InternalTravelALLOWANCE',
        #     'work_entry_type_id': internal_travel_allowances_work_entry[0].id,
        #     'sequence': 75,
        #     'number_of_days': 0,
        #     'number_of_hours': self.internal_travel_allowances,
        # }]
        general_deductions = [{
            'name': "General Deductions",
            'code': 'GeneralDeductions',
            'work_entry_type_id': general_deductions_work_entry[0].id,
            'sequence': 80,
            'number_of_days': 0,
            'number_of_hours': self.general_deductions,
        }]

        medical_insurance_employee_deduction = [{
            'name': "Medical Insurance Employee",
            'code': 'MedicalInsuranceEmployee',
            'work_entry_type_id': medical_insurance_employee_work_entry[0].id,
            'sequence': 85,
            'number_of_days': 0,
            'number_of_hours': self.medical_insurance_employee,
        }]
        medical_insurance_family_deduction = [{
            'name': "Medical Insurance Family",
            'code': 'MedicalInsuranceFamily',
            'work_entry_type_id': medical_insurance_family_work_entry[0].id,
            'sequence': 90,
            'number_of_days': 0,
            'number_of_hours': self.medical_insurance_family,
        }]
        employee_insurance_amount_deduction = [{
            'name': "Employee Insurance Amount",
            'code': 'EmployeeInsuranceAmount',
            'work_entry_type_id': employee_insurance_amount_work_entry[0].id,
            'sequence': 95,
            'number_of_days': 0,
            'number_of_hours': self.employee_insurance_amount,
        }]
        employee_gosi_deduction = [{
            'name': "Employee Gosi",
            'code': 'EmployeeGosi',
            'work_entry_type_id': employee_gosi_work_entry[0].id,
            'sequence': 100,
            'number_of_days': 0,
            'number_of_hours': self.employee_gosi,
        }]
        employee_penalty_deduction = [{
            'name': "Employee Penalty",
            'code': 'EmployeePenalty',
            'work_entry_type_id': employee_penalty_work_entry[0].id,
            'sequence': 105,
            'number_of_days': 0,
            'number_of_hours': self.penalty,
        }]
        business_trip_deduction = [{
            'name': "Business Trip",
            'code': 'BusinessTrip',
            'work_entry_type_id': business_trip_work_entry[0].id,
            'sequence': 110,
            'number_of_days': 0,
            'number_of_hours': self.business_trip,
        }]
        # residency_issuance_and_renewal_costs_deduction = [{
        #     'name': "Residency Issuance And Renewal Costs",
        #     'code': 'ResidencyIssuanceAndRenewalCosts',
        #     'work_entry_type_id': residency_issuance_and_renewal_costs_work_entry[0].id,
        #     'sequence': 115,
        #     'number_of_days': 0,
        #     'number_of_hours': self.residency_issuance_and_renewal_costs,
        # }]

        # nature_of_work_allowances = [{
        #     'name': "Nature Of Work Allowances",
        #     'code': 'NatureOfWorkAllowances',
        #     'work_entry_type_id': nature_of_work_allowances_work_entry[0].id,
        #     'sequence': 120,
        #     'number_of_days': 0,
        #     'number_of_hours': self.nature_of_work_allowances,
        # }]

        # food_allowances = [{
        #     'name': "Food Allowances",
        #     'code': 'FoodAllowances',
        #     'work_entry_type_id': food_allowances_work_entry[0].id,
        #     'sequence': 125,
        #     'number_of_days': 0,
        #     'number_of_hours': self.food_allowances,
        # }]

        # end_of_service_allowance = [{
        #     'name': "EndOfServiceAllowance",
        #     'code': 'End Of Service Allowance',
        #     'work_entry_type_id': end_of_service_allowance_work_entry[0].id,
        #     'sequence': 130,
        #     'number_of_days': 0,
        #     'number_of_hours': self.end_of_service_allowance,
        # }]

        # telephone_allowance = [{
        #     'name': "TelephoneAllowance",
        #     'code': 'Telephone Allowance',
        #     'work_entry_type_id': telephone_allowance_work_entry[0].id,
        #     'sequence': 135,
        #     'number_of_days': 0,
        #     'number_of_hours': self.telephone_allowance,
        # }]

        # contract_extension_allowances = [{
        #     'name': "Contract Extension Allowance",
        #     'code': 'ContractExtensionAllowance',
        #     'work_entry_type_id': contract_extension_work_entry[0].id,
        #     'sequence': 140,
        #     'number_of_days': 0,
        #     'number_of_hours': self.contract_extension,
        # }]
        # constant_refundable_advance = [{
        #     'name': "Refundable Advance Allowance",
        #     'code': 'RefundableAdvanceAllowance',
        #     'work_entry_type_id': constant_refundable_advance_work_entry[0].id,
        #     'sequence': 145,
        #     'number_of_days': 0,
        #     'number_of_hours': self.constant_refundable_advance,
        # }]

        # TODO _____________ AHMED SABER END CUSTOM SALARY ROLES _____________

        overtime = [{
            'name': "Overtime",
            'code': 'OVT',
            'work_entry_type_id': overtime_work_entry[0].id,
            'sequence': 30,
            'number_of_days': self.no_overtime,
            'number_of_hours': self.tot_overtime,
        }]
        absence = [{
            'name': "Absence",
            'code': 'ABS',
            'work_entry_type_id': absence_work_entry[0].id,
            'sequence': 35,
            'number_of_days': self.no_absence,
            'number_of_hours': self.tot_absence,
        }]
        late = [{
            'name': "Late In",
            'code': 'LATE',
            'work_entry_type_id': latin_work_entry[0].id,
            'sequence': 40,
            'number_of_days': self.no_late,
            'number_of_hours': self.tot_late,
        }]
        difftime = [{
            'name': "Difference time",
            'code': 'DIFFT',
            'work_entry_type_id': difftime_work_entry[0].id,
            'sequence': 45,
            'number_of_days': self.no_difftime,
            'number_of_hours': self.tot_difftime,
        }]
        worked_days_lines = overtime + late + absence + difftime + termination_indemnity_allowance + house_allowances + transport_allowances + other_allowances + general_deductions + medical_insurance_employee_deduction + medical_insurance_family_deduction + employee_insurance_amount_deduction + employee_gosi_deduction + employee_penalty_deduction + business_trip_deduction
        return worked_days_lines

    def create_payslip(self):
        payslips = self.env['hr.payslip']
        for att_sheet in self:
            if att_sheet.payslip_id:
                continue
            from_date = att_sheet.date_from
            to_date = att_sheet.date_to
            employee = att_sheet.employee_id
            slip_data = self.env['hr.payslip'].onchange_employee_id(from_date,
                                                                    to_date,
                                                                    employee.id,
                                                                    contract_id=False)
            contract_id = slip_data['value'].get('contract_id')
            if not contract_id:
                raise exceptions.Warning(
                    'There is No Contracts for %s That covers the period of the Attendance sheet' % employee.name)
            worked_days_line_ids = slip_data['value'].get(
                'worked_days_line_ids')
            # TODO _____________ AHMED SABER START CUSTOM SALARY ROLES _____________

            termination_indemnity_allowance = [{
                'name': "TERMINATION ALLOWANCE",
                'code': 'TERMINATION',
                'contract_id': contract_id,
                'sequence': 50,
                'number_of_days': att_sheet.termination_indemnity,
                'number_of_hours': att_sheet.termination_indemnity,
            }]
            house_allowances = [{
                'name': "House Allowance",
                'code': 'HouseAllowance',
                'contract_id': contract_id,
                'sequence': 55,
                'number_of_days': att_sheet.house_allowances,
                'number_of_hours': att_sheet.house_allowances,
            }]
            # transport_allowances = [{
            #     'name': "Transport ALLOWANCE",
            #     'code': 'TransportALLOWANCE',
            #     'contract_id': contract_id,
            #     'sequence': 60,
            #     'number_of_days': att_sheet.transport_allowances,
            #     'number_of_hours': att_sheet.transport_allowances,
            # }]
            living_allowances = [{
                'name': "living ALLOWANCE",
                'code': 'livingALLOWANCE',
                'contract_id': contract_id,
                'sequence': 65,
                'number_of_days': att_sheet.living_allowances,
                'number_of_hours': att_sheet.living_allowances,
            }]
            other_allowances = [{
                'name': "Other ALLOWANCE",
                'code': 'OtherALLOWANCE',
                'contract_id': contract_id,
                'sequence': 70,
                'number_of_days': att_sheet.other_allowances,
                'number_of_hours': att_sheet.other_allowances,
            }]
            # internal_travel_allowance = [{
            #     'name': "Internal Travel ALLOWANCE",
            #     'code': 'InternalTravelALLOWANCE',
            #     'contract_id': contract_id,
            #     'sequence': 75,
            #     'number_of_days': att_sheet.internal_travel_allowances,
            #     'number_of_hours': att_sheet.internal_travel_allowances,
            # }]
            general_deductions = [{
                'name': "General Deductions",
                'code': 'GeneralDeductions',
                'contract_id': contract_id,
                'sequence': 80,
                'number_of_days': att_sheet.general_deductions,
                'number_of_hours': att_sheet.general_deductions,
            }]

            medical_insurance_employee_deduction = [{
                'name': "Medical Insurance Employee",
                'code': 'MedicalInsuranceEmployee',
                'contract_id': contract_id,
                'sequence': 85,
                'number_of_days': att_sheet.medical_insurance_employee,
                'number_of_hours': att_sheet.medical_insurance_employee,
            }]
            medical_insurance_family_deduction = [{
                'name': "Medical Insurance Family",
                'code': 'MedicalInsuranceFamily',
                'contract_id': contract_id,
                'sequence': 90,
                'number_of_days': att_sheet.medical_insurance_family,
                'number_of_hours': att_sheet.medical_insurance_family,
            }]
            employee_insurance_amount_deduction = [{
                'name': "Employee Insurance Amount",
                'code': 'EmployeeInsuranceAmount',
                'contract_id': contract_id,
                'sequence': 95,
                'number_of_days': att_sheet.employee_insurance_amount,
                'number_of_hours': att_sheet.employee_insurance_amount,
            }]
            employee_gosi_deduction = [{
                'name': "Employee Gosi",
                'code': 'EmployeeGosi',
                'contract_id': contract_id,
                'sequence': 100,
                'number_of_days': att_sheet.employee_gosi,
                'number_of_hours': att_sheet.employee_gosi,
            }]

            employee_penalty_deduction = [{
                'name': "Employee Penalty",
                'code': 'EmployeePenalty',
                'contract_id': contract_id,
                'sequence': 105,
                'number_of_days': att_sheet.penalty,
                'number_of_hours': att_sheet.penalty,
            }]

            business_trip_deduction = [{
                'name': "Business Trip",
                'code': 'BusinessTrip',
                'contract_id': contract_id,
                'sequence': 110,
                'number_of_days': att_sheet.business_trip,
                'number_of_hours': att_sheet.business_trip,
            }]

            # residency_issuance_and_renewal_costs_deduction = [{
            #     'name': "Residency Issuance And Renewal Costs",
            #     'code': 'ResidencyIssuanceAndRenewalCosts',
            #     'contract_id': contract_id,
            #     'sequence': 115,
            #     'number_of_days': att_sheet.residency_issuance_and_renewal_costs,
            #     'number_of_hours': att_sheet.residency_issuance_and_renewal_costs,
            # }]

            # nature_of_work_allowances = [{
            #     'name': "Nature Of Work Allowances",
            #     'code': 'NatureOfWorkAllowances',
            #     'contract_id': contract_id,
            #     'sequence': 120,
            #     'number_of_days': att_sheet.nature_of_work_allowances,
            #     'number_of_hours': att_sheet.nature_of_work_allowances,
            # }]

            # food_allowances = [{
            #     'name': "Food Allowances",
            #     'code': 'FoodAllowances',
            #     'contract_id': contract_id,
            #     'sequence': 125,
            #     'number_of_days': att_sheet.food_allowances,
            #     'number_of_hours': att_sheet.food_allowances,
            # }]

            # end_of_service_allowance = [{
            #     'name': "EndOfServiceAllowance",
            #     'code': 'End Of Service Allowance',
            #     'contract_id': contract_id,
            #     'sequence': 130,
            #     'number_of_days': att_sheet.end_of_service_allowance,
            #     'number_of_hours': att_sheet.end_of_service_allowance,
            # }]

            # telephone_allowance = [{
            #     'name': "TelephoneAllowance",
            #     'code': 'Telephone Allowance',
            #     'contract_id': contract_id,
            #     'sequence': 135,
            #     'number_of_days': att_sheet.telephone_allowance,
            #     'number_of_hours': att_sheet.telephone_allowance,
            # }]

            # contract_extension_allowances = [{
            #     'name': "Contract Extension Allowance",
            #     'code': 'ContractExtensionAllowance',
            #     'contract_id': contract_id,
            #     'sequence': 140,
            #     'number_of_days': att_sheet.contract_extension,
            #     'number_of_hours': att_sheet.contract_extension,
            # }]

            # constant_refundable_advance = [{
            #     'name': "Refundable Advance Allowance",
            #     'code': 'RefundableAdvanceAllowance',
            #     'contract_id': contract_id,
            #     'sequence': 145,
            #     'number_of_days': att_sheet.constant_refundable_advance,
            #     'number_of_hours': att_sheet.constant_refundable_advance,
            # }]
            # TODO _____________ AHMED SABER END CUSTOM SALARY ROLES _____________

            overtime = [{
                'name': "Overtime",
                'code': 'OVT',
                'contract_id': contract_id,
                'sequence': 30,
                'number_of_days': att_sheet.no_overtime,
                'number_of_hours': att_sheet.tot_overtime,
            }]
            absence = [{
                'name': "Absence",
                'code': 'ABS',
                'contract_id': contract_id,
                'sequence': 35,
                'number_of_days': att_sheet.no_absence,
                'number_of_hours': att_sheet.tot_absence,
            }]
            late = [{
                'name': "Late In",
                'code': 'LATE',
                'contract_id': contract_id,
                'sequence': 40,
                'number_of_days': att_sheet.no_late,
                'number_of_hours': att_sheet.tot_late,
            }]
            difftime = [{
                'name': "Difference time",
                'code': 'DIFFT',
                'contract_id': contract_id,
                'sequence': 45,
                'number_of_days': att_sheet.no_difftime,
                'number_of_hours': att_sheet.tot_difftime,
            }]
            worked_days_line_ids += overtime + late + absence + difftime + termination_indemnity_allowance + house_allowances + living_allowances + other_allowances + general_deductions + medical_insurance_employee_deduction + medical_insurance_family_deduction + employee_insurance_amount_deduction + employee_gosi_deduction + employee_penalty_deduction + business_trip_deduction

            res = {
                'employee_id': employee.id,
                'name': slip_data['value'].get('name'),
                'struct_id': slip_data['value'].get('struct_id'),
                'contract_id': contract_id,
                'input_line_ids': [(0, 0, x) for x in
                                   slip_data['value'].get('input_line_ids')],
                'worked_days_line_ids': [(0, 0, x) for x in
                                         worked_days_line_ids],
                'date_from': from_date,
                'date_to': to_date,
            }
            new_payslip = self.env['hr.payslip'].create(res)
            att_sheet.payslip_id = new_payslip
            payslips += new_payslip
        return payslips


class AttendanceSheetLine(models.Model):
    _name = 'attendance.sheet.line'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('sum', 'Summary'),
        ('confirm', 'Confirmed'),
        ('done', 'Approved')], related='att_sheet_id.state', store=True, )

    date = fields.Date("Date")
    day = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], 'Day of Week', required=True, index=True, )
    att_sheet_id = fields.Many2one(comodel_name='attendance.sheet',
                                   ondelete="cascade",
                                   string='Attendance Sheet', readonly=True)
    employee_id = fields.Many2one(related='att_sheet_id.employee_id',
                                  string='Employee')
    pl_sign_in = fields.Float("Planned sign in", readonly=True)
    pl_sign_out = fields.Float("Planned sign out", readonly=True)
    worked_hours = fields.Float("Worked Hours", readonly=True)
    ac_sign_in = fields.Float("Actual sign in", readonly=True)
    ac_sign_out = fields.Float("Actual sign out", readonly=True)
    overtime = fields.Float("Overtime", readonly=True)
    act_overtime = fields.Float("Actual Overtime", readonly=True)
    late_in = fields.Float("Late In", readonly=True)
    diff_time = fields.Float("Diff Time",
                             help="Diffrence between the working time and attendance time(s) ",
                             readonly=True)
    act_late_in = fields.Float("Actual Late In", readonly=True)
    act_diff_time = fields.Float("Actual Diff Time",
                                 help="Diffrence between the working time and attendance time(s) ",
                                 readonly=True)
    status = fields.Selection(string="Status",
                              selection=[('ab', 'Absence'),
                                         ('weekend', 'Week End'),
                                         ('ph', 'Public Holiday'),
                                         ('leave', 'Leave'), ],
                              required=False, readonly=True)
    note = fields.Text("Note", readonly=True)
