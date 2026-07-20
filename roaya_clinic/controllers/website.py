from odoo import http, fields
from odoo.http import request
from odoo.exceptions import UserError


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
        return request.render('roaya_clinic.home_page', values)

    # Doctors page
    @http.route('/doctors', type='http', auth='public', website=True)
    def doctors(self, specialty_id=None, search=None, **kw):
        domain = [('active', '=', True)]
        if specialty_id:
            domain.append(('specialty_id', '=', int(specialty_id)))
        if search:
            domain.append(('name', 'ilike', search))
        return request.render('roaya_clinic.doctors_page', {
            'doctors': request.env['clinic.doctor'].sudo().search(domain),
            'specialties': request.env['clinic.specialty'].sudo().search([('active', '=', True)]),
            'selected_specialty': int(specialty_id) if specialty_id else False,
            'search': search or '',
        })

    # Services page
    @http.route('/services', type='http', auth='public', website=True)
    def services(self, **kw):
        return request.render('roaya_clinic.services_page', {
            'specialties': request.env['clinic.specialty'].sudo().search([('active', '=', True)])
        })

    # About page
    @http.route('/about', type='http', auth='public', website=True)
    def about(self, **kw):
        return request.render('roaya_clinic.about_page', {
            'doctor_count': request.env['clinic.doctor'].sudo().search_count([]),
            'patient_count': request.env['clinic.patient'].sudo().search_count([]),
            'appointment_count': request.env['clinic.appointment'].sudo().search_count([]),
            'specialty_count': request.env['clinic.specialty'].sudo().search_count([]),
        })

    # Display appointment page
    @http.route('/appointment', type='http', auth='public', website=True)
    def website_appointment(self, doctor_id=None, **kw):
        patient = request.env['clinic.patient'].sudo().search(
            [('user_id', '=', request.env.user.id)], limit=1
        )
        return request.render('roaya_clinic.page_appointment', {
            'doctors': request.env['clinic.doctor'].sudo().search([('active', '=', True)]),
            'specialties': request.env['clinic.specialty'].sudo().search([('active', '=', True)]),
            'doctor_id': int(doctor_id) if doctor_id else False,
            'patient': patient,
            # surfaced when we bounce the patient back here after a slot
            # got taken by someone else between page-load and submit
            'slot_error': kw.get('slot_error'),
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

        # Lock the slot for this lead BEFORE creating the lead. This is the
        # single source of truth for availability (sets state='reserved' +
        # reserved_until, with a row-level lock to prevent two patients
        # grabbing the same slot at once). If someone beat this patient to
        # it, bounce them back to the form instead of creating a lead for a
        # slot that's no longer theirs.
        if slot and slot.exists():
            try:
                slot.sudo().reserve_for_lead()
            except UserError:
                return request.redirect(
                    '/appointment?doctor_id=%s&slot_error=1' % doctor_id
                )

        # Create CRM lead for follow-up
        lead = request.env['crm.lead'].sudo().create({
            'name': 'New Lead from: %s' % patient_name,
            'partner_name': patient_name,
            'email_from': patient_email,
            'phone': post.get('patient_phone'),
            'mobile': post.get('patient_phone'),
            'doctor_id': int(doctor_id),

            'lead_source': 'website',
            'requested_appointment_datetime': date,
            'start_time': start,
            'end_time': end,
            'slot_id': slot.id if slot and slot.exists() else False,

            # These were previously collected on the form but never sent to
            # the lead, so they were silently lost before conversion.
            'patient_dob': post.get('patient_dob') or False,
            'patient_gender': post.get('patient_gender') or False,

            'description': 'Clinic Appointment Request: %s' % post.get('notes', ''),
        })

        return request.redirect('/appointment/success/0')

    # Success page
    @http.route('/appointment/success/<int:appointment_id>', type='http', auth='public', website=True)
    def appointment_success(self, appointment_id):
        return request.render('roaya_clinic.page_appointment_success', {
            "appointment": request.env['clinic.appointment'].sudo().browse(appointment_id)
        })

    # Get available slots (AJAX)
    @http.route('/appointment/get_slots', type='json', auth='public', website=True)
    def get_slots(self, doctor_id=None, appointment_date=None):
        if not doctor_id:
            return []

        domain = [
            ('doctor_id', '=', int(doctor_id)),
            ('active', '=', True),
            ('state', '=', 'available'),
        ]

        # Filter by the weekday matching the requested appointment date,
        # so we only return slots that actually belong to that day's schedule.
        if appointment_date:
            weekday_map = {0: 'mon', 1: 'tue', 2: 'wed', 3: 'thu', 4: 'fri', 5: 'sat', 6: 'sun'}
            try:
                date_obj = fields.Date.from_string(appointment_date)
                domain.append(('weekday', '=', weekday_map[date_obj.weekday()]))
            except Exception:
                # If the date can't be parsed, skip the weekday filter
                # rather than failing the whole request.
                pass

        slots = request.env['clinic.schedule.slot'].sudo().search(domain, order='start_time')
        return [
            {'id': s.id, 'name': s.name, 'start_time': s.start_time, 'end_time': s.end_time}
            for s in slots
        ]