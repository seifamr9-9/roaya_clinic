from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ClinicSchedule(models.Model):
    _name = "clinic.schedule"
    _description = "Doctor Schedule"
    _order = "doctor_id, weekday"

    name = fields.Char(
        compute="_compute_name",
        store=True
    )

    active = fields.Boolean(default=True)

    doctor_id = fields.Many2one(
        "clinic.doctor",
        required=True,
        ondelete="cascade",
    )

    specialty_id = fields.Many2one(
        related="doctor_id.specialty_id",
        store=True,
        readonly=True,
    )

    weekday = fields.Selection([
        ("sun", "Sunday"),
        ("mon", "Monday"),
        ("tue", "Tuesday"),
        ("wed", "Wednesday"),
        ("thu", "Thursday"),
        ("fri", "Friday"),
        ("sat", "Saturday"),
    ], required=True)

    start_time = fields.Float(
        required=True,
        default=9.0,
    )

    end_time = fields.Float(
        required=True,
        default=12.0,
    )

    slot_duration = fields.Integer(
        string="Slot Duration (Minutes)",
        default=30,
        required=True,
    )

    is_consultation = fields.Boolean(
        string="Consultation Day"
    )

    slot_ids = fields.One2many(
        "clinic.schedule.slot",
        "schedule_id",
        string="Generated Slots"
    )

    @api.depends("doctor_id", "weekday")
    def _compute_name(self):

        days = dict(self._fields["weekday"].selection)

        for rec in self:

            rec.name = "%s - %s" % (

                rec.doctor_id.name or "",

                days.get(rec.weekday, "")
            )

    @api.constrains("start_time", "end_time")
    def _check_time(self):

        for rec in self:

            if rec.start_time >= rec.end_time:
                raise ValidationError(
                    "End Time must be greater than Start Time."
                )

    def action_generate_slots(self):

        Slot = self.env["clinic.schedule.slot"]

        for schedule in self:

            if schedule.start_time >= schedule.end_time:
                raise ValidationError("Start time must be less than end time.")

            if schedule.slot_duration <= 0:
                raise ValidationError("Slot duration must be greater than 0.")

            schedule.slot_ids.unlink()

            current = schedule.start_time

            while current < schedule.end_time:

                next_time = current + (schedule.slot_duration / 60.0)

                if next_time > schedule.end_time:
                    next_time = schedule.end_time

                Slot.create({
                    "schedule_id": schedule.id,
                    "start_time": current,
                    "end_time": next_time,
                })

                current = next_time

        return {
            "type": "ir.actions.client",
            "tag": "reload",
        }