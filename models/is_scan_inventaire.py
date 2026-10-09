# -*- coding: utf-8 -*-
from odoo import models, fields, api   # type: ignore
from odoo.exceptions import UserError  # type: ignore
from datetime import datetime
import pytz
import time

class IsScanInventaire(models.Model):
    _name = 'is.scan.inventaire'
    _description = 'Inventaire par scan'
    _order = 'id desc'
    _rec_name = "id"

    barcode_input = fields.Char(string='Input utilisé par le widget pour récupérer les données du scan')
    barcode_scan  = fields.Char(string='Résultat du scan')
    ligne_ids = fields.One2many('is.scan.inventaire.ligne', 'scan_id', string='Lignes d\'inventaire')
    emplacement_dst_id = fields.Many2one('stock.location', 'Emplacement de destination')
    nb_lignes = fields.Integer('Nombre de lignes', compute='_compute_nb_lignes', store=True)
    move_ids = fields.One2many('stock.move', 'is_scan_inventaire_id', string='Mouvements créés', readonly=True)
    state = fields.Selection([
        ('emplacement', 'Emplacement'),
        ('saisie', 'Saisie'),
        ('termine', 'Terminé')
    ], string='État', default='emplacement', required=True)

    @staticmethod
    def _get_heure_francaise():
        """Retourne l'heure actuelle en timezone française (Europe/Paris)"""
        tz_france = pytz.timezone('Europe/Paris')
        now_france = datetime.now(tz_france)
        return now_france.strftime('%H:%M:%S')

    @api.depends('ligne_ids')
    def _compute_nb_lignes(self):
        for record in self:
            record.nb_lignes = len(record.ligne_ids)

    @api.onchange('barcode_scan')
    def _onchange_barcode_scan(self):
        barcode = self.barcode_scan

        if barcode:
            if barcode.startswith('E'):
                # Ne modifier l'emplacement que si l'état est 'emplacement'
                if self.state == 'emplacement':
                    try:
                        id = int(barcode[1:])
                    except Exception:
                        id = 0
                    location = self.env['stock.location'].search([('id', '=', id)], limit=1)
                    if location:
                        self.emplacement_dst_id = location.id
                        self.state = 'saisie'
            else:
                lot = self.env['stock.lot'].search([('name', '=', barcode)], limit=1)
                if lot:
                    # Récupérer la quantité totale du lot
                    quantite_totale = lot.product_qty or 0
                    
                    # Générer l'heure actuelle en heure française
                    heure_actuelle = self._get_heure_francaise()
                    self.ligne_ids = [(0, 0, {
                        'lot_id': lot.id,
                        'product_id': lot.product_id.id,  # Ajouter le product_id directement
                        'quantite': quantite_totale,  # Utiliser la quantité totale du lot
                        'heure_ajout': heure_actuelle,  # Ajouter l'heure française au format HH:MM:SS
                    })]


    def voir_lots_action(self):
        """
        Affiche la liste des lots scannés dans cet inventaire
        """
        for obj in self:
            lot_ids = []
            for ligne in obj.ligne_ids:
                if ligne.lot_id and ligne.lot_id.id not in lot_ids:
                    lot_ids.append(ligne.lot_id.id)
            
            return {
                "name": f"Lots inventaire {obj.id}",
                "view_mode": "tree,form",
                "res_model": "stock.lot",
                "domain": [
                    ("id", "in", lot_ids),
                ],
                "type": "ir.actions.act_window",
            }

    def voir_stock_detaille_action(self):
        """
        Affiche le stock détaillé (quants) des lots scannés dans cet inventaire
        """
        for obj in self:
            lot_ids = []
            for ligne in obj.ligne_ids:
                if ligne.lot_id and ligne.lot_id.id not in lot_ids:
                    lot_ids.append(ligne.lot_id.id)
            
            return {
                "name": f"Stock détaillé inventaire {obj.id}",
                "view_mode": "tree,form",
                "res_model": "stock.quant",
                "domain": [
                    ("lot_id", "in", lot_ids),
                    ("quantity", ">", 0),
                    ("location_id.usage", "=", "internal"),
                ],
                "type": "ir.actions.act_window",
            }

    def voir_mouvements_action(self):
        """
        Affiche la liste des mouvements créés par cet inventaire
        """
        for obj in self:
            return {
                "name": f"Mouvements inventaire {obj.id}",
                "view_mode": "tree,form",
                "res_model": "stock.move",
                "domain": [
                    ("is_scan_inventaire_id", "=", obj.id),
                ],
                "type": "ir.actions.act_window",
            }

    def voir_lignes_mouvements_action(self):
        """
        Affiche les lignes détaillées des mouvements créés par cet inventaire
        """
        for obj in self:
            return {
                "name": f"Lignes de mouvements inventaire {obj.id}",
                "view_mode": "tree,form",
                "res_model": "stock.move.line",
                "domain": [
                    ("move_id.is_scan_inventaire_id", "=", obj.id),
                ],
                "type": "ir.actions.act_window",
            }


    def vers_saisie_action(self):
        for obj in self:
            if not obj.emplacement_dst_id:
                raise UserError("Vous devez définir un emplacement de destination")
            obj.state="saisie"           
 

    def terminer_inventaire_action(self):
        """
        Termine l'inventaire en déplaçant le stock des lots vers le nouvel emplacement
        """
        for obj in self:
            if not obj.emplacement_dst_id:
                raise UserError("Vous devez définir un emplacement de destination")
            
            if not obj.ligne_ids:
                raise UserError("Aucune ligne d'inventaire à traiter")
            
            # Rechercher le type de picking pour les transferts internes
            picking_type = self.env['stock.picking.type'].search([
                ('code', '=', 'internal'),
                ('company_id', '=', self.env.company.id)
            ], limit=1)
            
            if not picking_type:
                raise UserError("Aucun type de picking interne trouvé")
            
            # Traiter chaque ligne d'inventaire
            for ligne in obj.ligne_ids:
                if not ligne.lot_id:
                    continue
                    
                # Rechercher les quants du lot pour trouver l'emplacement d'origine
                quants = self.env['stock.quant'].search([
                    ('lot_id', '=', ligne.lot_id.id),
                    ('quantity', '>', 0),
                    ('location_id.usage', '=', 'internal')
                ])
                
                for quant in quants:
                    if quant.location_id.id == obj.emplacement_dst_id.id:
                        # Le lot est déjà dans l'emplacement de destination
                        continue
                    
                    # Créer les valeurs pour le mouvement de stock
                    move_vals = {
                        'name': f'Inventaire par scan - {ligne.lot_id.name}',
                        'product_id': ligne.product_id.id,
                        'product_uom': ligne.product_id.uom_id.id,
                        'product_uom_qty': quant.quantity,
                        'location_id': quant.location_id.id,
                        'location_dest_id': obj.emplacement_dst_id.id,
                        'picking_type_id': picking_type.id,
                        'is_scan_inventaire_id': obj.id,  # Lier le mouvement à cet inventaire
                    }
                    
                    # Créer les valeurs pour la ligne de mouvement
                    move_line_vals = {
                        'product_id': ligne.product_id.id,
                        'product_uom_id': ligne.product_id.uom_id.id,
                        'qty_done': quant.quantity,
                        'location_id': quant.location_id.id,
                        'location_dest_id': obj.emplacement_dst_id.id,
                        'lot_id': ligne.lot_id.id,
                    }
                    
                    # Créer les valeurs pour le picking
                    picking_vals = {
                        'picking_type_id': picking_type.id,
                        'location_id': quant.location_id.id,
                        'location_dest_id': obj.emplacement_dst_id.id,
                        'origin': f'Inventaire scan {obj.id}',
                        'move_ids': [(0, 0, move_vals)],
                    }
                    
                    # Créer le picking
                    picking = self.env['stock.picking'].create(picking_vals)
                    
                    # Ajouter la ligne de mouvement au mouvement créé
                    picking.move_ids[0].move_line_ids = [(0, 0, move_line_vals)]
                    
                    # Confirmer et valider le picking
                    picking.action_confirm()
                    picking._action_done()
            
            # Changer l'état à terminé
            obj.state = 'termine'
            
        return True
 
    @api.model
    def on_barcode_scanned(self, barcode):
        """
            Méthode appelée par le widget OWL après le scan pour retourner les valeurs
        """
        return {'barcode': barcode}


