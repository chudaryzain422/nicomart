from odoo import models, fields,api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

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



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    hs_code = fields.Char(string="HS CODE",related='product_id.hs_code')
    image_128 = fields.Image(string="Image",related="product_id.image_128")

    # @api.onchange('product_id')
    # def onchange_sake_product_image(self):
    #     for product in self:
    #         product.image_128 = product.product_id.image_128