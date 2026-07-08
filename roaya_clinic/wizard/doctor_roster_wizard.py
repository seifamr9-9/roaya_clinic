from odoo import models, fields, api
from odoo.exceptions import UserError


class ClinicDoctorRosterWizard(models.TransientModel):
    _name = "clinic.doctor.roster.wizard"
    _description = "Doctor Daily Patient Roster Wizard"

    doctor_id = fields.Many2one(
        "clinic.doctor", required=True, string="Doctor"
    )
    date = fields.Date(
        required=True, default=fields.Date.context_today, string="Date"
    )

    def _get_appointment_domain(self):
        self.ensure_one()
        return [
            ("doctor_id", "=", self.doctor_id.id),
            ("date", "=", self.date),
            ("state", "!=", "cancelled"),
        ]

    def _get_appointments(self):
        """Returns appointments for this doctor/date, ordered by start time."""
        self.ensure_one()
        return self.env["clinic.appointment"].search(
            self._get_appointment_domain(), order="start_time asc"
        )

    def action_print_pdf(self):
        self.ensure_one()
        if not self._get_appointments():
            raise UserError("No appointments found for this doctor on the selected date.")
        return self.env.ref(
            "roaya_clinic.action_report_doctor_roster"
        ).report_action(self)