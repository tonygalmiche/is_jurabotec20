# -*- coding: utf-8 -*-
from odoo import models, fields, api   # type: ignore
from odoo.exceptions import UserError  # type: ignore


class IsScanDeplacementCharge(models.Model):
    _name = 'is.scan.deplacement.charge'
    _description = 'Déplacement de charge par scan'
    _order = 'id desc'
    _rec_name = "id"

    barcode_input = fields.Char(string='Input utilisé par le widget pour récupérer les données du scan')
    barcode_scan  = fields.Char(string='Résultat du scan')
    alert_message = fields.Char(string='Message alerte')
    alert_type    = fields.Selection([('success', 'Succès'), ('warning', 'Avertissement')], string='Type alerte')
    lot_id = fields.Many2one('stock.lot', 'Lot/Charge', readonly=True)
    product_id = fields.Many2one('product.product', 'Article', related='lot_id.product_id', readonly=True, store=True)
    emplacement_src_id = fields.Many2one('stock.location', 'Emplacement source', readonly=True)
    emplacement_dst_id = fields.Many2one('stock.location', 'Emplacement de destination', readonly=True)
    move_ids = fields.One2many('stock.move', 'is_scan_deplacement_charge_id', string='Mouvements créés', readonly=True)
    move_count = fields.Integer(string='Nb mouvements', compute='_compute_move_count', store=True)
    state = fields.Selection([
        ('lot', 'Scan charge'),
        ('emplacement', 'Scan emplacement'),
        ('termine', 'Terminé')
    ], string='État', default='lot', required=True)

    @api.depends('move_ids')
    def _compute_move_count(self):
        for rec in self:
            rec.move_count = len(rec.move_ids)
    message_scan = fields.Char(string='Message de scan', compute='_compute_message_scan')

    @api.depends('state')
    def _compute_message_scan(self):
        for record in self:
            if record.state == 'lot':
                record.message_scan = 'Scannez la charge'
            elif record.state == 'emplacement':
                record.message_scan = "Scannez l'emplacement"
            else:
                record.message_scan = ''

    @api.onchange('barcode_scan')
    def _onchange_barcode_scan(self):
        barcode = self.barcode_scan
        if not barcode:
            return

        if self.state == 'lot':
            lot = self.env['stock.lot'].search([('name', '=', barcode)], limit=1)
            if not lot:
                self.alert_message = f'Charge "{barcode}" non trouvée'
                self.alert_type = 'warning'
                return

            quant = self.env['stock.quant'].search([
                ('lot_id', '=', lot.id),
                ('quantity', '>', 0),
                ('location_id.usage', '=', 'internal')
            ], limit=1)
            if not quant:
                article_name = lot.product_id.name if lot.product_id else 'Article inconnu'
                self.alert_message = f'Charge "{barcode}" ({article_name}) non trouvée - aucun stock disponible'
                self.alert_type = 'warning'
                return

            self.lot_id = lot.id
            self.emplacement_src_id = quant.location_id.id
            self.state = 'emplacement'
            article_name = lot.product_id.name if lot.product_id else 'Article inconnu'
            self.alert_message = f'Charge "{lot.name}" de l\'article "{article_name}" scannée'
            self.alert_type = 'success'

        elif self.state == 'emplacement':
            if barcode.startswith('E'):
                try:
                    loc_id = int(barcode[1:])
                except Exception:
                    loc_id = 0
                location = self.env['stock.location'].search([('id', '=', loc_id), ('usage', '=', 'internal')], limit=1)
            else:
                location = self.env['stock.location'].search([('name', '=', barcode), ('usage', '=', 'internal')], limit=1)

            if not location:
                self.lot_id = False
                self.emplacement_src_id = False
                self.state = 'lot'
                self.alert_message = f'Emplacement "{barcode}" non trouvé — scannez à nouveau la charge'
                self.alert_type = 'warning'
                return

            if self.emplacement_src_id.id == location.id:
                lot_name = self.lot_id.name if self.lot_id else ''
                article_name = self.product_id.name if self.product_id else ''
                emplacement_name = location.complete_name or location.name
                self.lot_id = False
                self.emplacement_src_id = False
                self.state = 'lot'
                self.alert_message = f'La charge "{lot_name}" ({article_name}) est déjà dans l\'emplacement "{emplacement_name}"'
                self.alert_type = 'warning'
                return

            self.emplacement_dst_id = location.id
            return self._deplacer_charge()

    def _deplacer_charge(self):
        if not self.lot_id or not self.emplacement_dst_id:
            raise UserError("Lot et emplacement de destination requis")

        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        if not picking_type:
            raise UserError("Aucun type de picking interne trouvé")

        quants = self.env['stock.quant'].search([
            ('lot_id', '=', self.lot_id.id),
            ('quantity', '>', 0),
            ('location_id', '=', self.emplacement_src_id.id)
        ])
        if not quants:
            raise UserError(f"Aucun stock trouvé pour le lot {self.lot_id.name} dans l'emplacement {self.emplacement_src_id.name}")

        real_id = self._origin.id
        lot_name = self.lot_id.name
        article_name = self.product_id.name if self.product_id else ''
        emplacement_dest_name = self.emplacement_dst_id.complete_name or self.emplacement_dst_id.name

        for quant in quants:
            picking = self.env['stock.picking'].create({
                'picking_type_id': picking_type.id,
                'location_id': self.emplacement_src_id.id,
                'location_dest_id': self.emplacement_dst_id.id,
                'origin': f'Déplacement charge {real_id}',
                'move_ids': [(0, 0, {
                    'name': f'Déplacement charge - {self.lot_id.name}',
                    'product_id': self.product_id.id,
                    'product_uom': self.product_id.uom_id.id,
                    'product_uom_qty': quant.quantity,
                    'location_id': self.emplacement_src_id.id,
                    'location_dest_id': self.emplacement_dst_id.id,
                    'picking_type_id': picking_type.id,
                    'is_scan_deplacement_charge_id': real_id,
                })],
            })
            picking.move_ids[0].move_line_ids = [(0, 0, {
                'product_id': self.product_id.id,
                'product_uom_id': self.product_id.uom_id.id,
                'qty_done': quant.quantity,
                'location_id': self.emplacement_src_id.id,
                'location_dest_id': self.emplacement_dst_id.id,
                'lot_id': self.lot_id.id,
            })]
            picking.action_confirm()
            picking._action_done()
            # Forcer le lien sur tous les mouvements (action_done peut en créer de nouveaux)
            picking.move_ids.write({'is_scan_deplacement_charge_id': real_id})

        # Réinitialiser pour le prochain scan
        self.write({'lot_id': False, 'emplacement_src_id': False, 'emplacement_dst_id': False, 'state': 'lot'})

        # Afficher tous les mouvements de cette session
        self.move_ids = self.env['stock.move'].search([('is_scan_deplacement_charge_id', '=', real_id)])

        self.alert_message = f'Emplacement "{emplacement_dest_name}" scanné - charge "{lot_name}" ({article_name}) déplacée'
        self.alert_type = 'success'

    def terminer_action(self):
        for obj in self:
            obj.state = 'termine'
        return True

    def voir_mouvements_action(self):
        for obj in self:
            return {
                "name": f"Mouvements déplacement charge {obj.id}",
                "view_mode": "tree,form",
                "res_model": "stock.move.line",
                "domain": [("move_id.is_scan_deplacement_charge_id", "=", obj.id)],
                "type": "ir.actions.act_window",
            }

    @api.model
    def on_barcode_scanned(self, barcode):
        return {'barcode': barcode}


class StockMove(models.Model):
    _inherit = 'stock.move'

    is_scan_deplacement_charge_id = fields.Many2one('is.scan.deplacement.charge', 'Déplacement de charge', index=True)
