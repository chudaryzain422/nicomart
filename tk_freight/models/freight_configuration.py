from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    shipper = fields.Boolean('Shipper')
    consignee = fields.Boolean('Consignee')
    agent = fields.Boolean('Agent')
    is_policy = fields.Boolean('Policy Company')
    vendor = fields.Boolean(string="Vendor")
    notify = fields.Boolean(string="Notify")
    multiple_invoice_ids = fields.One2many('freight.multiple.invoice',
                                           'partner_id')


class CustomerInvoice(models.Model):
    _inherit = 'account.move'

    freight_operation_id = fields.Many2one('freight.shipment',
                                           string='Freight Shipment')

    direction = fields.Selection(related="freight_operation_id.direction",
                                 string='Direction')
    transport = fields.Selection(related="freight_operation_id.transport",
                                 string='Transport Via')
    operation = fields.Selection(related="freight_operation_id.operation",
                                 string='Operation')
    shipper_id = fields.Many2one(related="freight_operation_id.shipper_id",
                                 string="Shipper")
    consignee_id = fields.Many2one(related="freight_operation_id.consignee_id",
                                   string="Consignee")
    agent_id = fields.Many2one(related="freight_operation_id.agent_id",
                               string="Agent")
    source_location_id = fields.Many2one(related="freight_operation_id.source_location_id",
                                         string='Source Location')
    destination_location_id = fields.Many2one(related="freight_operation_id.source_location_id",
                                              string='Destination Location')

    @api.onchange('freight_operation_id')
    def _onchange_freight_operation_id(self):
        for rec in self:
            if rec.freight_operation_id:
                if rec.move_type == 'out_invoice':
                    rec.partner_id = rec.freight_operation_id.consignee_id.id
                if rec.move_type == 'in_invoice':
                    rec.partner_id = rec.freight_operation_id.agent_id.id


class CustomDepartment(models.Model):
    _name = 'custom.department'
    _description = 'Custom Department Services'

    freight_id = fields.Many2one('freight.shipment', string='Freight')
    declaration = fields.Char('Declaration No.', translate=True)
    note = fields.Char(string='Note', translate=True)
    date = fields.Date('Date')
    document = fields.Binary(string='Documents')
    file_name = fields.Char(string='File Name', translate=True)
    state = fields.Selection([('pass', 'Pass'),
                              ('in_process', 'Processing'),
                              ('cancel', 'Cancel')],
                             string='State')

    def action_pass(self):
        for rec in self:
            rec.state = 'pass'

    def action_in_process(self):
        for rec in self:
            rec.state = 'in_process'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'


class ShipmentStages(models.Model):
    _name = 'freight.shipment.stages'
    _description = 'shipment Stage'
    _order = 'sequence, id'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer('Sequence', default=10)


class ShipmentTracking(models.Model):
    _name = 'shipment.tracking'
    _description = 'Shipment Stage'

    date = fields.Date('Date')
    time = fields.Float(string='Time')
    location_id = fields.Many2one('shipment.location', string="Location ")
    activity_id = fields.Many2one('shipment.location.activity',
                                  string="Activity")
    shipment_id = fields.Many2one('freight.shipment',
                                  string='Shipment ID')
    status = fields.Selection([('pending', 'Pending'),
                               ('complete', 'Complete')],
                              default="pending")

    def action_complete(self):
        self.status = "complete"


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    freight_id = fields.Many2one('freight.shipment', string='Freight')
    direction = fields.Selection(related="freight_id.direction",
                                 string='Direction')
    transport = fields.Selection(related="freight_id.transport",
                                 string='Transport Via')
    operation = fields.Selection(related="freight_id.operation",
                                 string='Operation')
    shipper_id = fields.Many2one(related="freight_id.shipper_id",
                                 string="Shipper")
    consignee_id = fields.Many2one(related="freight_id.consignee_id",
                                   string="Consignee")
    agent_id = fields.Many2one(related="freight_id.agent_id", string="Agent")
    source_location_id = fields.Many2one(related="freight_id.source_location_id",
                                         string='Source Location')
    destination_location_id = fields.Many2one(related="freight_id.source_location_id",
                                              string='Destination Location')


