from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ClinicInsuranceCompany(models.Model):
    _name = "clinic.insurance.company"
    _description = "Insurance Company"
    _order = "name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)

    coverage_percent = fields.Float(
        string="Coverage %",
        required=True,
        default=80.0,
        help="Percentage of the charge total that this insurance company covers.",
    )

    phone = fields.Char()
    email = fields.Char()

    patient_ids = fields.One2many(
        "clinic.patient",
        "insurance_company_id",
        string="Insured Patients",
    )
    patient_count = fields.Integer(
        compute="_compute_patient_count",
    )

    _sql_constraints = [
        (
            "unique_name",
            "unique(name)",
            "An insurance company with this name already exists.",
        ),
    ]

    @api.depends("patient_ids")
    def _compute_patient_count(self):
        for rec in self:
            rec.patient_count = len(rec.patient_ids)

    @api.constrains("coverage_percent")
    def _check_coverage_percent(self):
        for rec in self:
            if not (0 <= rec.coverage_percent <= 100):
                raise ValidationError("Coverage % must be between 0 and 100.")