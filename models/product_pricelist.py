# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    is_unite = fields.Selection([
        ('m'    , 'm'),
        ('m2'   , 'm2'),
        ('m3'   , 'm3'),
        ('unite', 'Unité'),
    ], "Unité", default='m3')


    def dupliquer_ligne_action(self):
        for obj in self:
            res=obj.copy()


