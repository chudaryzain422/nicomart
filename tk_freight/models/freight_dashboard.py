# -*- coding: utf-8 -*-
# Copyright 2020 - Today Techkhedut.
# Part of Techkhedut. See LICENSE file for full copyright and licensing details.
import datetime
from odoo import models, fields, api
from datetime import timedelta, datetime


class DashboardDetails(models.Model):
    _name = 'dashboard.details'
    _description = 'Freight Dashboard'

    name = fields.Char(translate=True)

    @api.model
    def get_freight_info(self):
        fright_shipment = self.env['freight.shipment'].sudo()
        # Statics
        total_shipment = fright_shipment.search_count([])
        pending_quat = self.env['shipment.quotation'].sudo().search_count([
            ('status', '=', 'q')])
        pending_booking = self.env['shipment.freight.booking'].search_count(
            [('state', '=', 'draft')])
        total_port = self.env['freight.port'].search_count([])
        shipper_count = self.env['res.partner'].sudo().search_count(
            [('shipper', '=', True)])
        consignee_count = self.env['res.partner'].sudo().search_count(
            [('consignee', '=', True)])
        # Shipment
        direct_count = fright_shipment.search_count(
            [('operation', '=', 'direct')])
        house_count = fright_shipment.search_count(
            [('operation', '=', 'house')])
        master_count = fright_shipment.search_count(
            [('operation', '=', 'master')])
        air = fright_shipment.search_count(
            [('transport', '=', 'air')])
        ocean = fright_shipment.search_count(
            [('transport', '=', 'ocean')])
        land = fright_shipment.search_count(
            [('transport', '=', 'land')])
        import_count = fright_shipment.search_count(
            [('direction', '=', 'import')])
        export_count = fright_shipment.search_count(
            [('direction', '=', 'export')])

        data = {
            # Statics
            'total_shipment': total_shipment,
            'pending_quat': pending_quat,
            'pending_booking': pending_booking,
            'total_port': total_port,
            'shipper_count': shipper_count,
            'consignee_count': consignee_count,
            # Shipment
            'direct_count': direct_count,
            'house_count': house_count,
            'master_count': master_count,
            'air': air,
            'ocean': ocean,
            'land': land,
            'freight_direction': [['Import', 'Export'], [import_count, export_count]],
            'shipment_stages': self.get_shipment_stages(),
            # Graph
            'get_shipment_month': self.get_shipment_month_type(),
            'move_type': self.get_move_type(),
            'top_shipper': self.get_top_shipper(),
            'top_consign': self.get_top_consignee(),
            'get_bill_invoice': self.get_freight_invoice_bills(),
        }
        return data

    # Shipment Stages
    def get_shipment_stages(self):
        stages, shipment_counts, data = [], [], []
        stage_ids = self.env['freight.shipment.stages'].search(
            [], order='sequence asc')
        if not stage_ids:
            data = [[], []]
        for stg in stage_ids:
            shipment_data = self.env['freight.shipment'].sudo().search_count(
                [('stage_id', '=', stg.id)])
            shipment_counts.append(shipment_data)
            stages.append(stg.name)
        data = [stages, shipment_counts]
        return data

    # Top Shipper
    def get_top_shipper(self):
        shipper = {}
        for group in self.env['freight.shipment'].read_group([], ['shipper_id'],
                                                             ['shipper_id'], limit=10):
            if group['shipper_id']:
                name = self.env['res.partner'].sudo().browse(
                    int(group['shipper_id'][0])).name
                shipper[name] = group['shipper_id_count']

        shipper = dict(
            sorted(shipper.items(), key=lambda x: x[1], reverse=True))
        return [list(shipper.keys()), list(shipper.values())]

    # Top Consignee
    def get_top_consignee(self):
        partner, amount, data = [], [], []
        consignee = self.env['res.partner'].search(
            [('consignee', '=', True)]).mapped('id')
        for group in self.env['account.move'].read_group([('partner_id', 'in', consignee)],
                                                         ['amount_total',
                                                          'partner_id'],
                                                         ['partner_id'],
                                                         orderby="amount_total DESC", limit=5):
            if group['partner_id']:
                name = self.env['res.partner'].sudo().browse(
                    int(group['partner_id'][0])).name
                partner.append(name)
                amount.append(group['amount_total'])
        data = [partner, amount]
        return data

    # Move Type
    def get_move_type(self):
        move_type, counts, data = [], [], []
        move_types = self.env['freight.move.type'].search([])
        if not move_types:
            move_type, counts = [], []
        for type in move_types:
            rec = self.env['freight.shipment'].search_count(
                [('move_type', '=', type.id)])
            counts.append(rec)
            move_type.append(type.name)
        data = [move_type, counts]
        return data

    # Shipment Month
    def get_shipment_month(self):
        return {'January': 0,
                'February': 0,
                'March': 0,
                'April': 0,
                'May': 0,
                'June': 0,
                'July': 0,
                'August': 0,
                'September': 0,
                'October': 0,
                'November': 0,
                'December': 0,
                }

    # Shipment Month Value
    def get_month_keys(self):
        data = self.get_shipment_month()
        return list(data.keys())

    # Shipment By Month
    def get_shipment_month_type(self):
        year = fields.date.today().year
        air_dict = self.get_shipment_month()
        ocean_dict = self.get_shipment_month()
        land_dict = self.get_shipment_month()
        shipment = self.env['freight.shipment'].search([])
        for data in shipment:
            if data.create_datetime.year == year:
                if data.transport == 'air':
                    air_dict[data.create_datetime.strftime(
                        "%B")] = air_dict[data.create_datetime.strftime("%B")] + 1
                if data.transport == 'ocean':
                    ocean_dict[data.create_datetime.strftime(
                        "%B")] = ocean_dict[data.create_datetime.strftime("%B")] + 1
                if data.transport == 'land':
                    land_dict[data.create_datetime.strftime(
                        "%B")] = land_dict[data.create_datetime.strftime("%B")] + 1
        month = self.get_month_keys()
        air = list(air_dict.values())
        ocean = list(ocean_dict.values())
        land = list(land_dict.values())
        return [month, air, ocean, land]

    # Freight Invoice Bill
    def get_freight_invoice_bills(self):
        year = fields.date.today().year
        bill_dict = self.get_shipment_month()
        invoice_dict = self.get_shipment_month()
        bill = self.env['account.move'].search([])
        for data in bill:
            if data.invoice_date and data.invoice_date.year == year and data.freight_operation_id:
                if data.move_type == 'in_invoice':
                    bill_dict[data.invoice_date.strftime(
                        "%B")] = bill_dict[data.invoice_date.strftime("%B")] + data.amount_total
                if data.move_type == 'out_invoice':
                    invoice_dict[data.invoice_date.strftime("%B")] = invoice_dict[data.invoice_date.strftime(
                        "%B")] + data.amount_total

        return [self.get_month_keys(), list(bill_dict.values()), list(invoice_dict.values())]
