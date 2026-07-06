from odoo import models, fields, api  # type: ignore[reportMissingImports]
from datetime import date
import re
from odoo.exceptions import ValidationError

class ClinicPatient(models.Model):
    _name = "clinic.patient"
    _description = "Clinic Patient"
    _order = "name"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    name = fields.Char(required=True)
    email = fields.Char(required=True, index=True)
    phone = fields.Char()
    mobile = fields.Char()
    date_of_birth = fields.Date()
    gender = fields.Selection(
        [
            ("male", "Male"),
            ("female", "Female"),
        ],
        string="Gender",
    )
    blood_type = fields.Selection(
        [
            ("a+", "A+"),
            ("a-", "A-"),
            ("b+", "B+"),
            ("b-", "B-"),
            ("ab+", "AB+"),
            ("ab-", "AB-"),
            ("o+", "O+"),
            ("o-", "O-"),
        ],
        string="Blood Type",
    )
    allergies = fields.Text()
    user_id = fields.Many2one("res.users", string="Portal User")
    lab_order_ids = fields.One2many(
        "clinic.lab_order",
        "patient_id",
        string="Lab Orders",
    )
    appointment_ids = fields.One2many(
        "clinic.appointment", "patient_id", string="Appointments"
    )

    active = fields.Boolean(default=True)
    age = fields.Integer(
    string="Age",
    compute="_compute_age",
    store=True,
    )
    image_1920 = fields.Image()
    
    
    appointment_ids = fields.One2many(
    'clinic.appointment',
    'patient_id',
    string='Appointments'
    )
    
    prescription_ids = fields.One2many(
    'clinic.prescription',
    'patient_id',
    string='Prescriptions'
    )
    
    _sql_constraints = [
        ("unique_email", "unique(email)", "Email must be unique!"),
    ]

    @api.depends("date_of_birth")
    def _compute_age(self):
        today = date.today()
        for record in self:
            if record.date_of_birth:
                record.age = (
                    today.year
                    - record.date_of_birth.year
                    - (
                        (today.month, today.day)
                        < (record.date_of_birth.month, record.date_of_birth.day)
                    )
                )
            else:
                record.age = 0

    def action_print_patient_medical_summary(self):
        return self.env.ref("roaya_clinic.action_report_patient_medical").report_action(
            self
        )
    
    
    
    @api.constrains('email')
    def _check_email(self):
        pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
        for rec in self:
            if rec.email and not re.fullmatch(pattern, rec.email):
                raise ValidationError("Please enter a valid email address.")

    def action_open_create_appointment_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Create Appointment",
            "res_model": "create.appointment.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_patient_id": self.id,
            },
        }