# Extension du modèle stock.move pour ajouter la relation inverse
class StockMove(models.Model):
    _inherit = 'stock.move'
    
    is_scan_inventaire_id = fields.Many2one('is.scan.inventaire', 'Inventaire par scan', index=True)


class IsScanInventaireLigne(models.Model):
    _name = 'is.scan.inventaire.ligne'
    _description = 'Lignes inventaire par scan'

    scan_id         = fields.Many2one('is.scan.inventaire', 'Inventaire scan', required=True, ondelete='cascade')
    lot_id          = fields.Many2one('stock.lot', 'Lot/Série')
    product_id      = fields.Many2one('product.product', 'Article')
    quantite        = fields.Float('Quantité', digits='Product Unit of Measure', default=1.0)
    heure_ajout     = fields.Char('Heure d\'ajout', size=8, readonly=True)
    emplacement_ids = fields.Many2many('stock.location', compute='_compute_emplacement_ids', string='Emplacements du lot', store=True)

    @api.depends('lot_id')
    def _compute_emplacement_ids(self):
        for ligne in self:
            if ligne.lot_id:
                # Rechercher tous les quants du lot avec une quantité positive
                quants = self.env['stock.quant'].search([
                    ('lot_id', '=', ligne.lot_id.id),
                    ('quantity', '>', 0),
                    ('location_id.usage', '=', 'internal')
                ])
                # Extraire les emplacements uniques
                emplacements = quants.mapped('location_id')
                ligne.emplacement_ids = [(6, 0, emplacements.ids)]
            else:
                ligne.emplacement_ids = [(5, 0, 0)]  # Vider la relation

    @api.model
    def create(self, vals):
        # Définir l'heure française uniquement lors de la création si elle n'est pas déjà fournie
        if 'heure_ajout' not in vals or not vals['heure_ajout']:
            vals['heure_ajout'] = IsScanInventaire._get_heure_francaise()
        return super().create(vals)

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        if self.lot_id:
            self.product_id = self.lot_id.product_id
            self.heure_ajout = IsScanInventaire._get_heure_francaise()