class ShipmentPackageLine(models.Model):
    _name = 'shipment.package.line'
    _description = 'Freight Package Line'
    _rec_name = 'package'

    name = fields.Char(string='Container Number',
                       required=True,
                       translate=True)
    package_type = fields.Selection([('item', 'Box / Cargo'),
                                     ('container', 'Container / Box')],
                                    string="Package Type")
    transport = fields.Selection(([('air', 'Air'),
                                   ('ocean', 'Ocean'),
                                   ('land', 'Land')]),
                                 string='Transport')
    shipment_id = fields.Many2one('freight.shipment', 'Shipment ID')
    company_id = fields.Many2one('res.company',
                                 string='Company',
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency',
                                  related='company_id.currency_id',
                                  string='Currency')
    freight_package_ids = fields.Many2many('freight.package',
                                           string="Freight Packages",
                                           compute="compute_freight_packages")
    package = fields.Many2one('freight.package',
                              string='Size / Package',
                              required=True,
                              domain="[('id','in',freight_package_ids)]")
    charges = fields.Monetary(related='package.charge',
                              string='Charge')
    type = fields.Selection(([('dry', 'Dry'),
                              ('reefer', 'Reefer'),
                              ('flat_rock', 'Flat Rock'),
                              ('open_top', 'Open Top'),
                              ('other', 'Other')]),
                            string="Type ")
    qty = fields.Float('Qty', required=True, default=1.0)
    harmonize = fields.Char('Harmonize', translate=True)
    temperature = fields.Char('Temperature', translate=True)
    humidity = fields.Char(string="Humidity", translate=True)
    ventilation = fields.Char(string="Ventilation", translate=True)
    vgm = fields.Char('VGM', help='Verified gross mass', translate=True)
    carrier_seal = fields.Char('Carrier Seal', translate=True)
    seal_number = fields.Char('Seal Number', translate=True)
    reference = fields.Char('Reference', translate=True)
    dangerous_goods = fields.Boolean('Dangerous Goods')
    class_number = fields.Char('Class Number', translate=True)
    un_number = fields.Char('UN Number', translate=True)
    Package_group = fields.Char('Packaging Group:', translate=True)
    imdg_code = fields.Char('IMDG Code',
                            help='International Maritime Dangerous Goods Code',
                            translate=True)
    flash_point = fields.Char('Flash Point', translate=True)
    material_description = fields.Text('Material Description', translate=True)
    freight_item_lines = fields.One2many('shipment.item', 'package_line_id')
    route_id = fields.Many2one('freight.route', 'Route')
    container_type = fields.Selection([('GP', 'GP (General Purpose)'),
                                       ('HC', 'HC (High Cube)'),
                                       ('RF', 'RF (Reefer)'),
                                       ('FR', 'FR (Flat Rack)'),
                                       ('OT', 'OT (Open Top)'),
                                       ('GOH', 'GOH (Garment of Hanger)')],
                                      string="Type", default="GP")
    # Dimension
    volume = fields.Float('Volume (CBM)')
    gross_weight = fields.Float('Gross Weight (KG)')
    net_weight = fields.Float(string="Net Weight (KG)")
    height = fields.Float(string='Height(cm)')
    length = fields.Float(string='Length(cm)')
    width = fields.Float(string='Width(cm)')

    @api.onchange('package')
    def _onchange_package_dimension(self):
        for rec in self:
            if rec.package:
                rec.volume = rec.package.volume
                rec.gross_weight = rec.package.gross_weight
                rec.height = rec.package.height
                rec.length = rec.package.length
                rec.width = rec.package.width

    @api.depends('package_type', 'shipment_id', 'shipment_id.transport')
    def compute_freight_packages(self):
        for rec in self:
            ids = []
            freight_packages = self.env['freight.package'].sudo()
            if rec.package_type == 'item':
                if rec.shipment_id.transport == 'air':
                    ids = freight_packages.search(
                        [('air', '=', True), ('item', '=', True), ('active', '=', True)]).mapped('id')
                if rec.shipment_id.transport == 'ocean':
                    ids = freight_packages.search(
                        [('ocean', '=', True), ('item', '=', True), ('active', '=', True)]).mapped('id')
                if rec.shipment_id.transport == 'land':
                    ids = freight_packages.search(
                        [('land', '=', True), ('item', '=', True), ('active', '=', True)]).mapped('id')
            if rec.package_type == 'container':
                if rec.shipment_id.transport == 'air':
                    ids = freight_packages.search(
                        [('air', '=', True), ('container', '=', True), ('active', '=', True)]).mapped('id')
                if rec.shipment_id.transport == 'ocean':
                    ids = freight_packages.search(
                        [('ocean', '=', True), ('container', '=', True), ('active', '=', True)]).mapped('id')
                if rec.shipment_id.transport == 'land':
                    ids = freight_packages.search(
                        [('land', '=', True), ('container', '=', True), ('active', '=', True)]).mapped('id')
            rec.freight_package_ids = ids


