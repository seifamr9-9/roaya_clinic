# wizards/lead_reject_wizard.py

from odoo import models, fields, _
from odoo.exceptions import UserError


class LeadRejectWizard(models.TransientModel):
    _name = "clinic.lead.reject.wizard"
    _description = "Appointment Request Rejection Wizard"

    lead_id = fields.Many2one(
        "crm.lead",
        string="Lead",
        required=True,
        readonly=True,
    )
    patient_name = fields.Char(
        related="lead_id.contact_name",
        string="Patient",
        readonly=True,
    )
    lead_name = fields.Char(
        related="lead_id.name",
        string="Request",
        readonly=True,
    )
    rejection_reason = fields.Text(
        string="Rejection Reason",
        required=True,
        placeholder="Please provide a reason for rejecting this appointment request...",
    )
    send_email = fields.Boolean(
        string="Notify Patient by Email",
        default=True,
    )

    def action_confirm_rejection(self):
        self.ensure_one()
        lead = self.lead_id

        # 1. Write rejection reason
        lead.write({"rejection_reason": self.rejection_reason})

        # 2. Send email BEFORE changing stage
        if self.send_email:
            template = self.env.ref(
                "roaya_clinic.email_template_appointment_cancellation",
                raise_if_not_found=False,
            )
            if template:
                template.send_mail(lead.id, force_send=True)

        # 3. Set stage to Cancelled
        cancelled_stage = self.env["crm.stage"].search(
            [("name", "=", "Cancelled")], limit=1
        )
        # Prevent rejecting twice
        if lead.stage_id == cancelled_stage:
            raise UserError(_("This appointment request has already been cancelled."))

        if not cancelled_stage:
            raise UserError(
                _('Cancelled stage not found. Please create a stage named "Cancelled".')
            )

        lead.write({"stage_id": cancelled_stage.id})

        return {"type": "ir.actions.act_window_close"}
