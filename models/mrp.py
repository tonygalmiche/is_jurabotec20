# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from random import randint


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    type = fields.Selection(selection_add=[
        ('commande', 'Commande client'),
    ], ondelete={'commande': lambda recs: recs.write({'type': 'normal', 'active': False})})