class ShipmentItem(models.Model):
    _name = 'shipment.item'
    _description = 'Shipment Item Line'

    name = fields.Char(string='Description', translate=True)
    package_line_id = fields.Many2one('shipment.package.line',
                                      'Shipment ID')
    freight_package_ids = fields.Many2many('freight.package',
                                           string="Freight Package",
                                           compute="compute_freight_package")
    package = fields.Many2one('freight.package', 
                              'Item', 
                              domain="[('id','in',freight_package_ids)]")
    type = fields.Selection(([('dry', 'Dry'),
                              ('reefer', 'Reefer')]),
                            string="Operation")
    qty = fields.Float('Qty', default=1.0)
    # Dimension
    volume = fields.Float('Volume (CBM)')
    gross_weight = fields.Float('Gross Weight (KG)')
    height = fields.Float(string='Height(cm)')
    length = fields.Float(string='Length(cm)')
    width = fields.Float(string='Width(cm)')

    @api.depends('package_line_id', 'package_line_id.shipment_id.transport')
    def compute_freight_package(self):
        for line in self:
            ids = []
            freight_package = self.env['freight.package'].sudo()
            if line.package_line_id.shipment_id.transport == 'air':
                ids = freight_package.search(
                    [('air', '=', True), ('item', '=', True), ('active', '=', True)]).mapped('id')
            if line.package_line_id.shipment_id.transport == 'ocean':
                ids = freight_package.search(
                    [('ocean', '=', True), ('item', '=', True), ('active', '=', True)]).mapped('id')
            if line.package_line_id.shipment_id.transport == 'land':
                ids = freight_package.search(
                    [('land', '=', True), ('item', '=', True), ('active', '=', True)]).mapped('id')
            line.freight_package_ids = ids

    @api.onchange('package')
    def _onchange_item_dimension(self):
        for rec in self:
            if rec.package:
                rec.volume = rec.package.volume
                rec.gross_weight = rec.package.gross_weight
                rec.height = rec.package.height
                rec.length = rec.package.length
                rec.width = rec.package.width
                rec.name = rec.package.desc
               

class FreightService(models.Model):
    _name = 'freight.service'
    _description = 'Freight Service'

    shipment_id = fields.Many2one('freight.shipment', 'Shipment ID')
    route_id = fields.Many2one('freight.route', 'Route')
    # Services
    service_type = fields.Selection([('shipper', 'Shipper'),
                                     ('consignee', 'Consignee'),
                                     ('vendor', 'Vendor')],
                                    default="shipper",
                                    string="Service To")
    service_id = fields.Many2one('product.product',
                                 'Service',
                                 domain="[('type','=','service')]")
    currency_id = fields.Many2one('res.currency',
                                  'Currency')
    name = fields.Char(string='Description',
                       required=True,
                       translate=True)
    cost = fields.Float('Cost')
    sale = fields.Float('Price',
                        required=True)
    qty = fields.Float('Qty',
                       default=1)
    status = fields.Selection([('bill', 'Bill Created'),
                               ('invoice', 'Invoice Created'),
                               ('pending', 'Pending')],
                              default="pending", readonly=True)
    # Invoice
    shipper_id = fields.Many2one('res.partner',
                                 string="Shipper",
                                 domain="[('shipper','=',True)]")
    consignee_id = fields.Many2one('res.partner',
                                   string="Consignee",
                                   domain="[('consignee','=',True)]")
    customer_invoice = fields.Many2one('account.move')
    invoiced = fields.Boolean('Invoiced')
    # Bill
    vendor = fields.Selection([('single', 'Single Vendor'),
                               ('multiple', 'Multiple Vendor')],
                              string='Vendor ',
                              store=True)
    vendor_id = fields.Many2one('res.partner',
                                domain="['|',('notify','=',True),('vendor','=',True)]")
    vendor_invoice = fields.Many2one('account.move')
    vendor_invoiced = fields.Boolean('Vendor Invoiced')
    sale_order_id = fields.Many2one('sale.order', string="Sale Order")

    @api.model
    def default_get(self, fields):
        res = super(FreightService, self).default_get(fields)
        shipper_id = self._context.get('shipper_id')
        consignee_id = self._context.get('consignee_id')
        res['shipper_id'] = shipper_id
        res['consignee_id'] = consignee_id
        return res

    @api.onchange('service_id')
    def _onchange_service_description(self):
        for rec in self:
            if rec.service_id:
                rec.name = rec.service_id.name


