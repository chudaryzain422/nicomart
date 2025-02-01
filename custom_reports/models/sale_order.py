from odoo import models, fields,api
import base64

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
    custom_note = fields.Char(string='NOTE')

    from odoo import models, api

    class SaleOrderZ(models.Model):
        _inherit = "sale.order"

        def action_quotation_send(self):
            """Extend Odoo's default method to attach only the custom report."""
            action = super().action_quotation_send()  # Call the original method
            mail_template = self._find_mail_template()  # Get the email template
            if mail_template:
                mail_template.attachment_ids = [(5, 0, 0)]
                report = self.env.ref('custom_reports.action_report_proforma_invoice')
                if report:
                    pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(report.id, res_ids=self.ids)
                    pdf_base64 = base64.b64encode(pdf_content)
                    attachment = self.env['ir.attachment'].create({
                        'name': 'Custom_Quotation.pdf',
                        'type': 'binary',
                        'datas': pdf_base64,
                        'res_model': 'sale.order',
                        'res_id': self.id,
                        'mimetype': 'application/pdf',
                    })
                    mail_template.attachment_ids = [(6, 0, [attachment.id])]
            return action  # Return the original action


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    hs_code = fields.Char(string="HS CODE",related='product_id.hs_code')
    image_128 = fields.Image(string="Image",related="product_id.image_128")

    # @api.onchange('product_id')
    # def onchange_sake_product_image(self):
    #     for product in self:
    #         product.image_128 = product.product_id.image_128