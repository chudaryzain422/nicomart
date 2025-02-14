# -*- coding: utf-8 -*-
# Copyright 2020 - Today Techkhedut.
# Part of Techkhedut. See LICENSE file for full copyright and licensing details.
{
    'name': 'All in one Freight Management | Advance Freight | Transport Management',
    'description': """
        - Freight Management
        - Transport Management
        - Air, Land & Ocean Transport
    """,
    'summary': """
        All types of transportation management
    """,
    'version': '18.0',
    'author': 'TechKhedut Inc.',
    'category': 'services',
    'company': 'TechKhedut Inc.',
    'maintainer': 'TechKhedut Inc.',
    'website': "https://www.techkhedut.com",
    'depends': ['contacts',
                'base',
                'base_setup',
                'account',
                'product',
                'web',
                'fleet',
                'mail',
                'board',
                'calendar',
                'sale_management',
                'website',
                'portal',
                'hr'],
    'data': [
        # Security
        'security/ir.model.access.csv',
        'security/security.xml',
        # Data
        'data/freight_data.xml',
        'data/freight_paperformat.xml',
        # wizard
        'wizard/shipment_invoice_view.xml',
        # Views
        'views/asset.xml',
        'views/freight_shipment_view.xml',
        'views/freight_report.xml',
        'views/freight_configuration.xml',
        'views/booking_view.xml',
        'views/freight_templates.xml',
        'views/stages_view.xml',
        'views/freight_quotation_view.xml',
        'views/res_config_view.xml',
        # Report
        'report/freight_details_report.xml',
        'report/cmr_bill_land.xml',
        'report/bill_of_landing_report.xml',
        'report/shipping_instruction_report.xml',
        'report/airway_bill_report.xml',
        'report/freight_booking_form.xml',
        'report/freight_quotation_report.xml',
        # Menu
        'views/menus.xml',
        # Mail Template
        'data/quot_booking_mail_template.xml',
        'data/booking_shipment_mail_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'tk_freight/static/src/xml/template.xml',
            'tk_freight/static/src/css/style.scss',
            'tk_freight/static/src/js/lib/apexcharts.js',
            'tk_freight/static/src/js/freight.js',
        ],
        'web.assets_frontend': [
            'tk_freight/static/src/css/freight.css',
        ],
    },
    'images': ['static/description/banner.gif'],
    'application': True,
    'installable': True,
    'auto_install': False,
    'price': 199.00,
    'currency': 'USD',
    'license': 'OPL-1',
}
