from odoo import models, fields, api, _


class ShipmentQuotation(models.Model):
    _name = "shipment.quotation"
    _description = "Freight Shipment Quotation"
    _inherit = ['portal.mixin', 'mail.thread',
                'mail.activity.mixin', 'utm.mixin']

    name = fields.Char(string='Name', copy=False, default=lambda self: ('New'))
    status = fields.Selection([('q', 'Quotation'), ('qs', 'Quotation Sent'), ('c', 'Converted to Booking')],
                              string="Status", default="q")
    date = fields.Date(string="Date", default=fields.Date.today())
    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'Land')]), string='Transport')
    operation = fields.Selection(
        [('direct', 'Direct Shipment'), ('house', 'House Shipment'), ('master', 'Master Shipment')],
        string='Shipment')
    ocean_shipment_type = fields.Selection(([('fcl', 'Full Container(FCL)'), ('lcl', 'Less Container(LCL)')]),
                                           string='Ocean Shipment')
    inland_shipment_type = fields.Selection(([('ftl', 'Full Truckload(FTL)'), ('ltl', 'Less than Truckload(LTL)')]),
                                            string='Land Shipment')
    shipper_id = fields.Many2one('res.partner', 'Shipper', domain=[('shipper', '=', True)])
    consignee_id = fields.Many2one('res.partner', 'Consignee', domain=[('consignee', '=', True)])
    address_to = fields.Selection([('sc_address', 'Contact Address'), ('location_address', 'Location Address')],
                                  string="Address", default="sc_address")
    order_line_ids = fields.One2many('quot.order.line', 'quot_id')
    booking_id = fields.Many2one('shipment.freight.booking', string="Booking")
    total_text = fields.Text(string="Total Amount", compute="_compute_total", translate=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    from_booking = fields.Boolean(string="From Website")
    source = fields.Char(string="Source ", translate=True)
    destination = fields.Char(string="Destination", translate=True)

    # GENERAL INFORMATION
    height = fields.Float(string='Height(cm)')
    width = fields.Float(string='Width(cm)')
    length = fields.Float(string='Length(cm)')
    weight = fields.Float(string='weight(KG)')
    notes = fields.Text('Notes', translate=True)
    dangerous_goods = fields.Boolean('Dangerous Goods')
    dangerous_goods_notes = fields.Text('Dangerous Goods Info', translate=True)

    # Source Address
    source_location_id = fields.Many2one('freight.port', 'Source Location', index=True)
    s_zip = fields.Char()
    s_street = fields.Char(translate=True)
    s_street2 = fields.Char(translate=True)
    s_city = fields.Char(translate=True)
    s_country_id = fields.Many2one('res.country')
    s_state_id = fields.Many2one('res.country.state')

    # Destinations Address
    destination_location_id = fields.Many2one('freight.port', 'Destination Location', index=True)
    d_zip = fields.Char()
    d_street = fields.Char(translate=True)
    d_street2 = fields.Char(translate=True)
    d_city = fields.Char(translate=True)
    d_country_id = fields.Many2one('res.country')
    d_state_id = fields.Many2one('res.country.state')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            prefix = self.env['ir.config_parameter'].sudo().get_param('tk_freight.quot_seq')
            pre = str(prefix) if prefix else "FQ"
            if vals.get('name', ('New')) == ('New'):
                vals['name'] = pre + self.env['ir.sequence'].next_by_code('shipment.quot') or ('New')
        res = super(ShipmentQuotation, self).create(vals_list)
        return res

    @api.onchange('address_to', 'source_location_id', 'destination_location_id', 'shipper_id', 'consignee_id')
    def _onchange_address(self):
        for rec in self:
            if rec in self:
                if rec.address_to == "sc_address":
                    if rec.shipper_id:
                        rec.s_zip = rec.shipper_id.zip
                        rec.s_street = rec.shipper_id.street
                        rec.s_street2 = rec.shipper_id.street2
                        rec.s_city = rec.shipper_id.city
                        rec.s_country_id = rec.shipper_id.country_id.id
                        rec.s_state_id = rec.shipper_id.state_id.id
                    if rec.consignee_id:
                        rec.d_zip = rec.consignee_id.zip
                        rec.d_street = rec.consignee_id.street
                        rec.d_street2 = rec.consignee_id.street2
                        rec.d_city = rec.consignee_id.city
                        rec.d_country_id = rec.consignee_id.country_id.id
                        rec.d_state_id = rec.consignee_id.state_id.id
                elif rec.address_to == "location_address":
                    if rec.source_location_id:
                        rec.s_zip = rec.source_location_id.zip
                        rec.s_street = rec.source_location_id.street
                        rec.s_street2 = rec.source_location_id.street2
                        rec.s_city = rec.source_location_id.city
                        rec.s_country_id = rec.source_location_id.country_id.id
                        rec.s_state_id = rec.source_location_id.state_id.id
                    if rec.destination_location_id:
                        rec.d_zip = rec.destination_location_id.zip
                        rec.d_street = rec.destination_location_id.street
                        rec.d_street2 = rec.destination_location_id.street2
                        rec.d_city = rec.destination_location_id.city
                        rec.d_country_id = rec.destination_location_id.country_id.id
                        rec.d_state_id = rec.destination_location_id.state_id.id

    @api.depends('order_line_ids')
    def _compute_total(self):
        for rec in self:
            currency = self.order_line_ids.mapped('currency_id').mapped('id')
            total = ""
            amount = 0.0
            for c in currency:
                currency_id = self.env['res.currency'].browse(c)
                if rec.order_line_ids:
                    for order in rec.order_line_ids:
                        if order.currency_id.id == c:
                            amount = amount + order.total_amount
                total = total + str(currency_id.name) + " " + str(amount) + "\n"
                amount = 0.0
            rec.total_text = total

    def action_convert_booking(self):
        if self.shipper_id and self.consignee_id:
            self.consignee_id.consignee = True
            data = {
                'transport': self.transport,
                'operation': self.operation,
                'ocean_shipment_type': self.ocean_shipment_type,
                'inland_shipment_type': self.inland_shipment_type,
                'shipper_id': self.shipper_id.id,
                'consignee_id': self.consignee_id.id,
                'address_to': self.address_to,
                'source_location_id': self.source_location_id.id,
                'destination_location_id': self.destination_location_id.id,
                'length': self.length,
                'weight': self.weight,
                'height': self.height,
                'width': self.width,
                'notes': self.notes,
                'dangerous_goods_notes': self.dangerous_goods_notes,
                'dangerous_goods': self.dangerous_goods
            }
            book_id = self.env['shipment.freight.booking'].create(data)
            book_id._onchange_address()
            book_id.quot_id = self.id
            self.booking_id = book_id.id
            self.status = 'c'
            mail_template = self.env.ref('tk_freight.quot_booking_mail_template')
            if mail_template:
                mail_template.send_mail(self.id, force_send=True)
            return {
                'type': 'ir.actions.act_window',
                'name': 'Booking',
                'res_model': 'shipment.freight.booking',
                'res_id': book_id.id,
                'view_mode': 'form',
                'target': 'current'
            }

    def freight_quotation_sent(self):
        self.status = 'qs'


class QuotOrderLine(models.Model):
    _name = 'quot.order.line'
    _description = "Shipment Order Line"

    service_id = fields.Many2one('product.product', 'Service', domain="[('type','=','service')]")
    currency_id = fields.Many2one('res.currency', 'Currency')
    name = fields.Char(string='Description', required=True, translate=True)
    sale = fields.Float('Price', required=True)
    qty = fields.Float('Qty', default=1)
    quot_id = fields.Many2one('shipment.quotation', string="Shipment Quot")
    total_amount = fields.Monetary(string="Total Amount", compute="_compute_total_amount")

    @api.depends('qty', 'sale')
    def _compute_total_amount(self):
        for rec in self:
            if rec.sale and rec.qty:
                rec.total_amount = rec.sale * rec.qty
            else:
                rec.total_amount = 0.0

    @api.onchange('service_id')
    def _onchange_service_description(self):
        for rec in self:
            if rec.service_id:
                rec.name = rec.service_id.name
