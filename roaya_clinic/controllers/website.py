from odoo import http
from odoo.http import request

class SmartClinicWebsite(http.Controller):

    # Home page
    @http.route('/', type='http', auth='public', website=True)
    def home(self, **kwargs):
        docs = request.env['clinic.doctor'].sudo().search([('active', '=', True)], limit=4)
        specs = request.env['clinic.specialty'].sudo().search([('active', '=', True)], limit=6)
        values = {
            'doctors': docs, 'specialties': specs,
            'doctor_count': request.env['clinic.doctor'].sudo().search_count([]),
            'patient_count': request.env['clinic.patient'].sudo().search_count([]),
            'appointment_count': request.env['clinic.appointment'].sudo().search_count([]),
            'specialty_count': request.env['clinic.specialty'].sudo().search_count([]),
        }
        return request.render('smart_clinic.home_page', values)

    # Doctors page
    @http.route('/doctors', type='http', auth='public', website=True)
    def doctors(self, specialty_id=None, search=None, **kw):
        domain = [('active', '=', True)]
        if specialty_id: domain.append(('specialty_id', '=', int(specialty_id)))
        if search: domain.append(('name', 'ilike', search))
        return request.render('smart_clinic.doctors_page', {
            'doctors': request.env['clinic.doctor'].sudo().search(domain),
            'specialties': request.env['clinic.specialty'].sudo().search([('active', '=', True)]),
            'selected_specialty': int(specialty_id) if specialty_id else False,
            'search': search or '',
        })

    # Services page
    @http.route('/services', type='http', auth='public', website=True)
    def services(self, **kw):
        return request.render('smart_clinic.services_page', {
            'specialties': request.env['clinic.specialty'].sudo().search([('active', '=', True)])
        })

    # About page
    @http.route('/about', type='http', auth='public', website=True)
    def about(self, **kw):
        return request.render('smart_clinic.about_page', {
            'doctor_count': request.env['clinic.doctor'].sudo().search_count([]),
            'patient_count': request.env['clinic.patient'].sudo().search_count([]),
            'appointment_count': request.env['clinic.appointment'].sudo().search_count([]),
            'specialty_count': request.env['clinic.specialty'].sudo().search_count([]),
        })

    # Display appointment page
    @http.route('/appointment', type='http', auth='public', website=True)
    def website_appointment(self, doctor_id=None, **kw):
        patient = request.env['clinic.patient'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
        return request.render('smart_clinic.page_appointment', {
            'doctors': request.env['clinic.doctor'].sudo().search([('active', '=', True)]),
            'specialties': request.env['clinic.specialty'].sudo().search([('active', '=', True)]),
            'doctor_id': int(doctor_id) if doctor_id else False,
            'patient': patient,
        })

    # Confirm appointment, create lead (Removed Patient creation)
    @http.route('/appointment/confirm', type='http', auth='public', website=True, methods=['POST'])
    def confirm_appointment(self, **post):
        doctor_id, date, slot_id = post.get('doctor_id'), post.get('appointment_date'), post.get('slot_id')
        if not doctor_id or not date:
            return request.redirect('/appointment')

        patient_name = post.get('patient_name', 'Anonymous')
        patient_email = post.get('patient_email')

        start, end, slot = 9.0, 9.5, False
        if slot_id:
            slot = request.env['clinic.schedule.slot'].sudo().browse(int(slot_id))
            if slot.exists():
                start, end = slot.start_time, slot.end_time


        # Create CRM lead for follow-up
        request.env['crm.lead'].sudo().create({
            'name': 'New Lead from: %s' % patient_name,
            'partner_name': patient_name,
            'email_from': patient_email,
            'phone': post.get('patient_phone'),
            'doctor_id': int(doctor_id),

            'lead_source': 'website',
            'requested_appointment_datetime': date,
            'start_time': start,
            'end_time': end,

            'description': 'Clinic Appointment Request: %s' % post.get('notes', ''),
        })

        if slot and slot.exists():
            slot.sudo().write({'is_booked': True})

        return request.redirect('/appointment/success/0')
    # Success page
    @http.route('/appointment/success/<int:appointment_id>', type='http', auth='public', website=True)
    def appointment_success(self, appointment_id):
        return request.render('smart_clinic.page_appointment_success', {
            "appointment": request.env['clinic.appointment'].sudo().browse(appointment_id)
        })

    # Get available slots (AJAX)
    @http.route('/appointment/get_slots', type='json', auth='public', website=True)
    def get_slots(self, doctor_id=None, appointment_date=None):
        if not doctor_id: return []
        slots = request.env['clinic.schedule.slot'].sudo().search([
            ('doctor_id', '=', int(doctor_id)), ('active', '=', True), ('is_booked', '=', False)
        ])
        return [{'id': s.id, 'name': s.name, 'start_time': s.start_time, 'end_time': s.end_time} for s in slots]