class FreightRoute(models.Model):
    _name = 'freight.route'
    _description = 'Freight Route'

    name = fields.Char('Route', compute='_compute_name', translate=True)
    type = fields.Selection([('pickup', 'Pickup'),
                             ('oncarriage', 'On Carriage'),
                             ('precarriage', 'Pre Carriage'),
                             ('delivery', 'Delivery')],
                            string='Type')
    shipment_id = fields.Many2one('freight.shipment', 'Shipment ID')
    transport = fields.Selection([('air', 'Air'),
                                  ('ocean', 'Ocean'),
                                  ('land', 'Land')],
                                 string='Transport')
    ocean_shipment_type = fields.Selection([('fcl', 'FCL'),
                                            ('lcl', 'LCL')],
                                           string='Ocean Shipment Type')
    inland_shipment_type = fields.Selection([('ftl', 'FTL'),
                                             ('ltl', 'LTL')],
                                            string='Inland Shipment Type')
    freight_services = fields.One2many('freight.service', 'route_id')
    main_carriage = fields.Boolean('Main Carriage')
    shipper_id = fields.Many2one('res.partner', 'Shipper',
                                 domain=[('shipper', '=', True)])
    consignee_id = fields.Many2one('res.partner', 'Consignee',
                                   domain=[('consignee', '=', True)])
    charge_type = fields.Selection([('f', 'Free'),
                                    ('p', 'Paid')],
                                   string='Charge Type')
    company_id = fields.Many2one('res.company',
                                 string='Company',
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency',
                                  related='company_id.currency_id',
                                  string='Currency')
    total_charge = fields.Monetary(string="Charges")
    address_to = fields.Selection([('sc_address', 'Contact Address'),
                                   ('location_address', 'Location Address')],
                                  string="Address",
                                  default="sc_address")
    # Datetime/Common Field
    pickup_datetime = fields.Datetime('Estimate Pickup Time')
    arrival_datetime = fields.Datetime('Estimate Arrival Time')
    final_charges = fields.Monetary(string='Total Charges')

    # Source Address
    source_location = fields.Char(string="Source", translate=True)
    source_location_id = fields.Many2one('freight.port',
                                         'Source Location',
                                         index=True)
    s_zip = fields.Char()
    s_street = fields.Char(translate=True)
    s_street2 = fields.Char(translate=True)
    s_city = fields.Char(translate=True)
    s_country_id = fields.Many2one('res.country')
    s_state_id = fields.Many2one('res.country.state')
    # Destinations Address
    destination_location = fields.Char(string="Destination", translate=True)
    destination_location_id = fields.Many2one('freight.port',
                                              'Destination Location',
                                              index=True)
    d_zip = fields.Char()
    d_street = fields.Char(translate=True)
    d_street2 = fields.Char(translate=True)
    d_city = fields.Char(translate=True)
    d_country_id = fields.Many2one('res.country')
    d_state_id = fields.Many2one('res.country.state')
    # Ocean
    obl = fields.Char('OBL No.',
                      help='Original Bill Of Lading',
                      translate=True)
    voyage_no = fields.Char('Voyage No', translate=True)
    vessel_id = fields.Many2one('freight.vessel', 'Vessel')

    # Air
    mawb_no = fields.Char('MAWB No', translate=True)
    airline_id = fields.Many2one('freight.airline', 'Airline')
    flight_no = fields.Char('Flight No', translate=True)

    # Land
    truck_ref = fields.Char('CMR/RWB#/PRO#:', translate=True)
    trucker = fields.Many2one('fleet.vehicle', 'Trucker')
    trucker_number = fields.Char(string='Reference', translate=True)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(FreightRoute, self).create(vals_list)
        for id in res:
            id.freight_services.write({'shipment_id': id.shipment_id.id})
        return res

    def write(self, vals):
        res = super(FreightRoute, self).write(vals)
        self.freight_services.write({'shipment_id': self.shipment_id.id})
        return res

    def default_get(self, fields_list):
        res = super(FreightRoute, self).default_get(fields_list)
        res['shipper_id'] = self._context.get('shipper_id')
        res['consignee_id'] = self._context.get('consignee_id')
        return res

    @api.depends('address_to', 'source_location_id', 'destination_location_id', 'd_city', 's_city')
    def _compute_name(self):
        for rec in self:
            if rec.address_to == "sc_address":
                if rec.d_city and rec.s_city:
                    rec.name = rec.s_city + " to " + rec.d_city
                else:
                    rec.name = ""
            elif rec.address_to == "location_address":
                if rec.source_location_id and rec.destination_location_id:
                    rec.name = rec.source_location_id.name + \
                        " to " + rec.destination_location_id.name
                else:
                    rec.name = ""
            else:
                rec.name = ""

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


