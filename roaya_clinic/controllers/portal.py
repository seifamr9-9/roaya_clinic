from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal

class SmartClinicPortal(CustomerPortal):

    @http.route(['/my/clinic'], type='http', auth='user', website=True)
    def portal_dashboard(self, **kw):
        patient = request.env['clinic.patient'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
        appts = request.env['clinic.appointment'].sudo().search([('patient_id', '=', patient.id)])
        return request.render('roaya_clinic.portal_dashboard', {
            'patient': patient,
            'appointments_count': len(appts),
            'upcoming_count': len(appts.filtered(lambda a: a.state == 'confirmed')),
            'completed_count': len(appts.filtered(lambda a: a.state == 'done')),
        })

    @http.route(['/my/appointments'], type='http', auth='user', website=True)
    def portal_appointments(self, **kw):
        patient = request.env['clinic.patient'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
        return request.render('roaya_clinic.portal_appointments', {
            'appointments': request.env['clinic.appointment'].sudo().search([('patient_id', '=', patient.id)], order='date desc')
        })

    @http.route(['/my/appointments/<int:appointment_id>'], type='http', auth='user', website=True)
    def portal_appointment_details(self, appointment_id, **kw):
        patient = request.env['clinic.patient'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
        appt = request.env['clinic.appointment'].sudo().search([('id', '=', appointment_id), ('patient_id', '=', patient.id)], limit=1)
        if not appt: return request.redirect('/my/appointments')
        return request.render('roaya_clinic.portal_appointment_details', {'appointment': appt})

    @http.route(['/my/appointments/<int:appointment_id>/cancel'], type='http', auth='user', website=True)
    def portal_cancel_appointment(self, appointment_id, **kw):
        patient = request.env['clinic.patient'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
        appt = request.env['clinic.appointment'].sudo().search([('id', '=', appointment_id), ('patient_id', '=', patient.id)], limit=1)
        if appt: appt.write({'state': 'cancelled'})
        return request.redirect('/my/appointments')