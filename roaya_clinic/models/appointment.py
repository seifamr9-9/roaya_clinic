from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, timedelta, datetime


class ClinicAppointment(models.Model):
    _name = "clinic.appointment"
    _description = "Clinic Appointment"
    _order = "date desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    name = fields.Char(default="New", readonly=True)

    patient_id = fields.Many2one(
        "clinic.patient", required=True, index=True, tracking=True
    )

    consultation_fee = fields.Float(
        string="Consultation Fee",
        related="doctor_id.consultation_fee",
        store=True,
        readonly=True,
    )
     
    slot_id = fields.Many2one("clinic.schedule.slot", string="Slot")     
    doctor_id = fields.Many2one(
        "clinic.doctor", required=True, index=True, tracking=True
    )

    specialty_id = fields.Many2one(
        related="doctor_id.specialty_id", store=True, readonly=True
    )

    date = fields.Date(required=True, index=True, tracking=True)

    start_time = fields.Float()
    end_time = fields.Float()

    duration_minutes = fields.Float(compute="_compute_duration", store=True)
    reminder_sent = fields.Boolean(default=False, copy=False)
    lab_order_ids = fields.One2many(
        "clinic.lab_order", "appointment_id", string="Lab Orders"
    )
    # prescription_ids = fields.One2many(
    #     "clinic.prescription", "appointment_id", string="Prescriptions"
    # )
    charge_ids = fields.One2many("clinic.charge", "appointment_id", string="Charges")
    charge_count = fields.Integer(compute="_compute_counts")
    lab_order_count = fields.Integer(compute="_compute_counts")
    prescription_count = fields.Integer(compute="_compute_counts")

    reason = fields.Text(tracking=True)
    notes = fields.Text()

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("checked_in", "Checked In"),
            ("in_progress", "In Progress"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
            ("no_show", "No Show"),
        ],
        default="draft",
        tracking=True,
    )

    is_today = fields.Boolean(compute="_compute_is_today")

    payment_status = fields.Selection(
        [
            ("current", "Current"),
            ("upcoming", "Upcoming"),
            ("overdue", "Overdue"),
        ],
        compute="_compute_payment_status",
        store=True,
    )

    prescription_ids = fields.One2many(
        "clinic.prescription",
        "appointment_id",
    )

    crm_lead_id = fields.Many2one("crm.lead", readonly=True)

    @api.depends("start_time", "end_time")
    def _compute_duration(self):
        for rec in self:
            rec.duration_minutes = (
                (rec.end_time - rec.start_time) * 60
                if rec.start_time and rec.end_time
                else 0
            )

    @api.depends("date")
    def _compute_is_today(self):
        for rec in self:
            rec.is_today = rec.date == date.today()

    @api.depends("charge_ids", "lab_order_ids", "prescription_ids")
    def _compute_counts(self):
        for rec in self:
            rec.charge_count = len(rec.charge_ids)
            rec.lab_order_count = len(rec.lab_order_ids)
            rec.prescription_count = len(rec.prescription_ids)

    @api.depends("date", "state")
    def _compute_payment_status(self):
        today = date.today()
        for rec in self:
            if rec.state == "done":
                rec.payment_status = "current"
            elif rec.date and rec.date > today:
                rec.payment_status = "upcoming"
            else:
                rec.payment_status = "overdue"

    @api.constrains("start_time", "end_time")
    def _check_time(self):
        for rec in self:
            if rec.start_time and rec.end_time and rec.start_time >= rec.end_time:
                raise ValidationError("Invalid time range")

    @api.constrains("doctor_id", "date", "start_time", "end_time")
    def _check_overlap(self):
        for rec in self:
            if self.search(
                [
                    ("doctor_id", "=", rec.doctor_id.id),
                    ("date", "=", rec.date),
                    ("id", "!=", rec.id),
                    ("state", "!=", "cancelled"),
                    ("start_time", "<", rec.end_time),
                    ("end_time", ">", rec.start_time),
                ],
                limit=1,
            ):
                raise ValidationError("Time conflict for this doctor.")

    @api.onchange("doctor_id")
    def _onchange_doctor_id(self):
        if self.doctor_id:
            self.specialty_id = self.doctor_id.specialty_id
            self.start_time = 9.0
            self.end_time = 10.0
            self.consultation_fee = self.doctor_id.consultation_fee


   

    # cron methods executed on the model level not record 
    @api.model
    def _cron_send_appointment_reminders(self):
        tomorrow = fields.Date.today() + timedelta(days=1)

        appointments = self.search(
            [
                ("date", "=", tomorrow),
                ("state", "=", "confirmed"),
                ("reminder_sent", "=", False),
            ]
        )

        template = self.env.ref("roaya_clinic.email_template_appointment_reminder")

        for appointment in appointments:
            template.send_mail(appointment.id, force_send=False)
            appointment.reminder_sent = True

    
    @api.model
    def _cron_auto_mark_no_show(self):
        no_show_hours = float(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("clinic.no_show_hours", default=2)
        )
        now = fields.Datetime.now()
        appointments = self.search(
            [
                ("state", "=", "confirmed"),
                ("date", "=", fields.Date.today()),
            ]
        )

        # print(appointments)
        # Convert the separate date and hour fields to a combined datetime object
        for appointment in appointments:
            start_dt = datetime(
                appointment.date.year,
                appointment.date.month,
                appointment.date.day,
            ) + timedelta(hours=appointment.start_time)
            if now >= start_dt + timedelta(hours=no_show_hours):
                appointment.write({"state": "no_show"})
                appointment.message_post(
                    body=(
                        f"Appointment automatically marked as "
                        f"No Show after {no_show_hours} hour(s)."
                    )
                )

    def action_confirm(self):
        for record in self:
            if record.name == "New":
                record.name = (
                    self.env["ir.sequence"].next_by_code("clinic.appointment") or "New"
                )
            record.state = "confirmed"

    def action_print_appointment_confirmation(self):
        return self.env.ref("roaya_clinic.action_report_appointment").report_action(
            self
        )

    def action_check_in(self):
        for rec in self:
            if rec.state != "confirmed":
                raise ValidationError("Appointment must be confirmed first.")
            rec.state = "checked_in"
            

    def action_done(self):
        for rec in self:
            rec.state = "done"

    def action_cancel(self):
        for rec in self:
            if rec.state == "done":
                raise ValidationError("Cannot cancel a completed appointment.")

            if rec.state == "in_progress":
                raise ValidationError(
                    "Cannot cancel while consultation is in progress."
                )

            if rec.state in ("cancelled", "no_show"):
                continue

            rec.state = "cancelled"
            rec.message_post(body="Appointment cancelled.")

    def action_no_show(self):
        for rec in self:
            rec.state = "no_show"

    def unlink(self):
        for rec in self:
            if rec.state == "done":
                raise ValidationError(
                "You cannot delete a completed appointment. "
                "Completed records must be kept for medical/financial history."
            )

    # Instead of physically deleting, convert to "cancelled" so the
    # record — and any related charges/lab orders/prescriptions — stays
    # in the system for audit and billing history.
        self.write({"state": "cancelled"})
        for rec in self:
            rec.message_post(
            body="Appointment cancelled instead of deleted (delete action intercepted)."
        )
        return True

    def action_print_prescriptions(self):
        self.ensure_one()
        if not self.prescription_ids:
            raise ValidationError("No prescriptions found for this appointment.")
        return self.env.ref("roaya_clinic.action_report_prescription").report_action(
            self.prescription_ids
        )
        
    def action_view_prescriptions(self):
        self.ensure_one()

        action = self.env.ref(
            "roaya_clinic.action_clinic_prescription"
        ).read()[0]

        action["domain"] = [
            ("appointment_id", "=", self.id)
        ]

        action["context"] = {
            "default_appointment_id": self.id,
            "default_patient_id": self.patient_id.id,
            "default_doctor_id": self.doctor_id.id,
        }

        return action

    def action_open_charges(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": "Charges",
            "res_model": "clinic.charge",
            "view_mode": "tree,form",
            "domain": [("appointment_id", "=", self.id)],
            "context": {
                "default_appointment_id": self.id,
            },
        }

    def action_view_lab_orders(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": "Lab Orders",
            "res_model": "clinic.lab_order",
            "view_mode": "tree,form",
            "domain": [("appointment_id", "=", self.id)],
            "context": {
                "default_appointment_id": self.id,
            },
        }
    
    def action_print_lab_orders(self):
        self.ensure_one()
        if not self.lab_order_ids:
            raise ValidationError("No lab orders found for this appointment.")
        return self.env.ref("roaya_clinic.action_report_lab_order").report_action(
            self.lab_order_ids
    )

    def action_print_charges(self):
        self.ensure_one()
        if not self.charge_ids:
            raise ValidationError("No charges found for this appointment.")
        return self.env.ref("roaya_clinic.action_report_charge").report_action(
            self.charge_ids
    )

    def action_start_consultation(self):
        for rec in self:
            paid_charges = rec.charge_ids.filtered(lambda c: c.state == "paid")
            total_paid = sum(paid_charges.mapped("total_amount"))

            if total_paid < rec.consultation_fee:
                raise ValidationError(
                "Cannot start the consultation before the patient pays "
                "the consultation fee. Please create and confirm the "
                "payment first."
            )

            rec.state = "in_progress"