class FreightPort(models.Model):
    _name = 'freight.port'
    _description = 'Freight Port'

    code = fields.Char(string='Code', translate=True)
    name = fields.Char(string='Name', translate=True)
    air = fields.Boolean(string='Air')
    ocean = fields.Boolean(string='Ocean')
    land = fields.Boolean(string='Land')
    active = fields.Boolean(default=True, string='Active')
    # Address
    zip = fields.Char(string='Zip')
    street = fields.Char(string='Street1', translate=True)
    street2 = fields.Char(string='Street2', translate=True)
    city = fields.Char(string='City', translate=True)
    country_id = fields.Many2one('res.country', 'Country')
    state_id = fields.Many2one("res.country.state",
                               string='State',
                               readonly=False,
                               store=True,
                               domain="[('country_id', '=?', country_id)]")


class FreightVessel(models.Model):
    _name = 'freight.vessel'
    _description = 'Freight Vessel'

    code = fields.Char(string='Code', translate=True)
    name = fields.Char(string='Name', translate=True)
    global_zone = fields.Char(string='Global Zone', translate=True)
    country = fields.Many2one('res.country', 'Country')
    active = fields.Boolean(default=True, string='Active')
    imo_number = fields.Char(string="IMO", translate=True)
    flag_state = fields.Char(string="Flag state", translate=True)
    port_of_registry = fields.Char(string="Port of Registry", translate=True)
    capacity = fields.Char(string="Cargo Capacity", translate=True)
    engine = fields.Char(string="Type", translate=True)
    engine_power = fields.Char(string="Power", translate=True)
    speed = fields.Char(string="Speed(Knots)", translate=True)
    owner_id = fields.Many2one('res.partner', string='Shipping Line')


class FreightAirline(models.Model):
    _name = 'freight.airline'
    _description = 'Freight Airline'

    code = fields.Char(string='Code', translate=True)
    name = fields.Char(string='Name', translate=True)
    icao = fields.Char(string='ICAO', translate=True)
    country = fields.Many2one('res.country', 'Country')
    active = fields.Boolean(default=True, string='Active')
    aircraft_type = fields.Char(string="Aircraft Type", translate=True)
    capacity = fields.Char(string="Cargo Capacity", translate=True)
    owner_id = fields.Many2one('res.partner', string='Owner')


class FreightIncoterms(models.Model):
    _name = 'freight.incoterms'
    _description = 'Freight Incoterms'

    code = fields.Char(string='Code', translate=True)
    name = fields.Char(string='Name',
                       help="International Commercial Terms are a series of predefined commercial terms used in international transactions.", translate=True)
    active = fields.Boolean(default=True, string='Active')


