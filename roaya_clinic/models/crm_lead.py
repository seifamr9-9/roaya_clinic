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

    slot_id = fields.Many2one(
        comodel_name="clinic.schedule.slot",
        string="Reserved Slot",
        copy=False,
        tracking=True,
    )

    requested_appointment_datetime = fields.Datetime(string="Requested Appointment")
    rejection_reason = fields.Text(string="Rejection Reason", readonly=True)

    internal_notes = fields.Text(string="Reception Notes")
    start_time = fields.Float(string="Start Time")
    end_time = fields.Float(string="End Time")

    # Extra patient details captured from the website booking form. These
    # aren't stored anywhere else on the lead/partner, so they must be kept
    # here and copied onto clinic.patient when the lead is converted,
    # otherwise they are silently lost.
    patient_dob = fields.Date(string="Patient Date of Birth")
    patient_gender = fields.Selection(
        [("male", "Male"), ("female", "Female")],
        string="Patient Gender",
    )

    is_cancelled = fields.Boolean(
        string="Is Cancelled",
        compute="_compute_is_cancelled",
        store=False,
    )

    @api.depends("stage_id", "stage_id.name")
    def _compute_is_cancelled(self):
        for rec in self:
            rec.is_cancelled = bool(rec.stage_id and rec.stage_id.name == "Cancelled")

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
                            "phone": partner.phone or self.phone,
                            "mobile": partner.mobile or self.mobile,
                            "date_of_birth": self.patient_dob,
                            "gender": self.patient_gender,
                            "user_id": portal_user.id,
                        }
                    )
                )
            self.patient_id = patient

        # 4. Resolve appointment date/time
        # Priority:
        #   1) requested_appointment_datetime (set by website/API/patient request)
        #   2) date_deadline (manually set expected closing date on the lead)
        #   3) today (last-resort fallback)
        appointment_date = fields.Date.today()
        start_time = self.start_time
        end_time = self.end_time

        if self.requested_appointment_datetime:
            # requested_appointment_datetime is stored in UTC; convert to the
            # user's/company's timezone before extracting date & hour so the
            # displayed date/time matches what was actually requested.
            local_dt = fields.Datetime.context_timestamp(
                self, self.requested_appointment_datetime
            )
            appointment_date = local_dt.date()

            # Only derive start/end time from the requested datetime if they
            # weren't already set directly (e.g. from the website's slot
            # selection, stored on start_time/end_time). In many cases
            # requested_appointment_datetime only carries date information
            # with a midnight placeholder time, so blindly overriding a real
            # start_time with it produces a bogus time (e.g. 3.0 instead of
            # 10.0), which then falsely triggers the doctor overlap check.
            if not start_time:
                start_time = local_dt.hour + (local_dt.minute / 60.0)
                if not end_time:
                    end_time = start_time + 0.5  # default 30-minute slot
        elif self.date_deadline:
            appointment_date = self.date_deadline

        # 5. Create appointment
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
                    "slot_id": self.slot_id.id if self.slot_id else False,
                    "date": appointment_date,
                    "start_time": start_time,
                    "end_time": end_time,
                    "notes": self.internal_notes or "",
                    "crm_lead_id": self.id,
                }
            )
        )
        appointment.action_confirm()

        # The slot was only 'reserved' (pending confirmation) until now.
        # Converting the lead is the actual confirmation, so lock it in as
        # 'booked'. Otherwise it would just sit as 'reserved' until the
        # auto-release cron eventually frees it up from under the patient.
        if self.slot_id:
            self.slot_id.confirm()

        self.appointment_id = appointment

        # 6. Mark won + chatter
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

        # 7. Open the appointment form
        return {
            "type": "ir.actions.act_window",
            "res_model": "clinic.appointment",
            "res_id": appointment.id,
            "view_mode": "form",
            "target": "current",
        }