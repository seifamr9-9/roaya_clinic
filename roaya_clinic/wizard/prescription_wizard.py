from odoo import models, fields

class PrescriptionWizard(models.TransientModel):
    _name = 'clinic.prescription.wizard'
    _description = 'Prescription Wizard'

    appointment_id = fields.Many2one(
        'clinic.appointment',
        required=True
    )

    patient_id = fields.Many2one(
        'clinic.patient',
        related='appointment_id.patient_id',
        string='Patient',
        readonly=True
    )

    doctor_id = fields.Many2one(
        'clinic.doctor',
        related='appointment_id.doctor_id',
        string='Doctor',
        readonly=True
    )

    medication_name = fields.Char(required=True)
    dosage = fields.Char()
    frequency = fields.Char()
    duration_days = fields.Integer()
    notes = fields.Text()

    def action_create_prescription(self):
        self.ensure_one()

        self.env['clinic.prescription'].create({
        'appointment_id': self.appointment_id.id,
        'doctor_id': self.appointment_id.doctor_id.id,
        'medication_name': self.medication_name,
        'dosage': self.dosage,
        'frequency': self.frequency,
        'duration_days': self.duration_days,
        'notes': self.notes,
    })