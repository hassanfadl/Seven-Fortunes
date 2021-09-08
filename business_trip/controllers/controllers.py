# -*- coding: utf-8 -*-
from odoo import http

# class BusinessTrip(http.Controller):
#     @http.route('/business_trip/business_trip/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/business_trip/business_trip/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('business_trip.listing', {
#             'root': '/business_trip/business_trip',
#             'objects': http.request.env['business_trip.business_trip'].search([]),
#         })

#     @http.route('/business_trip/business_trip/objects/<model("business_trip.business_trip"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('business_trip.object', {
#             'object': obj
#         })