# -*- coding: utf-8 -*-
# Copyright 2020 - Today Techkhedut.
# Part of Techkhedut. See LICENSE file for full copyright and licensing details.

import datetime
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from random import choice
from string import digits
from odoo.exceptions import ValidationError


class FreightBooking(models.Model):
    _name = 'shipment.freight.booking'
    _inherit = ['portal.mixin', 'mail.thread',
                'mail.activity.mixin', 'utm.mixin']
    _description = 'Freight Bookings'

    def _get_default_stage_id(self):
        return self.env['freight.shipment.stages'].search([], order='sequence', limit=1)

    def _default_random_barcode(self):
        return "".join(choice(digits) for i in range(8))

    barcode = fields.Char(string="Barcode", help="ID used for shipment identification.",
                          default=_default_random_barcode, copy=False)
    color = fields.Integer('Color')
    create_datetime = fields.Datetime(
        string='Create Date', default=fields.Datetime.now())
    name = fields.Char(string='Name', copy=False, default=lambda self: ('New'))
    direction = fields.Selection(([('import', 'Import'),
                                   ('export', 'Export')]), string='Transfer')
    state = fields.Selection(([('draft', 'Draft'),
                               ('converted', 'Converted'),
                               ('cancel', 'Cancel')]),
                             string='Status', default='draft')
    transport = fields.Selection(([('air', 'Air'),
                                   ('ocean', 'Ocean'),
                                   ('land', 'Land')]),
                                 string='Transport')
    operation = fields.Selection([('direct', 'Direct Shipment'),
                                  ('house', 'House Shipment'),
                                  ('master', 'Master Shipment')],
                                 string='Shipment')
    ocean_shipment_type = fields.Selection(([('fcl', 'Full Container(FCL)'),
                                             ('lcl', 'Less Container(LCL)')]),
                                           string='Ocean Shipment')
    inland_shipment_type = fields.Selection(([('ftl', 'Full Truckload(FTL)'),
                                              ('ltl', 'Less than Truckload(LTL)')]),
                                            string='Land Shipment')
    shipper_id = fields.Many2one('res.partner', 'Shipper', domain=[
                                 ('shipper', '=', True)])
    shipper_email = fields.Char(
        related='shipper_id.email', string="Email ", translate=True)
    shipper_phone = fields.Char(
        related='shipper_id.phone', string="Phone ", translate=True)
    consignee_id = fields.Many2one('res.partner', 'Consignee', domain=[
                                   ('consignee', '=', True)])
    consignee_email = fields.Char(related='consignee_id.email', translate=True)
    consignee_phone = fields.Char(related='consignee_id.phone', translate=True)
    cancellation_reason_head = fields.Char(
        string="Cancellation Reason", translate=True)
    cancellation_reason = fields.Text(string="Cancellation", translate=True)
    quot_id = fields.Many2one('shipment.quotation', string="Quotation")

    # Datetime/Common Field
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', string='Currency')
    pickup_datetime = fields.Datetime('Estimate Pickup Time')
    arrival_datetime = fields.Datetime('Estimate Arrival Time')
    approx_charges = fields.Monetary(string='Approx Quotation Charges')
    distance = fields.Integer(string="Distance(KM)")
    height = fields.Float(string='Height(cm)')
    width = fields.Float(string='Width(cm)')
    length = fields.Float(string='Length(cm)')
    weight = fields.Float(string='weight(KG)')
    # Ocean
    obl = fields.Char(
        'OBL No.', help='Original Bill Of Landing', translate=True)
    voyage_no = fields.Char('Voyage No', translate=True)
    vessel_id = fields.Many2one('freight.vessel', string='Vessel/Ship')
    ship_owner_id = fields.Many2one(
        related='vessel_id.owner_id', string="Shipping Line")
    # Land
    truck_ref = fields.Char('CMR/RWB', translate=True)
    trucker = fields.Many2one('fleet.vehicle', 'Vehicle')
    trucker_number = fields.Char('Reference', translate=True)
    truck_owner_id = fields.Many2one(
        related="trucker.owner_id", string="Owner")
    # Air
    mawb_no = fields.Char('MAWB No', translate=True)
    airline_id = fields.Many2one('freight.airline', 'Airline')
    flight_no = fields.Char('Flight No', translate=True)
    airline_owner_id = fields.Many2one(
        related="airline_id.owner_id", string="Airline Owner")

    agent_id = fields.Many2one('res.partner', 'Agent', domain=[
                               ('agent', '=', True)])
    operator_id = fields.Many2one(
        'res.users', default=lambda self: self.env.user, string='Responsible', required=True)
    notes = fields.Text('Notes', translate=True)
    dangerous_goods = fields.Boolean('Dangerous Goods')
    dangerous_goods_notes = fields.Text('Dangerous Goods Info', translate=True)
    move_type = fields.Many2one('freight.move.type', 'Move Type')
    tracking_number = fields.Char('Tracking Number', translate=True)
    declaration_number = fields.Char('Declaration Number', translate=True)
    declaration_date = fields.Date('Declaration Date')
    custom_clearnce_date = fields.Datetime('Customs Clearance Date')
    incoterm = fields.Many2one('freight.incoterms', 'Incoterm')
    book_vals = fields.Char('Booking Vals', translate=True)
    freight_id = fields.Many2one(
        'freight.shipment', 'Freight Shipment', compute="_compute_freight_id")
    attachment = fields.Many2many('ir.attachment', 'attach_booking_rel', 'doc_id', 'booking_id',
                                  string="Attachment",
                                  help='You can attach the copy of your document', copy=False)
    track_ids = fields.One2many('booking.line', 'booking_id', 'Tracker Lines')
    address_to = fields.Selection([('sc_address', 'Contact Address'),
                                   ('location_address', 'Location Address')],
                                  string="Address",
                                  default="sc_address")

    # Notify Party
    first_notify_id = fields.Many2one(
        'res.partner', string="1st Notify", domain="[('notify','=',True)]")
    second_notify_id = fields.Many2one(
        'res.partner', string="2nd Notify", domain="[('notify','=',True)]")

    # Source Address
    source_location_id = fields.Many2one(
        'freight.port', 'Source Location', index=True)
    s_zip = fields.Char()
    s_street = fields.Char(translate=True)
    s_street2 = fields.Char(translate=True)
    s_city = fields.Char(translate=True)
    s_country_id = fields.Many2one('res.country')
    s_state_id = fields.Many2one('res.country.state')

    # Destinations Address
    destination_location_id = fields.Many2one(
        'freight.port', 'Destination Location', index=True)
    d_zip = fields.Char()
    d_street = fields.Char(translate=True)
    d_street2 = fields.Char(translate=True)
    d_city = fields.Char(translate=True)
    d_country_id = fields.Many2one('res.country')
    d_state_id = fields.Many2one('res.country.state')

    # Final Destination
    final_destination_id = fields.Many2one(
        'freight.port', string="Final Destination")

    # Cargo Details
    cargo_desc = fields.Text(string="Cargo Description", translate=True)
    hs_code = fields.Char(string="HS Code", translate=True)
    no_of_containers = fields.Integer(string="No Of Containers")
    container_size = fields.Many2one(
        'freight.package', string="Container Type")
    total_weight = fields.Char(string="Total Weight", translate=True)
    gross_weight = fields.Char(string="Gross Weight", translate=True)
    container_type = fields.Selection(
        [('dry', 'Dry'), ('reefer', 'Reefer'), ('flat_rock', 'Flat Rock'), ('open_top', 'Open Top'),
         ('other', 'Other')], string="Container Type ")
    other_container_type = fields.Char(
        string="Container Type  ", translate=True)
    temperature = fields.Char(string="Temperature", translate=True)
    humidity = fields.Char(string="Humidity", translate=True)
    ventilation = fields.Char(string="Ventilation", translate=True)
    mask_numbers = fields.Text(string="Mask & Numbers", translate=True)
    commodity = fields.Text(string="Commodity", translate=True)
    bl_document_type = fields.Selection(
        [('Draft', 'DRAFT'), ('Copy', 'COPY NON NEGOTIABLE '), ('original', 'ORIGINAL'),
         ('telex_release', 'Telex Release')],
        string="B/L Document Type")
    freight_collect_prepaid = fields.Selection([('Collect', 'Collect'), ('Prepaid', 'Prepaid')], string="Bill",
                                               default="Collect")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            prefix = self.env['ir.config_parameter'].sudo(
            ).get_param('tk_freight.booking_seq')
            pre = str(prefix) if prefix else "BOOKING"
            if vals.get('name', ('New')) == ('New'):
                vals['name'] = pre + self.env['ir.sequence'].next_by_code(
                    'shipment.freight.booking') or ('New')
            vals['tracking_number'] = vals.get('name')
        res = super(FreightBooking, self).create(vals_list)
        return res

    # Constrains
    @api.constrains('source_location_id', 'destination_location_id')
    def _check_source_destination_location(self):
        for record in self:
            if record.address_to == 'location_address':
                if record.source_location_id and record.destination_location_id:
                    if record.source_location_id.id == record.destination_location_id.id:
                        raise ValidationError(
                            "Source and Destination Location are not Same !")

    @api.constrains('shipper_id', 'consignee_id')
    def _check_shipper_consignee(self):
        for record in self:
            if record.shipper_id.id == record.consignee_id.id:
                raise ValidationError("Shipper and Consignee are not Same !")

    def convert_to_operation(self):
        if self.shipper_id and self.consignee_id:
            self.state = "converted"
            data = {
                'operation': self.operation,
                'direction': self.direction,
                'transport': self.transport,
                'ocean_shipment_type': self.ocean_shipment_type,
                'inland_shipment_type': self.inland_shipment_type,
                'shipper_id': self.shipper_id.id,
                'consignee_id': self.consignee_id.id,
                'source_location_id': self.source_location_id.id,
                'destination_location_id': self.destination_location_id.id,
                'mawb_no': self.mawb_no,
                'flight_no': self.flight_no,
                'airline_id': self.airline_id.id,
                'vessel_id': self.vessel_id.id,
                'voyage_no': self.voyage_no,
                'obl': self.obl,
                'truck_ref': self.truck_ref,
                'trucker_number': self.trucker_number,
                'trucker': self.trucker.id,
                'barcode': self.barcode,
                'notes': self.notes,
                'dangerous_goods': self.dangerous_goods,
                'dangerous_goods_notes': self.dangerous_goods_notes,
                'agent_id': self.agent_id.id,
                'operator_id': self.operator_id.id,
                'move_type': self.move_type.id,
                'incoterm': self.incoterm.id,
                'pickup_datetime': self.pickup_datetime,
                'arrival_datetime': self.arrival_datetime,
                'distance': self.distance,
                'address_to': self.address_to,
                'final_destination_id': self.final_destination_id.id,
                'second_notify_id': self.second_notify_id.id,
                'first_notify_id': self.first_notify_id.id,
                'quotation_id': self.quot_id.id,
            }
            booking_id = self.env['freight.shipment'].sudo().create(data)
            booking_id.booking_id = self.id
            booking_id._onchange_address()
            mail_template = self.env.ref(
                'tk_freight.booking_shipment_mail_template')
            if mail_template:
                mail_template.send_mail(self.id, force_send=True)
            return {
                'type': 'ir.actions.act_window',
                'name': 'Shipment',
                'res_model': 'freight.shipment',
                'res_id': booking_id.id,
                'view_mode': 'form',
                'target': 'current'
            }

        else:
            message = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'danger',
                    'title': ('Please add Shipper and Consignee to Convert Shipment !'),
                    'sticky': False,
                }
            }
            return message

    def convert_to_cancel(self):
        for rec in self:
            rec.state = 'cancel'

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

    def _compute_freight_id(self):
        for rec in self:
            rec.freight_id = (self.env['freight.shipment'].search(
                [('booking_id', '=', self.id)], limit=1)).id


class BookingLine(models.Model):
    _name = 'booking.line'
    _description = 'Booking Line'

    name = fields.Char('Note', translate=True)
    user_id = fields.Many2one('res.users', 'User ID')
    date = fields.Datetime('Date')
    actual_date = fields.Datetime('Actual')
    vendor_attachment = fields.Binary(attachment=True, string="Attachment")
    booking_id = fields.Many2one('shipment.freight.booking', 'Tender')

    @api.depends('date')
    def compute_actual(self):
        for line in self:
            line.actual_date = datetime.strptime(
                str(line.create_date), "%Y-%m-%d %H:%M:%S") + timedelta(hours=4)
