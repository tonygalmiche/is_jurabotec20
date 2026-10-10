
from odoo import api, fields, models, _


class IsCivilite(models.Model):
    # Civilité : supprimée d'Odoo en v20 (res.partner.title), recréée dans le module
    _name='is.civilite'
    _description = "Civilité"
    _order='name'

    name     = fields.Char('Civilité', required=True, translate=True)
    shortcut = fields.Char('Abréviation', translate=True)


class ResPartner(models.Model):
    _inherit = "res.partner"

    mobile      = fields.Char('Mobile')                       # Supprimé d'Odoo en v20
    is_civilite = fields.Many2one('is.civilite', 'Civilité')  # title supprimé d'Odoo en v20

    is_code_comptable_fournisseur = fields.Char("Code comptable fournisseur")
    is_code_comptable_client      = fields.Char("Code comptable client")
    is_gestion_colisage           = fields.Boolean("Gestion du colisage", default=False)
    is_emplacement_charge_id      = fields.Many2one('stock.location' , 'Emplacement des charges', domain=[('usage','=','internal')])
