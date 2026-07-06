from odoo import models, fields, api


class ClinicDoctor(models.Model):
    _name = "clinic.doctor"
    _description = "Clinic Doctor"
    _order = "name asc"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True)

    specialty_id = fields.Many2one(
        "clinic.specialty", string="Specialty", required=True, index=True, tracking=True
    )
    user_id = fields.Many2one("res.users", ondelete="set null", tracking=True)
    appointment_ids = fields.One2many(
        "clinic.appointment",
        "doctor_id",
        string="Appointments",
    )
    lab_order_ids = fields.One2many(
        "clinic.lab_order",
        "doctor_id",
        string="Lab Orders",
    )
    license_number = fields.Char(required=True, index=True)
    consultation_fee = fields.Float(tracking=True)

    weekday_schedule = fields.Selection(
        [
            ("mon", "Monday"),
            ("tue", "Tuesday"),
            ("wed", "Wednesday"),
            ("thu", "Thursday"),
            ("fri", "Friday"),
            ("sat", "Saturday"),
            ("sun", "Sunday"),
        ]
    )

    prescription_ids = fields.One2many(
    'clinic.prescription',
    'doctor_id',
    string='Prescriptions'
    )
    
    image_1920 = fields.Image()

    email = fields.Char(related="user_id.email", store=True, readonly=True)
    phone = fields.Char(related="user_id.phone", store=True, readonly=True)

    today_appointment_count = fields.Integer(compute="_compute_today_appointment_count")

    @api.depends("user_id")
    def _compute_today_appointment_count(self):
        today = fields.Date.today()
        for rec in self:
            rec.today_appointment_count = self.env["clinic.appointment"].search_count(
                [
                    ("doctor_id", "=", rec.id),
                    ("date", "=", today),
                    ("state", "!=", "cancelled"),
                ]
            )

    _sql_constraints = [
        (
            "unique_license_number",
            "unique(license_number)",
            "License number must be unique.",
        )
    ]

    is_published = fields.Boolean(default=True)

    
    
    

