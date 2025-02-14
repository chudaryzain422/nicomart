from odoo import fields, api, models


class FreightConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    quot_seq = fields.Char(string='Quotation', default="FQ", config_parameter='tk_freight.quot_seq')
    booking_seq = fields.Char(string='Booking', default="BOOKING", config_parameter='tk_freight.booking_seq')
    air_seq = fields.Char(string='Air Shipment', default="AIR", config_parameter='tk_freight.air_seq')
    ocean_seq = fields.Char(string='Ocean Shipment', default="OCEAN", config_parameter='tk_freight.ocean_seq')
    land_seq = fields.Char(string='Land Shipments', default="LAND", config_parameter='tk_freight.land_seq')
