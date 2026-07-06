from odoo import models, fields, api

class ClinicPrescription(models.Model):
    _name = 'clinic.prescription'
    _description = 'Prescription'
    _inherit = ['mail.thread', 'mail.activity.mixin']  

    name = fields.Char(
        string='Prescription Number',
        required=True,
        copy=False,
        readonly=True,
        default='New'
    )
     
    date = fields.Date(
    default=fields.Date.today,
    required=True
    )
    
    patient_id = fields.Many2one(
    related='appointment_id.patient_id',
    store=True,
    readonly=True
    )

    doctor_id = fields.Many2one(
    'clinic.doctor',
    string='Doctor',
    required=True
)
     
     
     
    appointment_id = fields.Many2one(
    'clinic.appointment',
    string='Appointment'
    )

    medication_name = fields.Char(string='Medication Name', required=True)

    dosage = fields.Char(string='Dosage')

    frequency = fields.Char(string='Frequency')

    duration_days = fields.Integer(string='Duration (Days)')

    notes = fields.Text(string='Notes')


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('clinic.prescription') or 'New'
        return super().create(vals_list)