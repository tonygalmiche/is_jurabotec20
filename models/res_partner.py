
from odoo import api, fields, models, _


class ResPartnerTitle(models.Model):
    # Civilité : supprimée d'Odoo en v20, recréée à l'identique de la v16 (même modèle, même table)
    _name='res.partner.title'
    _description = "Civilité"
    _order='name'

    name     = fields.Char('Civilité', required=True, translate=True)
    shortcut = fields.Char('Abréviation', translate=True)


class ResPartner(models.Model):
    _inherit = "res.partner"

    mobile = fields.Char('Mobile')                                # Supprimé d'Odoo en v20
    title  = fields.Many2one('res.partner.title', 'Civilité')    # Supprimé d'Odoo en v20

    is_code_comptable_fournisseur = fields.Char("Code comptable fournisseur")
    is_code_comptable_client      = fields.Char("Code comptable client")
    is_gestion_colisage           = fields.Boolean("Gestion du colisage", default=False)
    is_emplacement_charge_id      = fields.Many2one('stock.location' , 'Emplacement des charges', domain=[('usage','=','internal')])
