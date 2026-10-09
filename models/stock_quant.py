
# -*- coding: utf-8 -*-
from odoo import _, api, fields, models                          # type: ignore
from odoo.tools.float_utils import float_compare, float_is_zero  # type: ignore
from odoo.exceptions import UserError, ValidationError           # type: ignore
import os
import logging
_logger = logging.getLogger(__name__)


class StockQuant(models.Model):
    _inherit = "stock.quant"

    is_cout          = fields.Float(string="Coût"      , compute='_compute_is_cout', readonly=True, store=False, digits="Product Price", help="Coût pour valorisation stock (Prix achat du lot ou prix dans fiche article)")
    is_cout_total    = fields.Float(string="Coût total", compute='_compute_is_cout', readonly=True, store=False, digits="Product Price", help="Coût total pour valorisation stock")
    is_sale_order_id = fields.Many2one(related="lot_id.is_sale_order_id")
    is_pefc          = fields.Boolean(related="lot_id.is_pefc", store=True, readonly=True)
    is_volume        = fields.Float("Volume (m3) "      , digits='Volume', compute='_compute_volume', store=True, readonly=True)
    is_volume_total  = fields.Float("Volume total (m3) ", digits=(14,2)  , compute='_compute_volume', store=True, readonly=True)


    @api.depends('quantity')
    def _compute_volume(self):
        for obj in self:
            obj.is_volume       = obj.product_id.is_volume
            volume_total = (obj.is_volume or 0) * (obj.quantity or 0)
            if volume_total<0:
                volume_total = 0
            obj.is_volume_total = volume_total

    def _compute_is_cout(self):
        for obj in self:
            cout = obj.lot_id.is_prix_achat
            if not cout:
                cout = obj.product_id.standard_price
            obj.is_cout = cout
            obj.is_cout_total = obj.quantity * cout


    def deplacer_quant_action(self):
        for obj in self:
            context = self.env.context
            origine_id = obj.location_id.id
            new_context = dict(context).copy()
            new_context["origine_id"] = origine_id
            new_context["lot_id"]     = obj.lot_id.id
            new_context["product_id"] = obj.product_id.id
            new_context["quantity"]   = obj.quantity
            view_id = self.env.ref('is_jurabotec.is_stock_location_kanban_view2', False)
            return {
                "name": "Lot %s"%(obj.lot_id.name),
                "view_mode": "kanban",
                "res_model": "stock.location",
                "views": [(view_id.id, 'kanban')],
                "domain": [
                    ('usage', '=' , 'internal'),
                    ('id'   , '!=', origine_id),
                ],
                "type": "ir.actions.act_window",
                "context": new_context,
            }


    def imprime_etiquette_action(self):
        nb=len(self)
        ct=1
        for obj in self:
            ZPL = obj.lot_id.get_zpl()
            path="/tmp/etiquette-lot-stock-quant.zpl"
            fichier = open(path, "w")
            fichier.write(ZPL)
            fichier.close()
            imprimante = "ZD621-1"
            cmd="lpr -h -P"+imprimante+" "+path
            msg="%s/%s : %s"%(ct,nb,cmd)
            _logger.info(msg)
            os.system(cmd)
            ct+=1


    @api.model
    def _update_reserved_quantity(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None, strict=False):
        self = self.sudo()
        rounding = product_id.uom_id.rounding
        quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict)
        reserved_quants = []

        if float_compare(quantity, 0, precision_rounding=rounding) > 0:
            # if we want to reserve
            available_quantity = sum(quants.filtered(lambda q: float_compare(q.quantity, 0, precision_rounding=rounding) > 0).mapped('quantity')) - sum(quants.mapped('reserved_quantity'))
            #if float_compare(quantity, available_quantity, precision_rounding=rounding) > 0:
            #    raise UserError(_('It is not possible to reserve more products of %s than you have in stock.', product_id.display_name))
        elif float_compare(quantity, 0, precision_rounding=rounding) < 0:
            # if we want to unreserve
            available_quantity = sum(quants.mapped('reserved_quantity'))
            #if float_compare(abs(quantity), available_quantity, precision_rounding=rounding) > 0:
            #    raise UserError(_('It is not possible to unreserve more products of %s than you have in stock.', product_id.display_name))
        else:
            return reserved_quants

        for quant in quants:
            if float_compare(quantity, 0, precision_rounding=rounding) > 0:
                max_quantity_on_quant = quant.quantity - quant.reserved_quantity
                if float_compare(max_quantity_on_quant, 0, precision_rounding=rounding) <= 0:
                    continue
                max_quantity_on_quant = min(max_quantity_on_quant, quantity)
                quant.reserved_quantity += max_quantity_on_quant
                reserved_quants.append((quant, max_quantity_on_quant))
                quantity -= max_quantity_on_quant
                available_quantity -= max_quantity_on_quant
            else:
                max_quantity_on_quant = min(quant.reserved_quantity, abs(quantity))
                quant.reserved_quantity -= max_quantity_on_quant
                reserved_quants.append((quant, -max_quantity_on_quant))
                quantity += max_quantity_on_quant
                available_quantity += max_quantity_on_quant

            if float_is_zero(quantity, precision_rounding=rounding) or float_is_zero(available_quantity, precision_rounding=rounding):
                break
        return reserved_quants

