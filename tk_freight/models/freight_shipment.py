# -*- coding: utf-8 -*-
# Copyright 2020 - Today Techkhedut.
# Part of Techkhedut. See LICENSE file for full copyright and licensing details.
import logging
from odoo import api, fields, models, _
from random import choice
from string import digits
import json
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class FreightShipment(models.Model):
    _name = 'freight.shipment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Freight Shipment'

    def _get_default_stage_id(self):
        return self.env['freight.shipment.stages'].search([], order='sequence', limit=1)

    def _default_random_barcode(self):
        return "".join(choice(digits) for i in range(8))

    barcode = fields.Char(string="Barcode",
                          help="ID used for shipment identification.",
                          default=_default_random_barcode, copy=False)
    color = fields.Integer('Color')
    stage_id = fields.Many2one('freight.shipment.stages',
                               'Stage',
                               default=_get_default_stage_id,
                               group_expand='_read_group_stage_ids')
    create_datetime = fields.Datetime(string='Create Date',
                                      default=fields.Datetime.now())
    name = fields.Char(string='Name',
                       copy=False,
                       default=lambda self: ('New'))
    direction = fields.Selection(([('import', 'Import'),
                                   ('export', 'Export')]),
                                 string='Direction')
    transport = fields.Selection(([('air', 'Air'),
                                   ('ocean', 'Ocean'),
                                   ('land', 'Land')]),
                                 string='Transport Via')
    operation = fields.Selection([('direct', 'Direct Shipment'),
                                  ('house', 'House Shipment'),
                                  ('master', 'Master Shipment')],
                                 string='Operation')
    ocean_shipment_type = fields.Selection(([('fcl', 'Full Container(FCL)'),
                                             ('lcl', 'Less Container(LCL)')]),
                                           string='Ocean Shipment Type')
    inland_shipment_type = fields.Selection(([('ftl', 'Full Truckload(FTL)'),
                                              ('ltl', 'Less than Truckload(LTL)')]),
                                            string='Land Shipment Type')
    address_to = fields.Selection([('sc_address', 'Contact Address'),
                                   ('location_address', 'Location Address')],
                                  string="Address",
                                  default="sc_address")
    operator_id = fields.Many2one('res.users',
                                  default=lambda self: self.env.user,
                                  string='Responsible',
                                  required=True)
    dangerous_goods = fields.Boolean('Dangerous Goods')
    dangerous_goods_notes = fields.Text('Dangerous Goods Info')
    move_type = fields.Many2one('freight.move.type', 'Move Type')
    tracking_number = fields.Char('Tracking Number', translate=True)
    incoterm = fields.Many2one('freight.incoterms', 'Incoterm')
    parent_id = fields.Many2one('freight.shipment', 'Parent')
    booking_id = fields.Many2one('shipment.freight.booking')
    all_shipment = fields.Boolean(string='All Shipment')
    pass_state = fields.Boolean(string='Pass state',
                                compute="_compute_custom_check")
    term_condition = fields.Text(string='Term & Condition')
    shipment_add = fields.Boolean()
    route_add = fields.Boolean()
    company_id = fields.Many2one('res.company',
                                 string='Company',
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency',
                                  related='company_id.currency_id',
                                  string='Currency')
    total_service_charge = fields.Monetary(string="Total Customer Service",
                                           store=True,
                                           compute="_compute_service_charges")
    total_vendor_service_charge = fields.Monetary(string="Total Vendor Service",
                                                  store=True,
                                                  compute="_compute_service_charges")
    total_route_charge = fields.Monetary(string="Total Route Charges",
                                         store=True,
                                         compute="_compute_route_charges")
    frequent_location_id = fields.Many2one('freight.frequent.route',
                                           string='Frequent Route')

    # One2many
    freight_packages = fields.One2many('shipment.package.line', 'shipment_id')
    freight_services = fields.One2many('freight.service', 'shipment_id')
    freight_routes = fields.One2many('freight.route', 'shipment_id')
    shipments_ids = fields.One2many('freight.shipment', 'parent_id')
    sale_orders = fields.One2many('sale.order', 'freight_id')
    quotation_id = fields.Many2one('shipment.quotation', string="Quotation")
    document_ids = fields.One2many('freight.documents',
                                   'freight_id', string='Documents')
    custom_ids = fields.One2many('custom.department',
                                 'freight_id',
                                 string='Custom')

    # Shipment Tracking
    tracking_template_id = fields.Many2one('tracking.template',
                                           string="Template")
    freight_log = fields.One2many('shipment.tracking',
                                  'shipment_id')

    # Count
    service_count = fields.Integer('Services Count',
                                   compute='_compute_invoice')
    invoice_count = fields.Integer('Invoice Count',
                                   compute='_compute_invoice')
    service_quote_count = fields.Integer('Quote Count',
                                         compute='_compute_invoice')
    service_booking_count = fields.Integer('Booking Count',
                                           compute='_compute_invoice')
    document_count = fields.Integer(string='Documents Count',
                                    compute='_compute_document_count')

    # Shipper
    shipper_id = fields.Many2one('res.partner', 'Shipper',
                                 domain=[('shipper', '=', True)])
    shipper_email = fields.Char(related='shipper_id.email',
                                string="Email ",
                                translate=True)
    shipper_phone = fields.Char(related='shipper_id.phone',
                                string="Phone ", translate=True)

    # Consignee
    consignee_id = fields.Many2one('res.partner', 'Consignee',
                                   domain=[('consignee', '=', True)])
    consignee_email = fields.Char(related='consignee_id.email',
                                  translate=True)
    consignee_phone = fields.Char(related='consignee_id.phone',
                                  translate=True)

    # Datetime / Common Field / Carriage Details
    pickup_datetime = fields.Datetime('Estimate Pickup Time')
    arrival_datetime = fields.Datetime('Estimate Arrival Time')
    distance = fields.Integer(string='Distance')
    contact_place_of_receipt = fields.Selection([('Shipper', 'Shipper'),
                                                 ('Consignee', 'Consignee')],
                                                string="Place of Receipt",
                                                default="Consignee")
    contact_place_of_delivery = fields.Selection([('Shipper', 'Shipper'),
                                                  ('Consignee', 'Consignee')],
                                                 string="Place of Delivery",
                                                 default="Consignee")
    location_place_of_receipt = fields.Many2one('freight.port',
                                                string="Place of Receipt ")
    location_place_of_delivery = fields.Many2one('freight.port',
                                                 string="Place of Delivery ")
    freight_collect_prepaid = fields.Selection([('Collect', 'Collect'),
                                                ('Prepaid', 'Prepaid')],
                                               string="Bill",
                                               default="Collect")
    final_charges = fields.Monetary(string='Total Charges',
                                    store=True,
                                    compute="_compute_final_charges")
    notes = fields.Text('Notes')
    bl_number = fields.Char(string="B/L", translate=True)
    special_instruction = fields.Text(string="Special Instruction")

    # Air
    mawb_no = fields.Char('MAWB No',
                          translate=True)
    flight_no = fields.Char('Flight No',
                            translate=True)
    airline_owner_id = fields.Many2one('res.partner',
                                       string="Airline Owner")
    airline_id = fields.Many2one('freight.airline',
                                 'Airline',
                                 domain="[('owner_id','=',airline_owner_id)]")

    # Ocean
    ship_owner_id = fields.Many2one('res.partner', string="Shipping Line")
    obl = fields.Char('OBL No.',
                      help='Original Bill Of Landing',
                      translate=True)
    voyage_no = fields.Char('Voyage No', translate=True)
    vessel_id = fields.Many2one('freight.vessel',
                                'Vessel',
                                domain="[('owner_id','=',ship_owner_id)]")
    transhipment_port = fields.Many2one('freight.port',
                                        string="Transhipment Port")

    # Land
    truck_owner_id = fields.Many2one('res.partner', string="Owner")
    truck_ref = fields.Char('CMR/RWB', translate=True)
    trucker = fields.Many2one('fleet.vehicle',
                              'Vehicle',
                              domain="[('is_freight_shipment','=',True),('owner_id','=',truck_owner_id)]")
    trucker_number = fields.Char('Reference',
                                 translate=True)

    # Agent
    agent_id = fields.Many2one('res.partner',
                               'S/I Agent',
                               domain=[('agent', '=', True)])
    bl_document_type = fields.Selection([('Draft', 'DRAFT'),
                                         ('Copy', 'COPY NON NEGOTIABLE '),
                                         ('original', 'ORIGINAL'),
                                         ('telex_release', 'Telex Release')],
                                        string="B/L Document Type")
    freight_payable = fields.Char(string="Freight Payable At",
                                  translate=True)
    no_bill = fields.Selection([('zero', '(0) ZERO'),
                                ('three', '(3) THREE'),
                                ('surrender', 'SURRENDER')])
    freight_amount = fields.Monetary(string="Freight Amount")
    si_issue_date = fields.Date(string="S/I Issue Date")

    # Final Destination
    final_destination_id = fields.Many2one(
        'freight.port', string="Final Destination")

    # Source Address
    port_ids = fields.Many2many('freight.port',
                                string="Freight Port",
                                compute="compute_freight_port")
    source_location_id = fields.Many2one('freight.port',
                                         'Source Location',
                                         domain="[('id','in',port_ids)]",
                                         index=True)
    s_zip = fields.Char()
    s_street = fields.Char(translate=True)
    s_street2 = fields.Char(translate=True)
    s_city = fields.Char(translate=True)
    s_country_id = fields.Many2one('res.country')
    s_state_id = fields.Many2one('res.country.state')

    # Destinations Address
    destination_location_id = fields.Many2one('freight.port',
                                              'Destination Location',
                                              domain="[('id','in',port_ids)]",
                                              index=True)
    d_zip = fields.Char()
    d_street = fields.Char(translate=True)
    d_street2 = fields.Char(translate=True)
    d_city = fields.Char(translate=True)
    d_country_id = fields.Many2one('res.country')
    d_state_id = fields.Many2one('res.country.state')

    # Accountancy
    vendor_bill_count = fields.Integer('Vendor Bill Count',
                                       compute='_compute_invoice')
    total_invoiced = fields.Float('Total Invoiced(Receivables',
                                  compute='_compute_total_amount')
    total_bills = fields.Float('Total Bills(Payable)',
                               compute='_compute_total_amount')
    margin = fields.Float("Margin",
                          compute='_compute_total_amount')
    invoice_residual = fields.Float('Invoice Residual',
                                    compute='_compute_total_amount')
    bills_residual = fields.Float('Bills Residual',
                                  compute='_compute_total_amount')
    invoice_paid_amount = fields.Float('Invoice',
                                       compute='_compute_total_amount')
    bills_paid_amount = fields.Float('Bills',
                                     compute='_compute_total_amount')
    actual_margin = fields.Float('Actual Margin',
                                 compute='_compute_total_amount')
    accountancy_currency = fields.Char(compute='_compute_total_amount',
                                       translate=True)

    # Insurance
    is_freight_insurance = fields.Boolean(string='Is Freight Insurance')
    policy_no = fields.Char(string='Policy No.', translate=True)
    policy_company_id = fields.Many2one('res.partner',
                                        domain=[('company_type', '=', 'company'),
                                                ('is_policy', '=', True)])
    date = fields.Date(string='Issue Date')
    issue_by = fields.Char(string='Issued By',
                           translate=True)
    policy_name = fields.Char(string='Policy Name',
                              translate=True)
    policy_holder_id = fields.Many2one(related="consignee_id",
                                       string="Policy Holder")
    total_charge = fields.Monetary(string='Total Charge')
    term = fields.Html(string='Insurance Terms')
    risk_ids = fields.Many2many('policy.risk',
                                string='Risk Covered')
    policy_added = fields.Boolean(string='Policy Added')

    # Mask And Numbers
    mask_numbers = fields.Text(string="Mask and Numbers", translate=True)
    desc_pkg = fields.Text(string="Description and Packages & Goods Particulars Furnished by Shipper",
                           translate=True)
    measurement = fields.Text(string="Measurement", translate=True)
    remark = fields.Text(string="Remarks", translate=True)

    # Total Net, Gross and Volume
    package_total_gross = fields.Float(
        compute="_compute_total_gross_net_volume")
    package_total_net = fields.Float(compute="_compute_total_gross_net_volume")
    package_total_volume = fields.Float(
        compute="_compute_total_gross_net_volume")

    # Freight Package
    vendor_id = fields.Many2one('res.partner',
                                domain="[('shipper','=',False),('consignee','=',False)]")
    vendor = fields.Selection([('single', 'Single Vendor'),
                               ('multiple', 'Multiple Vendor')],
                              string='Vendor ',
                              default="single")

    # Notify Party
    first_notify_id = fields.Many2one('res.partner',
                                      string="1st Notify",
                                      domain="[('notify','=',True)]")
    second_notify_id = fields.Many2one('res.partner',
                                       string="2nd Notify",
                                       domain="[('notify','=',True)]")

    # Constrains
    @api.constrains('source_location_id', 'destination_location_id', 'address_to')
    def _check_source_destination_location(self):
        for record in self:
            if record.address_to == "location_address":
                if record.source_location_id.id == record.destination_location_id.id:
                    raise ValidationError(
                        "Source and Destination Location are not Same !")

    @api.constrains('shipper_id', 'consignee_id')
    def _check_shipper_consignee(self):
        for record in self:
            if record.shipper_id.id == record.consignee_id.id:
                raise ValidationError("Shipper and Consignee are not Same !")

    @api.onchange('tracking_template_id')
    def _onchange_tracking_template(self):
        for rec in self:
            if rec.tracking_template_id:
                rec.freight_log = [(5, 0, 0)]
                lines = []
                for line in rec.tracking_template_id.template_ids:
                    lines.append((0, 0, {
                        'location_id': line.location_id.id,
                        'activity_id': line.activity_id.id,
                    }))
                rec.freight_log = lines

    # Accountancy
    @api.depends('freight_services')
    def _compute_total_amount(self):
        for order in self:
            invoices = self.env['account.move'].sudo().search(
                [('freight_operation_id', '=', order.id), ('move_type', '=', 'out_invoice'), ('state', '=', 'posted')])
            invoice_amount = 0.0
            invoice_residual = 0.0
            bill_amount = 0.0
            bills_residual = 0.0
            for invoice in invoices:
                invoice_amount += invoice.amount_total_signed
                invoice_residual += invoice.amount_residual_signed
            bills = self.env['account.move'].sudo().search(
                [('freight_operation_id', '=', order.id), ('move_type', '=', 'in_invoice'), ('state', '=', 'posted')])
            for bill in bills:
                bill_amount += bill.amount_total_signed
                bills_residual += bill.amount_residual_signed
            order.total_invoiced = invoice_amount
            order.invoice_residual = invoice_residual
            order.invoice_paid_amount = invoice_amount - invoice_residual
            order.total_bills = bill_amount
            order.bills_residual = bills_residual
            order.bills_paid_amount = bill_amount - bills_residual
            order.actual_margin = invoice_amount - \
                invoice_residual - (-(bill_amount - bills_residual))
            order.margin = invoice_amount - (-bill_amount)
            order.accountancy_currency = "Amounts in " + \
                str(order.company_id.currency_id.symbol)

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        stage_ids = self.env['freight.shipment.stages'].search([])
        return stage_ids

    @api.depends('freight_services')
    def _compute_invoice(self):
        for order in self:
            order.service_count = len(order.freight_services)
            order.service_quote_count = 1 if self.quotation_id else 0
            order.invoice_count = self.env['account.move'].sudo().search_count(
                [('freight_operation_id', '=', order.id), ('move_type', '=', 'out_invoice')])
            order.vendor_bill_count = self.env['account.move'].sudo().search_count(
                [('freight_operation_id', '=', order.id), ('move_type', '=', 'in_invoice')])
            order.service_booking_count = 1 if self.booking_id else 0

    @api.depends('freight_packages')
    def _compute_total_gross_net_volume(self):
        for rec in self:
            net = 0.0
            gross = 0.0
            volume = 0.0
            if rec.freight_packages:
                for data in rec.freight_packages:
                    net = net + data.net_weight
                    gross = gross + data.gross_weight
                    volume = volume + data.volume
            rec.package_total_volume = volume
            rec.package_total_net = net
            rec.package_total_gross = gross

    @api.onchange('freight_packages')
    def _onchange_freight_packages(self):
        for rec in self:
            text = ""
            if rec.freight_packages:
                for data in rec.freight_packages:
                    text = text + \
                        str(data.qty) + " X " + str(data.package.name) + \
                        " - " + str(data.name) + "\n"
                rec.mask_numbers = text

    def button_services(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Services',
            'res_model': 'freight.service',
            'domain': [('shipment_id', '=', self.id)],
            'context': {'default_shipment_id': self.id},
            'view_mode': 'tree,form',
            'target': 'current'
        }

    @api.onchange('total_service_charge')
    def _onchange_freight_amount(self):
        self.freight_amount = self.total_service_charge

    def button_services_quotes(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Quotation',
            'res_model': 'shipment.quotation',
            'res_id': self.quotation_id.id,
            'view_mode': 'form',
            'target': 'current'
        }

    def button_services_bookings(self):
        action = {'name': _('Booking'),
                  'type': 'ir.actions.act_window',
                  'res_model': 'shipment.freight.booking',
                  'target': 'current',
                  'domain': [('id', '=', self.booking_id.id)]}
        booking_id = self.booking_id.id
        action['res_id'] = booking_id
        action['view_mode'] = 'form'
        return action

    def button_customer_invoices(self):
        invoices = self.env['account.move'].sudo().search(
            [('freight_operation_id', '=', self.id), ('move_type', '=', 'out_invoice')])
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_move_out_invoice_type")
        action['context'] = {
            'default_freight_operation_id': self.id, 'default_move_type': 'out_invoice', }
        if len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + \
                    [(state, view)
                     for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.id
        else:
            action['domain'] = [('id', 'in', invoices.ids)]
        return action

    def button_vendor_bills(self):
        invoices = self.env['account.move'].sudo().search(
            [('freight_operation_id', '=', self.id), ('move_type', '=', 'in_invoice')])
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_move_in_invoice_type")
        action['context'] = {
            'default_freight_operation_id': self.id, 'default_move_type': 'in_invoice', }
        if len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + \
                    [(state, view)
                     for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.id
        else:
            action['domain'] = [('id', 'in', invoices.ids)]
        return action

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if values.get('name', ('New')) == ('New'):
                if values.get('transport') == 'air':
                    air_prefix = self.env['ir.config_parameter'].sudo(
                    ).get_param('tk_freight.air_seq')
                    air_pre = str(air_prefix) if air_prefix else "AIR"
                    values['name'] = air_pre + \
                        self.env['ir.sequence'].next_by_code(
                            'operation.master') or _('New')
                elif values.get('transport') == 'ocean':
                    ocean_prefix = self.env['ir.config_parameter'].sudo(
                    ).get_param('tk_freight.ocean_seq')
                    ocean_pre = str(ocean_prefix) if ocean_prefix else "OCEAN"
                    values['name'] = ocean_pre + \
                        self.env['ir.sequence'].next_by_code(
                            'operation.house') or _('New')
                elif values.get('transport') == 'land':
                    land_prefix = self.env['ir.config_parameter'].sudo(
                    ).get_param('tk_freight.land_seq')
                    land_pre = str(land_prefix) if land_prefix else "LAND"
                    values['name'] = land_pre + \
                        self.env['ir.sequence'].next_by_code(
                            'operation.direct') or _('New')
            if values.get('name', False) and not values.get('tracking_number', False):
                values['tracking_number'] = values.get('name', False)
        id_data = super(FreightShipment, self).create(vals_list).id
        id = self.env['freight.shipment'].browse(id_data)
        if id.transport == 'air':
            route_id = self.env['freight.route'].create({'source_location_id': id.source_location_id.id,
                                                         'destination_location_id': id.destination_location_id.id,
                                                         'main_carriage': True,
                                                         'transport': id.transport,
                                                         'mawb_no': id.mawb_no,
                                                         'airline_id': id.airline_id.id,
                                                         'flight_no': id.flight_no,
                                                         'shipment_id': id.id,
                                                         'pickup_datetime': id.pickup_datetime,
                                                         'arrival_datetime': id.arrival_datetime,
                                                         'address_to': id.address_to,
                                                         'shipper_id': id.shipper_id.id,
                                                         'consignee_id': id.consignee_id.id,
                                                         'charge_type': 'f',
                                                         'inland_shipment_type': id.inland_shipment_type,
                                                         'ocean_shipment_type': id.ocean_shipment_type
                                                         })
            if route_id:
                route_id._onchange_address()
        if id.transport == 'ocean':
            route_id = self.env['freight.route'].create({'source_location_id': id.source_location_id.id,
                                                         'destination_location_id': id.destination_location_id.id,
                                                         'main_carriage': True,
                                                         'transport': id.transport,
                                                         'vessel_id': id.vessel_id.id,
                                                         'obl': id.obl,
                                                         'shipment_id': id.id,
                                                         'pickup_datetime': id.pickup_datetime,
                                                         'arrival_datetime': id.arrival_datetime,
                                                         'address_to': id.address_to,
                                                         'shipper_id': id.shipper_id.id,
                                                         'consignee_id': id.consignee_id.id,
                                                         'charge_type': 'f',
                                                         'inland_shipment_type': id.inland_shipment_type,
                                                         'ocean_shipment_type': id.ocean_shipment_type
                                                         })
            if route_id:
                route_id._onchange_address()
        if id.transport == 'land':
            route_id = self.env['freight.route'].create({'source_location_id': id.source_location_id.id,
                                                         'destination_location_id': id.destination_location_id.id,
                                                         'main_carriage': True,
                                                         'transport': id.transport,
                                                         'truck_ref': id.truck_ref,
                                                         'trucker': id.trucker.id,
                                                         'trucker_number': id.trucker_number,
                                                         'shipment_id': id.id,
                                                         'pickup_datetime': id.pickup_datetime,
                                                         'arrival_datetime': id.arrival_datetime,
                                                         'address_to': id.address_to,
                                                         'shipper_id': id.shipper_id.id,
                                                         'consignee_id': id.consignee_id.id,
                                                         'charge_type': 'f',
                                                         'inland_shipment_type': id.inland_shipment_type,
                                                         'ocean_shipment_type': id.ocean_shipment_type
                                                         })
            if route_id:
                route_id._onchange_address()
        return id

    @api.depends('transport', 'source_location_id', 'destination_location_id')
    def compute_freight_port(self):
        for rec in self:
            ids = []
            ports = self.env['freight.port'].sudo()
            if rec.transport == 'air':
                ids = ports.search([('air', '=', True)]).mapped('id')
            elif rec.transport == 'ocean':
                ids = ports.search([('ocean', '=', True)]).mapped('id')
            elif rec.transport == 'land':
                ids = ports.search([('land', '=', True)]).mapped('id')
            rec.port_ids = ids

    def action_freight_document(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Document',
            'res_model': 'freight.documents',
            'domain': [('freight_id', '=', self.id)],
            'context': {'default_freight_id': self.id},
            'view_mode': 'tree',
            'target': 'current'
        }

    @api.onchange('frequent_location_id')
    def _onchange_frequent_route(self):
        for rec in self:
            if rec.frequent_location_id:
                rec.destination_location_id = rec.frequent_location_id.destination_location_id.id
                rec.source_location_id = rec.frequent_location_id.source_location_id.id

    @api.depends('document_ids')
    def _compute_document_count(self):
        for rec in self:
            rec.document_count = self.env['freight.documents'].search_count(
                [('freight_id', '=', rec.id)])

    @api.depends('freight_services')
    def _compute_service_charges(self):
        for rec in self:
            total = 0.0
            vendor_total = 0.0
            if rec.freight_services:
                for data in rec.freight_services:
                    if data.service_type == 'shipper' or data.service_type == 'consignee':
                        total = total + (data.sale * data.qty)
                    else:
                        vendor_total = vendor_total + (data.sale * data.qty)
                rec.total_service_charge = total
                rec.total_vendor_service_charge = vendor_total
            else:
                rec.total_service_charge = 0
                rec.total_vendor_service_charge = 0

    @api.depends('freight_routes')
    def _compute_route_charges(self):
        for rec in self:
            total = 0
            if rec.freight_routes:
                for data in rec.freight_routes:
                    if data.charge_type == 'p':
                        total = total + data.total_charge
                rec.total_route_charge = total
            else:
                rec.total_route_charge = 0

    @api.depends('custom_ids')
    def _compute_custom_check(self):
        for rec in self:
            if rec.custom_ids:
                for data in rec.custom_ids:
                    if not data.state == 'pass':
                        rec.pass_state = False
                    else:
                        rec.pass_state = True
            else:
                rec.pass_state = False

    def add_policy(self):
        for rec in self:
            if rec.total_charge and rec.policy_no and rec.policy_name and rec.date:
                self.policy_added = True
                data = {'service_id': self.env.ref('tk_freight.policy_product_1').id,
                        'name': self.policy_name + " - " + self.policy_no,
                        'qty': 1.0,
                        'sale': rec.total_charge,
                        'cost': rec.total_charge,
                        'shipment_id': rec.id
                        }
                self.freight_services.create(data)
            else:
                message = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'danger',
                        'title': ('Policy Information Missing !'),
                        'message': " Please Enter Policy No, Policy Name, Issue Date and Total Charge",
                        'sticky': False,
                    }
                }
                return message

    @api.depends('freight_packages')
    def _compute_final_charges(self):
        total = 0
        for rec in self:
            if rec.freight_packages:
                for data in rec.freight_packages:
                    total = total + (data.qty * data.charges)
                rec.final_charges = total
            else:
                rec.final_charges = 0.0

    def action_add_shipment(self):
        record = ""
        for rec in self:
            if rec.freight_packages:
                for data in rec.freight_packages:
                    if data.package_type == "item":
                        type = 'Box / Cargo'
                    else:
                        type = "Container / Box"
                    record = record + \
                        "{} - {} - {} \n".format(type,
                                                 data.name, data.package.name)
        self.shipment_add = True
        self.freight_services.create({'service_id': self.env.ref('tk_freight.charges_product_1').id,
                                      'name': record,
                                      'qty': 1.0,
                                      'sale': self.final_charges,
                                      'cost': self.final_charges,
                                      'shipment_id': self.id})

    def action_add_route(self):
        record = ""
        for rec in self:
            if rec.freight_routes:
                for data in rec.freight_routes:
                    name = data.name
                    record = record + "{} - {}\n ".format(data.transport, name)
        self.route_add = True
        self.freight_services.create({
            'service_id': self.env.ref('tk_freight.route_product_1').id,
            'name': record,
            'qty': 1.0,
            'sale': self.total_route_charge,
            'cost': self.total_route_charge,
            'shipment_id': self.id
        })

    def action_create_invoice(self):
        shipper_invoice_line = []
        consignee_invoice_line = []
        shipper_list = self.env['freight.service'].search(
            [('shipment_id', '=', self.id), ('service_type', '=', 'shipper'), ('invoiced', '=', False)]).mapped(
            'shipper_id').mapped('id')
        consignee_list = self.env['freight.service'].search(
            [('shipment_id', '=', self.id), ('service_type', '=', 'consignee'), ('invoiced', '=', False)]).mapped(
            'consignee_id').mapped('id')
        currency_list = self.env['freight.service'].search(
            [('shipment_id', '=', self.id), '|', ('service_type', '=', 'shipper'), ('service_type', '=', 'consignee'),
             ('vendor_invoiced', '=', False)]).mapped(
            'currency_id').mapped('id')
        if len(shipper_list) > 0:
            for shipper in shipper_list:
                for c in currency_list:
                    for data in self.freight_services:
                        if data.service_type == "shipper":
                            if not data.invoiced:
                                if data.shipper_id.id == shipper:
                                    if data.currency_id.id == c:
                                        data.status = "invoice"
                                        data.invoiced = True
                                        shipper_invoice_record = {
                                            'product_id': data.service_id.id,
                                            'name': data.name,
                                            'quantity': data.qty,
                                            'price_unit': data.sale
                                        }
                                        shipper_invoice_line.append(
                                            (0, 0, shipper_invoice_record))
                    if len(shipper_invoice_line) > 0:
                        main_data = {
                            'partner_id': shipper,
                            'move_type': 'out_invoice',
                            'invoice_date': fields.date.today(),
                            'freight_operation_id': self.id,
                            'currency_id': c,
                            'invoice_line_ids': shipper_invoice_line,
                        }
                        shipper_invoice_line = []
                        self.env['account.move'].create(main_data)

        if len(consignee_list) > 0:
            for consignee in consignee_list:
                for c in currency_list:
                    for data in self.freight_services:
                        if data.service_type == "consignee":
                            if not data.invoiced:
                                if data.consignee_id.id == consignee:
                                    if data.currency_id.id == c:
                                        data.status = "invoice"
                                        data.invoiced = True
                                        consignee_invoice_record = {
                                            'product_id': data.service_id.id,
                                            'name': data.name,
                                            'quantity': data.qty,
                                            'price_unit': data.sale
                                        }
                                        consignee_invoice_line.append(
                                            (0, 0, consignee_invoice_record))
                    if len(consignee_invoice_line) > 0:
                        main_data = {
                            'partner_id': consignee,
                            'move_type': 'out_invoice',
                            'invoice_date': fields.date.today(),
                            'freight_operation_id': self.id,
                            'currency_id': c,
                            'invoice_line_ids': consignee_invoice_line,
                        }
                        consignee_invoice_line = []
                        self.env['account.move'].create(main_data)

    def action_create_vendor_bill(self):
        bill_line = []
        vendor_list = self.env['freight.service'].search(
            [('shipment_id', '=', self.id), ('service_type', '=', 'vendor'), ('vendor_invoiced', '=', False)]).mapped(
            'vendor_id').mapped('id')
        currency_list = self.env['freight.service'].search(
            [('shipment_id', '=', self.id), ('service_type', '=', 'vendor'), ('vendor_invoiced', '=', False)]).mapped(
            'currency_id').mapped('id')
        for vendor in vendor_list:
            for c in currency_list:
                for data in self.freight_services:
                    if data.service_type == "vendor":
                        if not data.vendor_invoiced:
                            if data.vendor_id.id == vendor:
                                if data.currency_id.id == c:
                                    data.status = "bill"
                                    data.vendor_invoiced = True
                                    bill_record = {
                                        'product_id': data.service_id.id,
                                        'name': data.name,
                                        'quantity': data.qty,
                                        'price_unit': data.sale
                                    }
                                    bill_line.append((0, 0, bill_record))
                if len(bill_line) > 0:
                    main_data = {
                        'partner_id': vendor,
                        'move_type': 'in_invoice',
                        'invoice_date': fields.date.today(),
                        'freight_operation_id': self.id,
                        'currency_id': c,
                        'invoice_line_ids': bill_line,
                    }
                    bill_line = []
                    self.env['account.move'].create(main_data)

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

    @api.onchange('address_to', 'destination_location_id')
    def _onchange_port_location_delivery(self):
        for rec in self:
            if rec.address_to == "location_address" and rec.destination_location_id:
                rec.location_place_of_receipt = rec.destination_location_id.id
                rec.location_place_of_delivery = rec.destination_location_id.id

    def action_create_shipper_invoice(self):
        if not len(self.shipper_id.ids) == 1:
            raise ValidationError(
                "Please select only one shipping provider. You have selected multiple shippers.")
        else:
            shipper_id = self.shipper_id.ids[0]
            shipment_ids = self.env['freight.shipment'].browse(self.ids)
            invoice_lines = []
            for data in shipment_ids:
                record = {
                    'product_id': self.env.ref('tk_freight.freight_order_1').id,
                    'name': data.name,
                    'quantity': 1,
                    'price_unit': data.total_service_charge,
                }
                invoice_lines.append((0, 0, record))
            data = {
                'partner_id': shipper_id,
                'invoice_line_ids': invoice_lines,
                'move_type': 'out_invoice',
            }
            invoice_id = self.env['account.move'].create(data)
            invoice_data = {
                'partner_id': shipper_id,
                'invoice_id': invoice_id.id,
                'amount': invoice_id.amount_total
            }
            self.env['freight.multiple.invoice'].create(invoice_data)
            return {
                'type': 'ir.actions.act_window',
                'name': 'Invoice',
                'res_model': 'account.move',
                'res_id': invoice_id.id,
                'view_mode': 'form',
                'target': 'current'
            }

    def action_create_consignee_invoice(self):
        if not len(self.consignee_id.ids) == 1:
            raise ValidationError(
                "Please select only one consignee provider. You have selected multiple consignee.")
        else:
            consignee_id = self.consignee_id.ids[0]
            shipment_ids = self.env['freight.shipment'].browse(self.ids)
            invoice_lines = []
            for data in shipment_ids:
                record = {
                    'product_id': self.env.ref('tk_freight.freight_order_1').id,
                    'name': data.name,
                    'quantity': 1,
                    'price_unit': data.total_service_charge,
                }
                invoice_lines.append((0, 0, record))
            data = {
                'partner_id': consignee_id,
                'invoice_line_ids': invoice_lines,
                'move_type': 'out_invoice',
            }
            invoice_id = self.env['account.move'].create(data)
            invoice_data = {
                'partner_id': consignee_id,
                'invoice_id': invoice_id.id,
                'amount': invoice_id.amount_total
            }
            self.env['freight.multiple.invoice'].create(invoice_data)
            return {
                'type': 'ir.actions.act_window',
                'name': 'Invoice',
                'res_model': 'account.move',
                'res_id': invoice_id.id,
                'view_mode': 'form',
                'target': 'current'
            }


class FleetShipment(models.Model):
    _inherit = 'fleet.vehicle'

    is_freight_shipment = fields.Boolean()
    owner_id = fields.Many2one('res.partner', string="Owner")
