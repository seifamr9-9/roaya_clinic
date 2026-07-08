from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo import fields


class ClinicCharge(models.Model):
    _name = "clinic.charge"
    _description = "Clinic Charge"
    _order = "due_date desc"

    name = fields.Char(default="New", readonly=True)

    appointment_id = fields.Many2one(
        "clinic.appointment",
        required=True,
        index=True,
    )

    patient_id = fields.Many2one(
        related="appointment_id.patient_id",
        store=True,
        readonly=True,
    )

    doctor_id = fields.Many2one(
        related="appointment_id.doctor_id",
        store=True,
        readonly=True,
    )

    line_type = fields.Selection(
        [
            ("consultation", "Consultation"),
            ("lab", "Lab"),
            ("prescription", "Prescription"),
            ("other", "Other"),
        ]
    )

    amount = fields.Float()

    late_fee = fields.Float()

    total_amount = fields.Float(
        compute="_compute_total_amount",
        store=True,
    )

    due_date = fields.Date()

    payment_date = fields.Date()

    payment_method = fields.Selection(
        [
            ("cash", "Cash"),
            ("card", "Card"),
            ("insurance", "Insurance"),
        ]
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("pending", "Pending"),
            ("paid", "Paid"),
        ],
        default="draft",
    )

    notes = fields.Text()

    def action_pay(self):
        for rec in self:

            if not rec.payment_method:
                raise ValidationError("Please select a payment method.")

            rec.payment_date = fields.Date.today()
            rec.state = "paid"

    def action_reset_to_draft(self):
        for rec in self:
            rec.state = "draft"

    @api.depends("amount", "late_fee")
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = rec.amount + rec.late_fee
            
    @api.onchange("appointment_id")
    def _onchange_appointment_id(self):
        for rec in self:
            if rec.appointment_id:
                rec.amount = rec.appointment_id.consultation_fee
                rec.state = "pending"

    

    # def write(self, vals):
    #     res = super().write(vals)

    #     for rec in self:
    #         if rec.state == "paid" and rec.appointment_id:
    #             rec.appointment_id.write({"state": "done"})

    #     return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = (
                self.env['ir.sequence'].next_by_code('clinic.charge') or 'New' )
        return super().create(vals_list)

    def action_print_charge(self):
        self.ensure_one()
        return self.env.ref("roaya_clinic.action_report_charge").report_action(self)