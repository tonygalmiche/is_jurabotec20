# -*- coding: utf-8 -*-
from odoo import models,fields,api,tools
from datetime import datetime, timedelta
import pytz


class stock_move(models.Model):
    _inherit = "stock.move"

    inventory_id            = fields.Many2one("stock.inventory", "Inventaire", index=True ) #Champ dans Odoo 8 et supprimé dans Odoo 16


class stock_move_line(models.Model):
    _inherit = "stock.move.line"

    inventory_id = fields.Many2one(related="move_id.inventory_id")


class stock_inventory(models.Model):
    _name='stock.inventory'
    _description="Inventaire (model d'Odoo 8 supprimé dans Odoo 16 => Recréé pour migration)"
    _order="id desc"

    INVENTORY_STATE_SELECTION = [
        ('draft', 'Brouillon'),
        ('cancel', 'Annulé'),
        ('confirm', 'En cours'),
        ('done', 'Validé'),
    ]
    INVENTORY_FILTER_SELECTION = [
        ('none'   , 'Tous les articles'),
        ('product', 'Un article seulement'),
    ]

    name= fields.Char('Référence', required=True, readonly=True, states={'draft': [('readonly', False)]}, default="Inventaire")
    date= fields.Datetime('Date' , required=True, readonly=True, states={'draft': [('readonly', False)]}, default=fields.Datetime.now, copy=False)
    line_ids= fields.One2many('stock.inventory.line', 'inventory_id', 'Lignes', readonly=False, states={'done': [('readonly', True)]}, copy=False)
    move_ids= fields.One2many('stock.move', 'inventory_id', 'Mouvements', help="Inventory Moves.", states={'done': [('readonly', True)]})
    state= fields.Selection(INVENTORY_STATE_SELECTION, 'Etat', readonly=True, index=True, copy=False, default="draft")
    company_id= fields.Many2one('res.company', 'Société', required=True, index=True, readonly=True, default=1)
    location_id= fields.Many2one('stock.location', 'Emplacement', domain=[("usage","=","internal")],  required=True, readonly=True, states={'draft': [('readonly', False)]})
    product_id= fields.Many2one('product.product', 'Article', readonly=True, states={'draft': [('readonly', False)]})
    lot_id= fields.Many2one('stock.lot', 'Lot', readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    filter=fields.Selection(INVENTORY_FILTER_SELECTION, 'Inventaire de', required=True, readonly=True, states={'draft': [('readonly', False)]}, default='none')
    inventaire_id = fields.Many2one('is.inventaire', 'Inventaire général', readonly=True)


    def demarrer_inventaire_action(self):
        for obj in self:
            filtre=[ 
                ('location_id', '=', obj.location_id.id),
            ]
            if obj.product_id and obj.filter=="product":
                filtre.append(('product_id', '=', obj.product_id.id))
            quants=self.env['stock.quant'].search(filtre)
            for quant in quants:
                vals={
                    "inventory_id": obj.id,
                    "location_id": quant.location_id.id,
                    "product_id": quant.product_id.id,
                    "product_uom_id": quant.product_id.uom_id.id,
                    "product_qty": quant.quantity,
                    "prod_lot_id": quant.lot_id.id,
                }
                line=self.env['stock.inventory.line'].create(vals)
            obj.state="confirm"
        return self.continuer_inventaire_action()


    def continuer_inventaire_action(self):
        for obj in self:
            context = {
                'default_inventory_id': obj.id,
                'default_location_id' : obj.location_id.id,
            }
            if obj.product_id and obj.filter=="product":
                context["default_product_id"] = obj.product_id.id
            return {
                'name': 'Lignes',
                'view_mode': 'tree',
                'res_model': 'stock.inventory.line',
                'domain': [
                    ('inventory_id','=',obj.id),
                ],
                'context':context,
                'type': 'ir.actions.act_window',
                'limit': 1000,
            }


    def valider_inventaire_action(self):
        for obj in self:
            for line in obj.line_ids:
                name = obj.name
                qty = line.theoretical_qty - line.product_qty
                inventory_location_id = 14 #TODO ; Emplacement inventaire
                location_id = line.location_id.id
                location_dest_id = inventory_location_id 
                if qty<0:
                    qty=-qty
                    location_dest_id = line.location_id.id
                    location_id = inventory_location_id
                if qty>0:
                    vals={
                        "date_deadline": obj.date,
                        "inventory_id": line.inventory_id.id,
                        "product_id": line.product_id.id,
                        "product_uom": line.product_uom_id.id,
                        "location_id": location_id,
                        "location_dest_id": location_dest_id,
                        "origin": name,
                        "name": name,
                        "reference": name,
                        "procure_method": "make_to_stock",
                        "product_uom_qty": qty,
                        "scrapped": False,
                        "propagate_cancel": True,
                        "is_inventory": True,
                        "additional": False,
                    }
                    move=self.env['stock.move'].create(vals)
                    vals={
                        "move_id": move.id,
                        "product_id": line.product_id.id,
                        "product_uom_id": line.product_uom_id.id,
                        "location_id": location_id,
                        "location_dest_id": location_dest_id,
                        "lot_id": line.prod_lot_id.id,
                        "qty_done": qty,
                        "reference": name,
                    }
                    move_line=self.env['stock.move.line'].create(vals)
                    move._action_confirm()
                    move._action_done()
                    move_line.date=obj.date
            obj.state="done"


    def voir_mouvements_action(self):
        view_id=self.env.ref('stock.view_move_line_tree')
        for obj in self:
            return {
                'name': 'Mouvements',
                'view_mode': 'tree,form',
                'views': [[view_id.id, "list"], [False, "form"]],
                'res_model': 'stock.move.line',
                'domain': [
                    ('inventory_id','=',obj.id),
                    ('qty_done'    ,'!=',0),
                ],
                'type': 'ir.actions.act_window',
                'limit': 1000,
            }


    def voir_inventory_action(self):
        for obj in self:
            res= {
                'name': obj.name,
                'view_mode': 'form',
                'res_model': 'stock.inventory',
                'res_id': obj.id,
                'type': 'ir.actions.act_window',
            }
            return res


class stock_inventory_line(models.Model):
    _name='stock.inventory.line'
    _description="Lignes d'Inventaire (model d'Odoo 8 supprimé dans Odoo 16 => Recréé pour migration)"
    _order="id"

    inventory_id=fields.Many2one('stock.inventory', 'Inventaire', ondelete='cascade', index=True)
    location_id=fields.Many2one('stock.location', 'Emplacement', required=True, index=True)
    product_id=fields.Many2one('product.product', 'Article', required=True, index=True)
    product_uom_id=fields.Many2one('uom.uom', 'unité', compute='_compute_product_id', readonly=True, store=True)
    product_qty=fields.Float('Quantité inventoriée', digits='Product Unit of Measure', default=0)
    company_id=fields.Many2one('res.company', 'Société', index=True, readonly=True,default=1)
    prod_lot_id=fields.Many2one('stock.lot', 'Lot', domain="[('product_id','=',product_id)]")
    state=fields.Selection(related='inventory_id.state')
    theoretical_qty=fields.Float('Quantité théorique', compute='_compute_theoretical_qty', digits='Product Unit of Measure', readonly=True, store=True)
    partner_id=fields.Many2one('res.partner', 'Partenaire')
    product_name=fields.Char('Nom Article'     , compute='_compute_product_id' , readonly=True, store=True)
    location_name=fields.Char('Nom Emplacement', compute='_compute_location_id', readonly=True, store=True)
    prodlot_name=fields.Char('Nom Lot'         , compute='_compute_prod_lot_id', readonly=True, store=True)


    @api.depends('product_id')
    def _compute_product_id(self):
        for obj in self:
            obj.product_uom_id = obj.product_id.uom_id.id
            obj.product_name = obj.product_id.name


    @api.depends('location_id')
    def _compute_location_id(self):
        for obj in self:
            obj.location_name = obj.location_id.name


    @api.depends('prod_lot_id')
    def _compute_prod_lot_id(self):
        for obj in self:
            obj.prodlot_name = obj.prod_lot_id.name


    @api.depends('product_id','prod_lot_id','location_id')
    def _compute_theoretical_qty(self):
        for obj in self:
            filtre=[ 
                ('location_id', '=', obj.location_id.id),
                ('lot_id', '=', obj.prod_lot_id.id),
                ('product_id', '=', obj.product_id.id),
            ]
            quants=self.env['stock.quant'].search(filtre)
            qty=0
            for quant in quants:
                qty+=quant.quantity
            obj.theoretical_qty = qty


class is_inventaire(models.Model):
    _name='is.inventaire'
    _description="Inventaire"
    _order='name desc'

    name          = fields.Char("N°", readonly=True)
    date          = fields.Datetime("Date de l'inventaire", required=True, default=lambda *a: fields.datetime.now())
    inventory_ids = fields.One2many('stock.inventory', 'inventaire_id', 'Inventaires', readonly=True)


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('is.inventaire')
        return super().create(vals_list)


    def utc_offset(self):
        now = datetime.now()
        offset = int(pytz.timezone('Europe/Paris').localize(now).utcoffset().total_seconds()/3600)
        return offset
 

    def creer_inventaires_action(self):
        for obj in self:
            filtre=[ 
                ('usage', '=', 'internal'),
            ]
            locations=self.env['stock.location'].search(filtre,order='name desc')
            for location in locations:
                offset = self.utc_offset()
                date=obj.date+timedelta(hours=offset)
                name = "%s : %s - %s"%(obj.name,date,location.name)
                vals={
                    'name'         : name,
                    'date'         : obj.date,
                    'location_id'  : location.id,
                    'inventaire_id': obj.id,
                }
                inventory = self.env['stock.inventory'].create(vals)
                inventory.demarrer_inventaire_action()

