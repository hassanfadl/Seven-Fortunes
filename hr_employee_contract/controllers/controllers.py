# -*- coding: utf-8 -*-
# from odoo import http


# class HrEmployeeContract(http.Controller):
#     @http.route('/hr_employee_contract/hr_employee_contract/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_employee_contract/hr_employee_contract/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_employee_contract.listing', {
#             'root': '/hr_employee_contract/hr_employee_contract',
#             'objects': http.request.env['hr_employee_contract.hr_employee_contract'].search([]),
#         })

#     @http.route('/hr_employee_contract/hr_employee_contract/objects/<model("hr_employee_contract.hr_employee_contract"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_employee_contract.object', {
#             'object': obj
#         })