class FreightPackage(models.Model):
    _name = 'freight.package'
    _description = 'Freight Package'

    code = fields.Char(string='Code', translate=True)
    name = fields.Char(string='Name / Size', translate=True)
    container = fields.Boolean('Container/Box')
    item = fields.Boolean(string='Is Item')
    other = fields.Boolean('Other')
    active = fields.Boolean(default=True, string='Active')
    air = fields.Boolean(string='Air')
    ocean = fields.Boolean(string='Ocean')
    land = fields.Boolean(string='Land')
    desc = fields.Char(string="Description", translate=True)
    height = fields.Float(string='Height(cm)')
    length = fields.Float(string='Length(cm)')
    width = fields.Float(string='Width(cm)')
    volume = fields.Float('Volume (CBM)')
    gross_weight = fields.Float('Gross Weight (KG)')

    company_id = fields.Many2one('res.company',
                                 string='Company',
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency',
                                  related='company_id.currency_id',
                                  string='Currency')
    charge = fields.Monetary(string='Charges')


class FreightMoveType(models.Model):
    _name = 'freight.move.type'
    _description = 'Freight Move Type'

    code = fields.Char(string='Code', translate=True)
    name = fields.Char(string='Name', translate=True)
    active = fields.Boolean(default=True, string='Active')


class FreightDocuments(models.Model):
    _name = 'freight.documents'
    _description = 'Document related to Freight Shipment'
    _rec_name = 'type_id'

    freight_id = fields.Many2one('freight.shipment',
                                 string='Shipment',
                                 readonly=True)
    type_id = fields.Many2one('certificate.type', string='Type')
    document_date = fields.Date(string='Date', default=fields.Date.today())
    document = fields.Binary(string='Documents', required=True)
    file_name = fields.Char(string='File Name', translate=True)


class CertificateType(models.Model):
    _name = 'certificate.type'
    _description = 'Type Of Certificate'
    _rec_name = 'type'

    type = fields.Char(string='Type', translate=True)


class PolicyRisk(models.Model):
    _name = 'policy.risk'
    _description = 'Policy Risk Details'

    name = fields.Char(string='Title', translate=True)
    desc = fields.Char(string='Description', translate=True)


class FrequentRoute(models.Model):
    _name = 'freight.frequent.route'
    _description = 'Frequent Route'

    name = fields.Char(string='Name', translate=True)
    source_location_id = fields.Many2one('freight.port',
                                         string="Source Location")
    destination_location_id = fields.Many2one('freight.port',
                                              string="Destination Location")

    @api.onchange('source_location_id', 'destination_location_id')
    def _onchage_source_destination(self):
        for rec in self:
            if rec.source_location_id and rec.destination_location_id:
                rec.name = rec.source_location_id.name + \
                    " - " + rec.destination_location_id.name


class FreightMultipleInvoice(models.Model):
    _name = "freight.multiple.invoice"
    _description = "Multiple Invoice"

    partner_id = fields.Many2one('res.partner')
    invoice_id = fields.Many2one('account.move', string="Invoice")
    date = fields.Date(string="Date", default=fields.Date.today())
    amount = fields.Float(string="Amount")


class ShipmentLocation(models.Model):
    _name = "shipment.location"
    _description = "Shipment Location"

    name = fields.Char(string="Title", translate=True)


class ShipmentActivity(models.Model):
    _name = "shipment.location.activity"
    _description = "Shipment Location Activity"

    name = fields.Char(string="Activity", translate=True)


class TrackingTemplate(models.Model):
    _name = 'tracking.template'
    _description = "Tracking Template"

    name = fields.Char(string="Title", translate=True)
    template_ids = fields.One2many(
        'tracking.template.line', 'template_id', string="Template")


class TrackingTemplateLine(models.Model):
    _name = 'tracking.template.line'
    _description = "Tracking Template Line"
    _rec_name = "location_id"

    location_id = fields.Many2one('shipment.location', string="Location")
    activity_id = fields.Many2one('shipment.location.activity',
                                  string="Activity")
    template_id = fields.Many2one('tracking.template', string="Template")
