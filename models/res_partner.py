
from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_code_comptable_fournisseur = fields.Char("Code comptable fournisseur")
    is_code_comptable_client      = fields.Char("Code comptable client")
    is_gestion_colisage           = fields.Boolean("Gestion du colisage", default=False)
    is_emplacement_charge_id      = fields.Many2one('stock.location' , 'Emplacement des charges', domain=[('usage','=','internal')])
