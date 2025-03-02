from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    pre_carriage = fields.Char(
        string='Pre Carriage By',
        help='Specify the pre-carriage transportation method'
    )
    country_of_origin = fields.Char(
        string='Country of Origin',
        help='Specify the country of origin for the goods'
    )
    port_of_loading = fields.Char(
        string='Port Of Loading',
        help='Specify the port of Loading'
    )
    port_of_discharge = fields.Char(
        string='Port of Discharge',
        help='Specify the port where goods will be discharged'
    )
    container_qty = fields.Char(
        string='Container Quantity',
        help='Specify the quantity of containers'
    )
    custom_note = fields.Char(string='NOTE')

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    hs_code = fields.Char(
        string="HS CODE",
        related='product_id.hs_code'
    )