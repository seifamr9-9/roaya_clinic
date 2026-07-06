from odoo import models, fields


class LabOrderWizard(models.TransientModel):
    _name = "lab.order.wizard"
    _description = "Lab Order Wizard"

    appointment_id = fields.Many2one(
        "clinic.appointment",
        required=True,
    )

    patient_id = fields.Many2one(
        "clinic.patient",
        related="appointment_id.patient_id",
        readonly=True,
    )

    doctor_id = fields.Many2one(
        "clinic.doctor",
        related="appointment_id.doctor_id",
        readonly=True,
    )

    test_type = fields.Selection(
        [
            ("blood", "Blood"),
            ("urine", "Urine"),
            ("xray", "X-Ray"),
            ("ct", "CT Scan"),
            ("mri", "MRI"),
        ],
        required=True,
    )

    urgency = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("emergency", "Emergency"),
        ],
        default="medium",
    )

    description = fields.Text()

    def action_confirm(self):
        self.env["clinic.lab_order"].create(
            {
                "appointment_id": self.appointment_id.id,
                "test_type": self.test_type,
                "urgency": self.urgency,
                "description": self.description,
            }
        )

        return {"type": "ir.actions.act_window_close"}