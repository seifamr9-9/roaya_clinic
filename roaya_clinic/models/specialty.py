from odoo import models, fields


class ClinicSpecialty(models.Model):
    _name = 'clinic.specialty'
    _description = 'Clinic Specialty'
    _order = 'name'

    name = fields.Char(required=True)
    description = fields.Text()
    active = fields.Boolean(default=True)

    doctor_ids = fields.One2many(
        'clinic.doctor',
        'specialty_id',
        string='Doctors'
    )

    _sql_constraints = [
        (
            'unique_specialty_name',
            'unique(name)',
            'Specialty name already exists.'
        )
    ]