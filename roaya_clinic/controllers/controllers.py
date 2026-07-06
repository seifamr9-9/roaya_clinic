# -*- coding: utf-8 -*-
# from odoo import http


# class SmartClinic(http.Controller):
#     @http.route('/smart_clinic/smart_clinic', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/smart_clinic/smart_clinic/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('smart_clinic.listing', {
#             'root': '/smart_clinic/smart_clinic',
#             'objects': http.request.env['smart_clinic.smart_clinic'].search([]),
#         })

#     @http.route('/smart_clinic/smart_clinic/objects/<model("smart_clinic.smart_clinic"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('smart_clinic.object', {
#             'object': obj
#         })

