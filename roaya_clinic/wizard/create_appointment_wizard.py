from odoo import models, fields, api
from odoo.exceptions import ValidationError

WEEKDAY_MAP = {
    6: "sun", 0: "mon", 1: "tue", 2: "wed",
    3: "thu", 4: "fri", 5: "sat",
}


class CreateAppointmentWizard(models.TransientModel):
    _name = "create.appointment.wizard"
    _description = "Create Appointment Wizard"

    slot_id = fields.Many2one(
        "clinic.schedule.slot",
        string="Slot",
        required=True,
        domain="[('id', 'in', available_slot_ids)]",
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

    start_time = fields.Float(string="Start Time", readonly=True)
    end_time = fields.Float(string="End Time", readonly=True)
    consultation_fee = fields.Float(string="Consultation Fee", readonly=True)

    reason = fields.Text(string="Reason")
    notes = fields.Text(string="Notes")

    is_today = fields.Boolean(compute="_compute_is_today")

    available_slot_ids = fields.Many2many(
        "clinic.schedule.slot",
        compute="_compute_available_slot_ids",
    )

    # -------------------------
    # AVAILABLE SLOTS (drives the domain shown in the view)
    # -------------------------
    @api.depends("doctor_id", "date")
    def _compute_available_slot_ids(self):
        for rec in self:
            if not (rec.doctor_id and rec.date):
                rec.available_slot_ids = False
                continue

            day = WEEKDAY_MAP[rec.date.weekday()]

            all_slots = self.env["clinic.schedule.slot"].search([
                ("doctor_id", "=", rec.doctor_id.id),
                ("weekday", "=", day),
            ])

            # Check against ALL existing appointments for this doctor/date,
            # regardless of whether they have a slot_id set (e.g. portal
            # bookings that only carry start_time/end_time). This keeps the
            # availability check consistent with clinic.appointment's own
            # _check_overlap constraint, which compares actual times, not
            # slot_id equality.
            existing_appointments = self.env["clinic.appointment"].search([
                ("doctor_id", "=", rec.doctor_id.id),
                ("date", "=", rec.date),
                ("state", "!=", "cancelled"),
            ])

            available = all_slots
            for appt in existing_appointments:
                if not (appt.start_time and appt.end_time):
                    continue
                available = available.filtered(
                    lambda s: not (
                        s.start_time < appt.end_time and s.end_time > appt.start_time
                    )
                )

            rec.available_slot_ids = available

    @api.onchange("doctor_id")
    def _onchange_doctor_id(self):
        if self.doctor_id:
            self.specialty_id = self.doctor_id.specialty_id
            self.consultation_fee = self.doctor_id.consultation_fee

    @api.onchange("doctor_id", "date")
    def _onchange_doctor_date(self):
        self.slot_id = False

        if not (self.doctor_id and self.date):
            return

        if not self.available_slot_ids:
            day = WEEKDAY_MAP[self.date.weekday()]
            has_schedule = self.env["clinic.schedule.slot"].search_count([
                ("doctor_id", "=", self.doctor_id.id),
                ("weekday", "=", day),
            ])
            if not has_schedule:
                return {
                    "warning": {
                        "title": "No Schedule",
                        "message": "This doctor has no scheduled slots on the selected day of the week.",
                    },
                }
            return {
                "warning": {
                    "title": "No Available Slots",
                    "message": "All slots for this doctor on the selected date are already booked.",
                },
            }

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
            raise ValidationError("You cannot book an appointment in the past.")

        day = WEEKDAY_MAP[self.date.weekday()]

        schedule = self.env["clinic.schedule"].search([
            ("doctor_id", "=", self.doctor_id.id),
            ("weekday", "=", day),
        ], limit=1)

        if not schedule:
            raise ValidationError("Doctor is not available on the selected day.")

        existing = self.env["clinic.appointment"].search([
            ("slot_id", "=", self.slot_id.id),
            ("date", "=", self.date),
            ("state", "!=", "cancelled"),
        ], limit=1)

        if existing:
            raise ValidationError("This slot is already booked for the selected date.")

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