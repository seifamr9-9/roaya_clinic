from odoo import models, fields, api


class ClinicLabOrder(models.Model):
    _name = "clinic.lab_order"
    _description = "Clinic Lab Order"
    _order = "ordered_date desc"

    name = fields.Char(default="New", readonly=True)

    appointment_id = fields.Many2one(
        "clinic.appointment",
        required=True,
        index=True,
    )

    patient_id = fields.Many2one(
        related="appointment_id.patient_id",
        store=True,
        readonly=True,
    )
    doctor_id = fields.Many2one(
        related="appointment_id.doctor_id",
        store=True,
        readonly=True,
    )

    test_type = fields.Selection(
        [
            ("blood", "Blood"),
            ("urine", "Urine"),
            ("xray", "X-Ray"),
            ("ct", "CT Scan"),
            ("mri", "MRI"),
        ]
    )

    description = fields.Text()

    urgency = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("emergency", "Emergency"),
        ]
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("ordered", "Ordered"),
            ("in_progress", "In Progress"),
            ("done", "Done"),
        ],
        default="draft",
    )

    result = fields.Text()

    ordered_date = fields.Date()

    completed_date = fields.Date()

    actual_cost = fields.Float()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = (
                self.env['ir.sequence'].next_by_code('clinic.lab_order') or 'New'
            )
        return super().create(vals_list)
