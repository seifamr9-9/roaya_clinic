# -*- coding: utf-8 -*-
{
    "name": "Smart Clinic Management",
    "summary": "A multi-specialty private clinic management system",
    "description": "",
    "author": "NTI HireReady | Team A",
    "website": "https://www.yourcompany.com",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Healthcare",
    "version": "17.0.1.0.0",
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "LGPL-3",
    # any module necessary for this one to work correctly
    "depends": ["base", "web", "mail", "website", "portal", "crm"],
    # always loaded
    "data": [
        "security/record_rules.xml",
        "security/ir.model.access.csv",
        "wizard/create_appointment_wizard_views.xml",
        "wizard/daily_census_wizard.xml",
        "wizard/prescription_wizerd.xml",
        "wizard/report_wizard_views.xml",
        "wizard/lead_cancel_wizard.xml",
        "data/clinic_data.xml",
        "data/ir_sequence_data.xml",
        "data/ir_sequence_data.xml",
        "data/ir_cron.xml",
        "data/mail_template_data.xml",
        "report/appointment_report.xml", 
        "report/patient_report.xml",
        "report/lab_order_report.xml",
        "views/prescription_views.xml",
        "report/charge_report.xml",
        "report/prescription_report.xml",
        "views/website/menu_web.xml",
        "views/website/home.xml",
        "views/website/about.xml",
        "views/website/snippets/hero.xml",
        "views/website/snippets/services.xml",
        "views/website/snippets/doctors.xml",
        "views/website/pages/page_appointment.xml",
        "views/website/pages/appointment_success.xml",
        'views/portal/dashboard.xml',
        'views/portal/appointments.xml',
        'views/portal/portal_appointment_details.xml',
        'views/portal/portal_menu.xml',
        "views/appointment_views.xml",
        "views/doctor_views.xml",
        "views/schedule_views.xml",
        "views/schedule_slot_views.xml",
        "views/patient_views.xml",
        "views/specialty_views.xml",
        "views/api_token_views.xml",
        "views/lab_order_views.xml",
        "views/charge_views.xml",
        "views/crm_lead_views.xml",
        "views/lab_order_wizard_views.xml",
        "views/menu.xml",

    ],
    # only loaded in demonstration mode
    "demo": [
        "demo/demo.xml",
    ],

    'assets': {
    'web.assets_frontend': [
        'smart_clinic/static/src/js/portal.js',
    ],
},
}
