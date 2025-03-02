# -*- coding: utf-8 -*-
# Copyright 2020 - Today Techkhedut.
# Part of Techkhedut. See LICENSE file for full copyright and licensing details.
import logging
import base64

from odoo import fields
from odoo.http import request, route
from odoo import http, tools, _

from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager

_logger = logging.getLogger(__name__)


class BookingsCustom(http.Controller):

    @http.route(['/freight/shipment/booking/create'], type='http', auth='user', website=True, cache=300, csrf=False)
    def portal_my_bookings_create(self, redirect=None, **post):
        shipper = request.env['res.partner'].sudo().search([('shipper', '=', True)])
        consignee = request.env['res.partner'].search(
            [('consignee', '=', True)])
        users = request.env['res.users'].search([])
        gateways = request.env['freight.port'].search([])
        values = {
            'shipper': shipper,
            'consignee': consignee,
            'users': users,
            'gateways': gateways,
        }
        return request.render("tk_freight.portal_booking_create", values)

    @http.route(['/freight/shipment/booking/submit'], type='http', auth='user', website=True, cache=300, csrf=False)
    def portal_my_bookings_submit(self, **post):
        operation = request.env['shipment.quotation']
        final_dict = {}
        if post:
            if post.get('operation'):
                final_dict['operation'] = post.get('operation')
            if post.get('transport'):
                final_dict['transport'] = post.get('transport')
                dir = post.get('transport')
            final_dict['consignee_id'] = request.env.user.partner_id.id
            if post.get('source'):
                final_dict['source'] = post.get('source')
            if post.get('destination'):
                final_dict['destination'] = post.get('destination')
            if post.get('notes'):
                final_dict['notes'] = post.get('notes')
            if post.get('length'):
                final_dict['length'] = post.get('length')
            if post.get('height'):
                final_dict['height'] = post.get('height')
            if post.get('weight'):
                final_dict['weight'] = post.get('weight')
            if post.get('width'):
                final_dict['width'] = post.get('width')
            if post.get('danger') == 'on':
                final_dict['dangerous_goods'] = True
                if 'danger_info' in post.keys():
                    final_dict['dangerous_goods_notes'] = post.get(
                        'danger_info')
        final_dict['address_to'] = 'location_address'
        final_dict['from_booking'] = True
        booking = operation.sudo().create(final_dict)
        return request.render("tk_freight.portal_booking_create_thankyou", {'operation': booking})

    @http.route(['/freight/shipment/booking'], type='http', auth="user", website=True, cache=300)
    def portal_my_bookings(self, **post):
        bookings = request.env['shipment.freight.booking']
        # make pager
        values = {}
        domain = ['|', ('create_uid', '=', False),
                  ('create_uid', '=', request.env.user.id)]
        bookings_recs = bookings.search(domain)
        values.update({
            'bookings': bookings_recs.sudo(),
        })
        return request.render("tk_freight.portal_my_bookings", values)

    @http.route(['/freight/shipment/booking/details/<model("shipment.freight.booking"):booking>'], type='http',
                auth="user",
                website=True, cache=300)
    def portal_my_booking_detail(self, booking):
        track_ids = request.env['booking.line'].sudo().search(
            [('booking_id', '=', booking.id)], order='id DESC')
        values = {
            'booking': booking.sudo(),
            'track_ids': track_ids,
        }
        return request.render("tk_freight.portal_my_booking_detail", values)

    @http.route(['/freight/shipment/quotation/details/<model("shipment.quotation"):q>'], type='http',
                auth="user",
                website=True, cache=300)
    def portal_my_quotation_detail(self, q):
        values = {
            'quot': q.sudo(),
        }
        return request.render("tk_freight.portal_my_quotation_detail", values)

    @http.route(['/freight/shipment/bookings'], type='http', auth="user", website=True)
    def booking_details(self):
        bookings = request.env['shipment.freight.booking']
        values = {}
        domain = [('consignee_id', '=', request.env.user.partner_id.id)]
        bookings_recs = bookings.search(domain)
        values.update({
            'bookings': bookings_recs.sudo(),
        })
        return request.render("tk_freight.booking_details", values)

    @http.route(['/freight/shipment/quotation'], type='http', auth="user", website=True)
    def quotation_details(self):
        quotation = request.env['shipment.quotation']
        values = {}
        domain = ['|', ('consignee_id', '=', request.env.user.partner_id.id),
                  ('shipper_id', '=', request.env.user.partner_id.id)]
        quot_recs = quotation.search(domain)
        values.update({
            'quot': quot_recs.sudo(),
        })
        return request.render("tk_freight.quotation_detail", values)

    @http.route(['/post/comment'], type='http', auth="user", website=True)
    def post_comment(self, **kw):
        book_id = request.env['shipment.freight.booking'].sudo().browse(
            int(kw['book_id']))
        vals = {'name': tools.ustr(kw['comment']),
                'user_id': request.env.user.id,
                'date': fields.datetime.now(),
                'booking_id': book_id.id}
        request.env['booking.line'].sudo().create(vals)
        track_ids = request.env['booking.line'].sudo().search(
            [('booking_id', '=', book_id.id)], order='id DESC')
        body = 'Note:%s noted by %s' % (tools.ustr(
            kw['comment']), request.env.user.partner_id.name)
        book_id.sudo().message_post(body=body)
        values = {}
        values.update({
            'booking': book_id.sudo(),
            'track_ids': track_ids,
        })
        return request.render("tk_freight.portal_my_booking_detail", values)

    @http.route(['/shipment'], type='http', auth="public", website=True)
    def track_freight(self, **kw):
        return request.render('tk_freight.track_shipment')

    @http.route('/track/shipment', type='http', auth="public", website=True)
    def track_shipment(self):
        tracking_no = request.params.get('q')
        if not tracking_no:
            return request.redirect('/shipment')
        freight = request.env['freight.shipment'].sudo().search(
            [('name', '=', tracking_no)])
        if freight:
            return request.render('tk_freight.freight_success', {'freight': freight})
        return request.redirect('/shipment')

    @http.route(['/freight/shipment/shipment'], type='http', auth="user", website=True)
    def shipment_details(self):
        shipment = request.env['freight.shipment']
        values = {}
        domain = ['|', ('consignee_id', '=', request.env.user.partner_id.id),
                  ('shipper_id', '=', request.env.user.partner_id.id)]
        shipment = shipment.search(domain)
        values.update({
            'shipments': shipment.sudo(),
        })
        return request.render("tk_freight.shipment_details", values)

    @http.route(['/freight/shipment/shipment/details/<model("freight.shipment"):s>'], type='http',
                auth="user",
                website=True, cache=300)
    def portal_my_shipment_detail(self, s):
        values = {
            'shipment': s.sudo()
        }
        return request.render("tk_freight.portal_my_shipment_details", values)


class FreightCustomerPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        bookings = request.env['shipment.freight.booking']
        domain = [('consignee_id', '=', request.env.user.partner_id.id)]
        values['freight_count'] = bookings.search_count(domain)
        shipment = request.env['freight.shipment']
        shipment_domain = ['|', ('consignee_id', '=', request.env.user.partner_id.id),
                           ('shipper_id', '=', request.env.user.partner_id.id)]
        values['quotation_count'] = request.env['shipment.quotation'].search_count(shipment_domain)
        values['shipment_count'] = shipment.search_count(shipment_domain)
        return values
