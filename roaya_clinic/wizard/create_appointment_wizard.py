from odoo import models, fields, api
from odoo.exceptions import ValidationError


class CreateAppointmentWizard(models.TransientModel):
    _name = "create.appointment.wizard"
    _description = "Create Appointment Wizard"

    slot_id = fields.Many2one(
        "clinic.schedule.slot",
        string="Slot",
        required=True,
    )

    patient_id = fields.Many2one(
        "clinic.patient",
        string="Patient",
        required=True,
        readonly=True,
    )

    doctor_id = fields.Many2one(
        "clinic.doctor",
        string="Doctor",
        required=True,
    )

    specialty_id = fields.Many2one(
        "clinic.specialty",
        string="Specialty",
        readonly=True,
    )

    date = fields.Date(
        string="Date",
        required=True,
    )

    start_time = fields.Float(
        string="Start Time",
        readonly=True,
    )

    end_time = fields.Float(
        string="End Time",
        readonly=True,
    )

    consultation_fee = fields.Float(
        string="Consultation Fee",
        readonly=True,
    )

    reason = fields.Text(string="Reason")
    notes = fields.Text(string="Notes")

    is_today = fields.Boolean(
        compute="_compute_is_today",
    )

    # -------------------------
    # ONCHANGE DOCTOR
    # -------------------------
    @api.onchange("doctor_id")
    def _onchange_doctor_id(self):
        if self.doctor_id:
            self.specialty_id = self.doctor_id.specialty_id
            self.consultation_fee = self.doctor_id.consultation_fee

    # -------------------------
    # ONCHANGE SLOT
    # -------------------------
    @api.onchange("slot_id")
    def _onchange_slot_id(self):
        if self.slot_id:
            self.start_time = self.slot_id.start_time
            self.end_time = self.slot_id.end_time

    # -------------------------
    # IS TODAY
    # -------------------------
    @api.depends("date")
    def _compute_is_today(self):
        today = fields.Date.today()
        for rec in self:
            rec.is_today = rec.date == today

    # -------------------------
    # CREATE APPOINTMENT
    # -------------------------
    def action_create_appointment(self):
        self.ensure_one()

        if self.date < fields.Date.today():
            raise ValidationError(
                "You cannot book an appointment in the past."
            )

        weekday_map = {
            6: "sun",
            0: "mon",
            1: "tue",
            2: "wed",
            3: "thu",
            4: "fri",
            5: "sat",
        }

        day = weekday_map[self.date.weekday()]
             
             
        print("Selected Date:", self.date)
        print("Weekday:", day)
             
        schedule = self.env["clinic.schedule"].search(
            [
                ("doctor_id", "=", self.doctor_id.id),
                ("weekday", "=", day),
            ],
            limit=1,
        )

        if not schedule:
            raise ValidationError(
                "Doctor is not available on the selected day."
            )

        if self.slot_id.is_booked:
            raise ValidationError(
                "This slot is already booked."
            )

        appointment = self.env["clinic.appointment"].create({
            "patient_id": self.patient_id.id,
            "doctor_id": self.doctor_id.id,
            "date": self.date,
            "slot_id": self.slot_id.id,
            "start_time": self.slot_id.start_time,
            "end_time": self.slot_id.end_time,
            "reason": self.reason,
            "notes": self.notes,
        })

        appointment.action_confirm()

        return {
            "type": "ir.actions.act_window",
            "name": "Appointment",
            "res_model": "clinic.appointment",
            "res_id": appointment.id,
            "view_mode": "form",
            "target": "current",
        }