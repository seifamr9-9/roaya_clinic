from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import timedelta


class ClinicScheduleSlot(models.Model):
    _name = "clinic.schedule.slot"
    _description = "Doctor Schedule Slot"
    _order = "schedule_id, start_time"

    name = fields.Char(compute="_compute_name", store=True)
    active = fields.Boolean(default=True)

    schedule_id = fields.Many2one(
        "clinic.schedule", string="Schedule", required=True, ondelete="cascade",
    )
    doctor_id = fields.Many2one(related="schedule_id.doctor_id", store=True, readonly=True)
    specialty_id = fields.Many2one(related="schedule_id.specialty_id", store=True, readonly=True)
    weekday = fields.Selection(related="schedule_id.weekday", store=True, readonly=True)

    start_time = fields.Float(required=True)
    end_time = fields.Float(required=True)

    # --- Replaces is_booked ---
    state = fields.Selection(
        [
            ("available", "Available"),
            ("reserved", "Reserved (Pending Confirmation)"),
            ("booked", "Booked"),
        ],
        string="Status",
        default="available",
        required=True,
        copy=False,
    )

    # Deadline for a 'reserved' slot before it auto-releases back to available
    reserved_until = fields.Datetime(string="Reserved Until", copy=False)

    # Kept for backward compatibility with any existing domain/report that
    # still reads is_booked; now just a mirror of state.
    is_booked = fields.Boolean(
        string="Booked", compute="_compute_is_booked", store=True,
    )

    @api.depends("state")
    def _compute_is_booked(self):
        for rec in self:
            rec.is_booked = rec.state != "available"

    @api.depends("doctor_id", "start_time", "end_time")
    def _compute_name(self):
        for rec in self:
            rec.name = "%s | %.2f - %.2f" % (
                rec.doctor_id.name or "", rec.start_time, rec.end_time,
            )

    # -------------------------------------------------
    # RESERVE (called from the website, source = CRM lead)
    # Locks the row at DB level to prevent two concurrent
    # requests from both reserving the same slot.
    # -------------------------------------------------
    def reserve_for_lead(self):
        self.ensure_one()
        self.env.cr.execute(
            "SELECT id FROM clinic_schedule_slot WHERE id = %s AND state = 'available' FOR UPDATE",
            (self.id,),
        )
        if not self.env.cr.fetchone():
            raise UserError(
                "This slot is no longer available. Please choose another time."
            )

        timeout_hours = float(
            self.env["ir.config_parameter"].sudo().get_param(
                "clinic.slot_reservation_hours", default=24
            )
        )
        self.write({
            "state": "reserved",
            "reserved_until": fields.Datetime.now() + timedelta(hours=timeout_hours),
        })

    # -------------------------------------------------
    # RESERVE + CONFIRM DIRECTLY (reception direct booking,
    # no pending phase needed since the receptionist IS the confirmation)
    # -------------------------------------------------
    def reserve_and_confirm(self):
        self.ensure_one()
        self.env.cr.execute(
            "SELECT id FROM clinic_schedule_slot WHERE id = %s AND state = 'available' FOR UPDATE",
            (self.id,),
        )
        if not self.env.cr.fetchone():
            raise UserError(
                "This slot is no longer available. Please choose another time."
            )
        self.write({"state": "booked", "reserved_until": False})

    # -------------------------------------------------
    # CONFIRM a slot that was already 'reserved' (CRM lead accepted)
    # -------------------------------------------------
    def confirm(self):
        for rec in self:
            rec.write({"state": "booked", "reserved_until": False})

    # -------------------------------------------------
    # RELEASE back to available (lead rejected / cancelled / expired)
    # -------------------------------------------------
    def release(self):
        for rec in self:
            rec.write({"state": "available", "reserved_until": False})

    # -------------------------------------------------
    # CRON: auto-release slots whose reservation window passed
    # -------------------------------------------------
    @api.model
    def _cron_release_expired_slots(self):
        now = fields.Datetime.now()
        expired_slots = self.search([
            ("state", "=", "reserved"),
            ("reserved_until", "<=", now),
        ])
        for slot in expired_slots:
            lead = self.env["crm.lead"].sudo().search(
                [("slot_id", "=", slot.id), ("appointment_id", "=", False)], limit=1
            )
            slot.release()
            if lead:
                lead.message_post(
                    body="Reservation expired without confirmation — slot released back to availability."
                )