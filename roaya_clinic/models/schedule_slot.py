from odoo import models, fields, api


class ClinicScheduleSlot(models.Model):
    _name = "clinic.schedule.slot"
    _description = "Doctor Schedule Slot"
    _order = "schedule_id, start_time"

    name = fields.Char(
        compute="_compute_name",
        store=True
    )

    active = fields.Boolean(default=True)

    schedule_id = fields.Many2one(
        "clinic.schedule",
        string="Schedule",
        required=True,
        ondelete="cascade",
    )

    doctor_id = fields.Many2one(
        related="schedule_id.doctor_id",
        store=True,
        readonly=True,
    )

    specialty_id = fields.Many2one(
        related="schedule_id.specialty_id",
        store=True,
        readonly=True,
    )

    weekday = fields.Selection(
        related="schedule_id.weekday",
        store=True,
        readonly=True,
    )

    start_time = fields.Float(
        required=True
    )

    end_time = fields.Float(
        required=True
    )

    is_booked = fields.Boolean(
        string="Booked",
        default=False
    )

    @api.depends(
        "doctor_id",
        "start_time",
        "end_time",
    )
    def _compute_name(self):

        for rec in self:

            rec.name = "%s | %.2f - %.2f" % (

                rec.doctor_id.name or "",

                rec.start_time,

                rec.end_time,

            )