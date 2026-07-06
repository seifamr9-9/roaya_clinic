from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CrmLead(models.Model):
    _inherit = "crm.lead"

    doctor_id = fields.Many2one(
        comodel_name="clinic.doctor",
        string="Doctor",
        copy=False,
    )

    specialty_id = fields.Many2one(
        comodel_name="clinic.specialty",
        string="Specialty",
        related="doctor_id.specialty_id",
        store=True,
        readonly=True,
    )

    patient_id = fields.Many2one(
        comodel_name="clinic.patient",
        string="Patient",
        copy=False,
        tracking=True,
    )

    lead_source = fields.Selection(
        selection=[
            ("website", "Website"),
            ("api", "API"),
            ("manual", "Manual"),
        ],
        string="Lead Source",
        default="manual",
        required=True,
        readonly=True,
        copy=False,
    )

    appointment_id = fields.Many2one(
        "clinic.appointment",
        string="Appointment",
        tracking=True,
        copy=False,
        readonly=True,
    )

    requested_specialty_id = fields.Many2one(
        comodel_name="clinic.specialty",
        string="Requested Specialty",
    )

    requested_appointment_datetime = fields.Datetime(string="Requested Appointment")
    rejection_reason = fields.Text(string="Rejection Reason", readonly=True)

    internal_notes = fields.Text(string="Reception Notes")
    start_time = fields.Float(string="Start Time")
    end_time = fields.Float(string="End Time")

    def action_convert_to_patient_and_appointment(self):
        self.ensure_one()

        if self.appointment_id:
            raise UserError(
                _("This lead has already been converted (appointment: %s).")
                % self.appointment_id.name
            )

        if not self.doctor_id:
            raise UserError(_("Please select a doctor before converting this lead."))

        # 1. Resolve or create partner
        partner = self.partner_id
        if not partner:
            partner = (
                self.env["res.partner"]
                .sudo()
                .create(
                    {
                        "name": self.contact_name or self.partner_name or self.name,
                        "email": self.email_from,
                        "phone": self.phone,
                        "mobile": self.mobile,
                        "street": self.street,
                        "city": self.city,
                        "country_id": self.country_id.id if self.country_id else False,
                    }
                )
            )
            self.partner_id = partner

        if not partner.email:
            raise UserError(
                _("A valid email is required to create a portal user for %s.")
                % partner.name
            )

        # 2. Resolve or create portal user
        existing_user = (
            self.env["res.users"]
            .sudo()
            .search([("login", "=", partner.email)], limit=1)
        )
        if existing_user:
            portal_user = existing_user
        else:
            portal_group = self.env.ref("base.group_portal")
            portal_user = (
                self.env["res.users"]
                .sudo()
                .create(
                    {
                        "name": partner.name,
                        "login": partner.email,
                        "email": partner.email,
                        "partner_id": partner.id,
                        "groups_id": [(6, 0, [portal_group.id])],
                    }
                )
            )
            # only send reset email to newly created users
            # generate signup token and send email manually
            portal_user.sudo().mapped("partner_id").signup_prepare()
            token = portal_user.partner_id.signup_token
            base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
            signup_url = f"{base_url}/web/signup?token={token}"

            self.env["mail.mail"].sudo().create(
                {
                    "subject": _("Set your password – %s") % self.env.company.name,
                    "email_to": partner.email,
                    "email_from": self.env.company.email or "noreply@example.com",
                    "body_html": _(
                        "<p>Hello %(name)s,</p>"
                        "<p>Your clinic portal account has been created.</p>"
                        "<p><a href='%(url)s'>Click here to set your password</a></p>"
                    )
                    % {"name": partner.name, "url": signup_url},
                    "auto_delete": True,
                }
            ).send()

        # 3. Resolve or create patient  ← reuse portal_user from above, no second search
        patient = self.patient_id
        if not patient:
            patient = (
                self.env["clinic.patient"]
                .sudo()
                .search([("user_id", "=", portal_user.id)], limit=1)
            )
            if not patient:
                patient = (
                    self.env["clinic.patient"]
                    .sudo()
                    .create(
                        {
                            "name": partner.name,
                            "email": partner.email or self.email_from,
                            "user_id": portal_user.id,
                        }
                    )
                )
            self.patient_id = patient

        # 4. Create appointment
        appointment = (
            self.env["clinic.appointment"]
            .sudo()
            .create(
                {
                    "patient_id": patient.id,
                    "specialty_id": self.specialty_id.id
                    if self.specialty_id
                    else False,
                    "doctor_id": self.doctor_id.id if self.doctor_id else False,
                    "date": self.date_deadline or fields.Date.today(),
                    "start_time": self.start_time,
                    "end_time": self.end_time,
                    "notes": self.internal_notes or "",
                    "crm_lead_id": self.id,
                }
            )
        )
        appointment.action_confirm()
        self.appointment_id = appointment

        # 5. Mark won + chatter
        self.action_set_won()
        self.message_post(
            body=_(
                "Converted by %(user)s — "
                "Partner: %(coname)s · Patient: %(pname)s · Appointment: %(aname)s"
            )
            % {
                "user": self.env.user.name,
                "coname": partner.name,
                "pname": patient.name,
                "aname": appointment.name,
            },
            subtype_xmlid="mail.mt_note",
        )
        template = self.env.ref(
            "roaya_clinic.email_template_appointment_confirmation",
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(self.id, force_send=True)

        # 6. Open the appointment form
        return {
            "type": "ir.actions.act_window",
            "res_model": "clinic.appointment",
            "res_id": appointment.id,
            "view_mode": "form",
            "target": "current",
        }
