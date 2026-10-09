# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import ValidationError
from odoo.fields import Command
from datetime import datetime, timedelta
from math import *

class IsSaleOrderColis(models.Model):
    _name='is.sale.order.colis'
    _description = "Colis des commandes"
    _order='sequence'

    order_id     = fields.Many2one('sale.order', 'Commande', required=True, ondelete='cascade')
    sequence     = fields.Integer("Ordre")
    name         = fields.Char("Colis", required=True)
    repartition  = fields.Integer("Répartition", default=8)
    colisage_ids = fields.One2many('is.sale.order.colisage.composant', 'colis_id', 'Colisage')


    def imprimer_fiche_colisage_action(self):
        for obj in self:
            report=self.env.ref('is_jurabotec20.is_sale_order_colis_reports')
            return report.report_action([obj.id])


    def repartir_par1_colis_action(self):
        self.repartir_par_colis_action(maxi=1)


    def repartir_par8_colis_action(self):
        self.repartir_par_colis_action(maxi=8)


    def repartir_par_colis_action(self,maxi=8):
        for obj in self:
            #** Test si supérieur à maxi
            for line in obj.colisage_ids:
                if line.qty_cde<=maxi:
                    raise ValidationError("La quantité commandée doit-être supérieure à %s"%maxi)
                if line.qty!=(line.qty_cde*line.qty_bom):
                    raise ValidationError("Une répartition a déjà été faite")
                
            #** Recherche qty mini
            qty_mini=False
            for line in obj.colisage_ids:
                if line.qty_cde>0:
                    if not qty_mini:
                        qty_mini = line.qty_cde
                    if qty_mini>line.qty_cde:
                        qty_mini = line.qty_cde
            repartition=ceil(qty_mini/maxi)
            if repartition>1:
                #Liste des colis
                dict_colis={}
                name=obj.name
                for i in range(0, repartition):
                    if i==0:
                        dict_colis[i]=obj
                        colis = obj
                    else:
                        colis = obj.copy()
                    colis.name = "%s.%s"%(name,(i+1))
                    dict_colis[i]=colis
                for line in obj.colisage_ids:
                    reste = line.qty_cde
                    if line.qty_cde>0:

                        for i in range(0, repartition):
                            qty=ceil(line.qty_cde/repartition)
                            reste = reste - qty
                            if reste<0:
                                qty=qty+reste
                            if i==0:
                                line.qty=qty*line.qty_bom
                            else:
                                new_line = line.copy()
                                new_line.qty = qty*line.qty_bom
                                new_line.colis_id = dict_colis[i].id


    def lignes_colis_action(self):
        for obj in self:
            return {
                "name": obj.name,
                "view_mode": "list,form",
                "res_model": "is.sale.order.colisage.composant",
                "domain": [
                    ("colis_id","=",obj.id),
                ],
                "type": "ir.actions.act_window",
            }

    def voir_colis_action(self):
        for obj in self:
            res= {
                'name': obj.name,
                'view_mode': 'form',
                'res_model': 'is.sale.order.colis',
                'res_id': obj.id,
                'type': 'ir.actions.act_window',
            }
            return res


class IsSaleOrderColisageComposant(models.Model):
    _name='is.sale.order.colisage.composant'
    _description = "Colisage des composants"

    order_id     = fields.Many2one('sale.order', 'Commande', required=True, ondelete='cascade')
    colis_id     = fields.Many2one('is.sale.order.colis', 'Colis', group_expand='_group_expand_colis_id', required=True)
    product_id   = fields.Many2one("product.product", string="Article", related="sale_line_id.product_id", readonly=True)
    composant_id = fields.Many2one('product.product', 'Composant')
    qty          = fields.Float(string='Quantité', digits='Product Unit')
    qty_bom      = fields.Float(string='Qt nomenclature', digits='Product Unit')
    qty_cde      = fields.Float(related='sale_line_id.product_uom_qty')
    sale_line_id = fields.Many2one('sale.order.line', 'Ligne de commande', required=True)
    colis_ids    = fields.Many2many('is.sale.order.colis', 'is_sale_order_line_colis_ids', 'line_id', 'colis_id', store=False, readonly=True, compute='_compute_colis_ids', string="Colis autorisés")
    state        = fields.Selection(related="order_id.state")
    volume_article = fields.Float(related="composant_id.is_volume")
    date_order   = fields.Datetime(string="Date commande" , store=True, readonly=True, compute='_compute')
    partner_id   = fields.Many2one('res.partner', 'Client', store=True, readonly=True, compute='_compute')
    volume_total = fields.Float("Volume total (m3) "      , store=True, readonly=True, compute='_compute', digits='Volume')
    nb_copies    = fields.Integer("Nombre de copies à faire", default=2)


    @api.depends('order_id','order_id.date_order')
    def _compute(self):
        for obj in self:
            obj.date_order = obj.order_id.date_order
            obj.partner_id = obj.order_id.partner_id.id
            obj.volume_total = obj.qty * obj.volume_article


    @api.depends('colis_id')
    def _compute_colis_ids(self):
        for obj in self:
            ids=[]
            for colis in obj.order_id.is_colis_ids:
                ids.append(colis.id)
            obj.colis_ids= [(6, 0, ids)]


    @api.model
    def _group_expand_colis_id(self, stages, domain):
        colis = stages.order_id.is_colis_ids
        return colis


    def creer_copie_action(self):
        for obj in self:
            if obj.nb_copies>1:
                qty = ceil(obj.qty / obj.nb_copies)
                reste = obj.qty - qty
                obj.qty = qty
                for i in range(1,obj.nb_copies):
                    reste=reste-qty
                    if reste<0:
                        qty = qty+reste
                    copy = obj.copy()
                    copy.qty=qty


    def dupliquer_colis_action(self):
        for obj in self:
            res=obj.copy()
            res.qty=0


    def voir_colis_action(self):
        for obj in self:
            res= {
                'name': obj.colis_id.name,
                'view_mode': 'form',
                'res_model': 'is.sale.order.colis',
                'res_id': obj.colis_id.id,
                'type': 'ir.actions.act_window',
            }
            return res


class sale_order(models.Model):
    _inherit = "sale.order"

    is_colis_ids         = fields.One2many('is.sale.order.colis'             , 'order_id', 'Colis')
    is_colisage_ids      = fields.One2many('is.sale.order.colisage.composant', 'order_id', 'Colisage')
    is_num_cde_client    = fields.Char('N° commande client')
    is_detail_composants = fields.Boolean('Imprimer le détail des composants', default=False)
    is_devis_id          = fields.Many2one('sale.order', "Devis d'origine", copy=False, readonly=True)
    is_volume_total      = fields.Float(string="Volume total", digits='Volume', compute='_compute_is_volume_total', store=True, readonly=False)
    is_gestion_colisage  = fields.Boolean(related="partner_id.is_gestion_colisage")
    is_delai             = fields.Datetime('Délai')
    is_eco_contribution  = fields.Monetary("Eco contribution", compute='_compute_is_eco_contribution', store=True, readonly=True, currency_field='currency_id')
    is_emplacement_charge_id = fields.Many2one(related="partner_id.is_emplacement_charge_id")
    is_charge_ids            = fields.One2many('stock.lot', 'is_sale_order_id', 'Charges')
    is_nombre_unites         = fields.Integer("Nombre d’unités")
    is_solde_commande        = fields.Boolean('Commande soldée', default=False)


    @api.depends('order_line.is_eco_contribution')
    def _compute_is_eco_contribution(self):
        for obj in self:
            is_eco_contribution=0
            for line in obj.order_line:
                is_eco_contribution+=line.is_eco_contribution
            obj.is_eco_contribution = is_eco_contribution


    def write(self, vals):
        res = super(sale_order, self).write(vals)
        self.ajout_eco_contribution()
        return res


    def action_confirm(self):
        res = super(sale_order, self).action_confirm()
        for obj in self:
            if obj.is_emplacement_charge_id:
                domain=[
                    ('sale_id', '=' , obj.id),
                    ('state'  , '!=', 'cancel'),
                ]
                pickings = self.env['stock.picking'].search(domain,limit=1)
                for picking in pickings:
                    picking.move_line_ids.unlink()
                    for line in obj.order_line:
                        if line.is_charge_id:
                            vals={
                                "picking_id"        : picking.id,
                                "product_id"        : line.product_id.id,
                                "lot_id"            : line.is_charge_id.id,
                                "company_id"        : picking.company_id.id,
                                "uom_id"            : line.product_id.uom_id.id,
                                "location_id"       : obj.is_emplacement_charge_id.id,
                                "quantity"          : line.product_uom_qty,
                                "picked"            : True,
                            }
                            self.env['stock.move.line'].create(vals)
        return res


    def ajout_eco_contribution(self):
        for obj in self:
            if obj.is_eco_contribution>0:
                products = self.env['product.product'].search([('default_code','=','ECO-CONTRIBUTION')])
                for product in products:
                    sequence = 0
                    order_line=False
                    for line in obj.order_line:
                        if line.sequence>sequence:
                            sequence=line.sequence
                        if line.product_id == product:
                            order_line = line
                    sequence+=10
                    if not order_line:
                        vals={
                            'order_id': obj.id,
                            'product_id': product.id,
                            'name': product.display_name,
                            'product_uom_qty': 1,
                            'price_unit':obj.is_eco_contribution,
                            'sequence': sequence,
                        }
                        res=self.env['sale.order.line'].create(vals)
                    else:
                        order_line.sequence=sequence
                        order_line.price_unit = obj.is_eco_contribution


    @api.onchange('date_order')
    def _onchange_date_order(self):
        if not self.is_delai and self.date_order:
            delai = self.date_order+timedelta(days=6*7)
            self.is_delai = delai


    @api.depends('order_line','order_line.product_uom_qty','is_solde_commande')
    def _compute_is_volume_total(self):
        for obj in self:
            volume = 0
            for line in obj.order_line:
                line._onchange_product_uom_qty()
                volume+=line.is_volume_total
            obj.is_volume_total = volume


    def _create_invoices(self, final=False, grouped=False):
        # Commandes facturées dans l'ordre de création, avec une section par commande (voir _prepare_invoice)
        orders = self.sorted('id').with_context(is_section_commande=True)
        return super(sale_order, orders)._create_invoices(final=final, grouped=grouped)


    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        if self.env.context.get('is_section_commande'):
            # Section en tête des lignes de la commande (invoice_line_ids est vide à ce stade)
            invoice_vals['invoice_line_ids'].append(Command.create(self._get_section_commande_vals()))
        return invoice_vals


    def _get_section_commande_vals(self):
        """Section de la commande sur la facture : commande, références client et livraisons à facturer"""
        self.ensure_one()

        #** Recherche des livraisons à facturer pour indiquer le BL ********
        pickings=[]
        for line in self.order_line:
            if line.qty_invoiced<line.qty_delivered:
                for move in line.move_ids:
                    if move.state=='done' and move.picking_id not in pickings:
                        pickings.append(move.picking_id)
        #******************************************************************

        list=[]
        list.append("Commande : %s"%self.name)
        if self.client_order_ref:
            list.append("Référence client : %s"%self.client_order_ref)
        if self.is_num_cde_client:
            list.append("N° commande client : %s"%self.is_num_cde_client)
        for picking in pickings:
            list.append("Livraison : %s"%picking.name)
        return {
            'display_type': 'line_section',
            'name': " - ".join(list),
            'sequence': -1, # Avant les lignes de la commande (renumérotées par Odoo si plusieurs commandes sur une facture)
        }


    def convertir_en_commande_action(self):
        for obj in self:
            copy = obj.copy()
            copy.is_devis_id = obj.id
            res= {
                'name': copy.name,
                'view_mode': 'form',
                'res_model': 'sale.order',
                'res_id': copy.id,
                'type': 'ir.actions.act_window',
            }
            return res


    def colisage_init_ir_cron(self):
        self.env['sale.order'].search([]).colisage_init()


    def colisage_action(self):
        for obj in self:
            if obj.is_gestion_colisage:
                obj.colisage_init()
                return {
                    "name": "Colisage des composants %s"%(obj.name),
                    "view_mode": "kanban,list,form",
                    "res_model": "is.sale.order.colisage.composant",
                    "domain": [
                        ("order_id","=",obj.id),
                    ],
                    "type": "ir.actions.act_window",
                }


    def reinit_colisage_action(self):
        for obj in self:
            obj.is_colisage_ids.unlink()
            obj.is_colis_ids.unlink()
            obj.colisage_action()


    def colisage_init(self):
        for obj in self:

            if obj.is_gestion_colisage:
                "A livrer"

                #** Création colis par défaut si inexistant *******************
                if len(obj.is_colis_ids)==0:
                    vals={
                        'order_id': obj.id,
                        'name'    : 'A livrer',
                        'sequence': 1,
                    }
                    self.env['is.sale.order.colis'].create(vals)
                #**************************************************************

                if len(obj.is_colisage_ids)==0 and len(obj.is_colis_ids)>0:
                    for line in obj.order_line:
                        filtre=[
                            ('product_tmpl_id', '=', line.product_id.product_tmpl_id.id),
                            ('type'           , '=', 'commande'),
                        ]
                        boms = self.env['mrp.bom'].search(filtre,limit=1)
                        if len(boms)>0:
                            for bom_line in boms[0].bom_line_ids:
                                vals={
                                    "colis_id"    : obj.is_colis_ids[0].id,
                                    "order_id"    : obj.id,
                                    "composant_id": bom_line.product_id.id,
                                    "qty"         : line.product_uom_qty*bom_line.product_qty,
                                    "qty_bom"     : bom_line.product_qty,
                                    "sale_line_id": line.id,
                                }
                                res = self.env['is.sale.order.colisage.composant'].create(vals)
                        else:
                            vals={
                                "colis_id": obj.is_colis_ids[0].id,
                                "order_id": obj.id,
                                "composant_id": line.product_id.id,
                                "qty": line.product_uom_qty,
                                "sale_line_id": line.id,
                            }
                            res = self.env['is.sale.order.colisage.composant'].create(vals)


    def liste_colis_action(self):
        for obj in self:
           return {
                "name": "Colis %s"%(obj.name),
                "view_mode": "list,form",
                "res_model": "is.sale.order.colis",
                "domain": [
                    ("order_id","=",obj.id),
                ],
                "type": "ir.actions.act_window",
            }


    def associer_charges_action(self):
        for obj in self:
            domain=[
                ('location_id','=',obj.is_emplacement_charge_id.id)
            ]
            quants = self.env['stock.quant'].search(domain)
            ids=[]
            for quant in quants:
                if  quant.quantity>0 and quant.lot_id:
                    order_id = quant.lot_id.is_sale_order_id.id
                    if order_id==obj.id or order_id==False:
                        ids.append(quant.lot_id.id)
            view_id = self.env.ref('is_jurabotec20.is_stock_lot_sale_order_kanban_view', False)
            ctx={
                'is_sale_order_id':  obj.id,
            }
            return {
                "name": "Charges",
                "view_mode": "kanban,list,form",
                "views": [(view_id.id, 'kanban'),(False, 'list'),(False, 'form')],
                "res_model": "stock.lot",
                "domain": [
                    ("id","in",ids),
                ],
                "type": "ir.actions.act_window",
                "context": ctx,
            }


    def actualiser_lignes_action(self):
        for obj in self:
            obj.order_line.unlink()
            sequence=10
            for charge in obj.is_charge_ids:
                vals={
                    'order_id'    : obj.id,
                    'product_id'  : charge.product_id.id,
                    'name'        : charge.product_id.display_name,
                    'sequence'    : sequence,
                    'is_charge_id': charge.id,
                }
                line = self.env['sale.order.line'].create(vals)
                line._onchange_product_id()
                line.product_uom_qty = charge.product_qty
                line._onchange_product_uom_qty()
                line._compute_longeur()
                sequence+=10


class sale_order_line(models.Model):
    _inherit = "sale.order.line"

    is_composants     = fields.Html(string='Composants', compute='_compute_is_composants')
    is_composants_ids = fields.One2many('is.sale.order.colisage.composant', 'sale_line_id', 'Lignes des composants')
    is_prix_tarif  = fields.Float(string="Prix tarif", digits='Product Unit', help="Tarif de la liste de prix")
    is_unite_tarif = fields.Selection([
        ('m'    , 'm'),
        ('m2'   , 'm2'),
        ('m3'   , 'm3'),
        ('unite', 'Unité'),
    ], "Unité", help="Unité de la liste de prix")

    is_longueur        = fields.Float(string="Longueur",      digits='Product Unit', compute='_compute_longeur')
    is_surface         = fields.Float(string="Surface",       digits='Product Unit', compute='_compute_longeur')
    is_volume          = fields.Float(string="Volume",        digits='Volume'                 , compute='_compute_longeur')

    is_longueur_totale = fields.Float(string="Longueur cde",  digits='Product Unit')
    is_surface_totale  = fields.Float(string="Surface cde",   digits='Product Unit')
    is_volume_total    = fields.Float(string="Volume cde",    digits='Volume')
    is_longueur_product = fields.Float(string="Longueur product", digits='Product Unit', related="product_id.is_longueur", readonly=True)

    is_quantite_saisie  = fields.Float("Quantité saisie"      , digits='Product Unit')
    is_largeur_saisie   = fields.Float("Largeur saisie (mm)"  , digits='Product Unit')
    is_epaisseur_saisie = fields.Float("Epaisseur saisie (mm)", digits='Product Unit')
    is_longueur_saisie  = fields.Float("Longueur saisie (m)"  , digits='Product Unit')

    is_detail_quantite  = fields.Text(string='Détail quantité', compute='_compute_is_detail_quantite')
    is_num_palette      = fields.Char(string='N°Palette')

    is_bareme_valobat_id = fields.Many2one(related='product_id.is_bareme_valobat_id')
    is_eco_contribution  = fields.Monetary("Eco contribution", compute='_compute_is_eco_contribution', store=True, readonly=True, currency_field='currency_id')
    is_charge_id         = fields.Many2one('stock.lot', string="Charge", readonly=True, copy=False)
    is_onchange_origine  = fields.Char(store=False, help="Champ modifié par l'utilisateur, pour ne pas enchaîner les onchange des quantités (voir _onchange_autorise)")


    @api.depends('product_id', 'product_uom_qty')
    def _compute_is_eco_contribution(self):
        for obj in self:
            eco_contribution = obj.product_id.is_eco_contribution * obj.product_uom_qty
            obj.is_eco_contribution = eco_contribution


    @api.depends('product_id', 'is_largeur_saisie', 'is_epaisseur_saisie','is_longueur_saisie')
    def _compute_longeur(self):
        for obj in self:
            if obj.product_id.is_longueur>0:
                is_longueur = obj.product_id.is_longueur
                is_surface  = obj.product_id.is_surface
                is_volume   = obj.product_id.is_volume
            else:
                is_longueur = obj.is_longueur_saisie
                is_surface  = obj.is_longueur_saisie * obj.is_largeur_saisie / 1000
                is_volume   = obj.is_longueur_saisie * obj.is_largeur_saisie * obj.is_epaisseur_saisie / 1000/1000
            obj.is_longueur    = is_longueur
            obj.is_surface     = is_surface
            obj.is_volume      = is_volume


    @api.depends('product_id', 'product_uom_qty', 'is_longueur_totale', 'is_surface_totale', 'is_volume_total')
    def _compute_is_detail_quantite(self):
        for obj in self:
            x = False
            if obj.is_quantite_saisie and  obj.is_epaisseur_saisie and obj.is_largeur_saisie:
                x = "%.0f pièces de %.0fx%.0f. "%(obj.is_quantite_saisie, obj.is_epaisseur_saisie, obj.is_largeur_saisie)
            if obj.product_uom_qty and obj.is_longueur  and obj.is_longueur_totale and obj.is_surface_totale:
                if not x:
                    x=""
                x = "%sLongueur de %.1fm soit %.1fml ou %.1fm2"%(x,obj.is_longueur, obj.is_longueur_totale, obj.is_surface_totale)
            obj.is_detail_quantite = x


    @api.depends('product_id', 'product_uom_id', 'product_uom_qty','is_prix_tarif','is_unite_tarif','product_uom_qty')
    def _compute_price_unit(self):
        for line in self:
            price = 0
            if line.product_id:
                for l in line.product_id.product_template_variant_value_ids:
                    if l.attribute_line_id.attribute_id.name=="Longueur":
                        variante = l.product_attribute_value_id.name
                        if variante in ['ml','m2','m','u']:
                            price = line.is_prix_tarif
                if price==0:
                    if line.is_unite_tarif=="m":
                        price = line.is_prix_tarif*line.is_longueur
                    if line.is_unite_tarif=="m2":
                        price = line.is_prix_tarif*line.is_surface
                    if line.is_unite_tarif=="m3":
                        price = line.is_prix_tarif*line.is_volume
                    if line.is_unite_tarif=="unite":
                        price = line.is_prix_tarif
            line.price_unit = price


    # Remplace volontairement (sans super) le _onchange_product_id ajouté par Odoo en v17 :
    # il appelle _reset_price_unit(), qui écraserait le prix calculé par _compute_price_unit (m, m2, m3)
    @api.onchange('product_id','product_template_id', 'product_uom_qty')
    def _onchange_product_id(self):
        price = 0
        unite = False
        pricelist = self.order_id.pricelist_id
        if pricelist:
            #** Recherche dans les variantes **********************************
            for line in pricelist.item_ids:
                if line.product_id == self.product_id:
                    price = line.fixed_price
                    unite = line.is_unite
                    break
            #** Recherche dans les artciles si non trouvé *********************
            if price==0:
                for line in pricelist.item_ids:
                    if line.product_tmpl_id == self.product_template_id and self.product_uom_qty>=line.min_quantity:
                        price = line.fixed_price
                        unite = line.is_unite
                        break       
        self.is_prix_tarif  = price
        self.is_unite_tarif = unite


    def _get_dimensions(self):
        if self.product_id.is_longueur:
            longueur  = self.product_id.is_longueur
            largeur   = self.product_id.is_largeur
            epaisseur = self.product_id.is_epaisseur
        else:
            longueur  = self.is_longueur_saisie
            largeur   = self.is_largeur_saisie
            epaisseur = self.is_epaisseur_saisie
        return longueur, largeur, epaisseur


    def _get_type_unite(self):
        """Type de l'unité de la ligne (les catégories d'unités ont été supprimées en v19) :
        recherche de l'unité standard qui a la même unité de référence"""
        for xmlid, type_unite in [
            ('uom.product_uom_unit'        , 'Unité'),
            ('uom.product_uom_meter'       , 'Longueur/distance'),
            ('uom.product_uom_square_meter', 'Surface'),
            ('uom.product_uom_cubic_meter' , 'Volume'),
        ]:
            uom = self.env.ref(xmlid, raise_if_not_found=False)
            if uom and self.product_uom_id and self.product_uom_id._has_common_reference(uom):
                return type_unite
        return False


    def _onchange_autorise(self, field_name):
        """En v20, les onchange des champs modifiés par un onchange sont relancés : seul celui du champ
        modifié par l'utilisateur doit recalculer les autres quantités (remplace le contexte noonchange)"""
        if self.is_onchange_origine and self.is_onchange_origine != field_name:
            return False
        self.is_onchange_origine = field_name
        return True


    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty(self):
        if self._onchange_autorise('product_uom_qty'):
            longueur, largeur, epaisseur = self._get_dimensions()
            unite = self._get_type_unite()
            surface  = volume   = 0
            if unite=='Unité':
                longueur = self.product_uom_qty * self.is_longueur
                surface  = self.product_uom_qty * self.is_surface
                volume   = self.product_uom_qty * self.is_volume
            if unite=='Longueur/distance':
                longueur = self.product_uom_qty
                surface  = self.product_uom_qty * largeur / 1000
                volume   = self.product_uom_qty * largeur * epaisseur / 1000 / 1000
            if unite=='Surface':
                surface  = self.product_uom_qty
                if largeur>0:
                    longueur = 1000 * self.product_uom_qty / largeur
                volume = self.product_uom_qty * epaisseur /1000
            if unite=='Volume':
                volume  = self.product_uom_qty
                if epaisseur>0:
                    surface = 1000 * self.product_uom_qty / epaisseur
                    if largeur>0:
                        longueur = 1000 * 1000 * self.product_uom_qty / epaisseur / largeur
            self.is_longueur_totale = longueur
            self.is_surface_totale  = surface
            self.is_volume_total    = volume


    @api.onchange('is_longueur_totale')
    def _onchange_is_longueur_totale(self):
        if self._onchange_autorise('is_longueur_totale'):
            qty = surface = volume = 0
            longueur, largeur, epaisseur = self._get_dimensions()
            unite = self._get_type_unite()
            if unite=='Unité':
                if longueur>0:
                    qty = self.is_longueur_totale/longueur
            if unite=='Longueur/distance':
                qty = self.is_longueur_totale
            if unite=='Surface':
                qty = self.is_longueur_totale * largeur/1000
            if unite=='Volume':
                qty = self.is_longueur_totale * largeur/1000 * epaisseur/1000
            surface = self.is_longueur_totale * largeur/1000
            volume  = self.is_longueur_totale * largeur/1000 * epaisseur/1000
            self.product_uom_qty   = qty
            self.is_surface_totale = surface
            self.is_volume_total   = volume


    @api.onchange('is_surface_totale')
    def _onchange_is_surface_totale(self):
        if self._onchange_autorise('is_surface_totale'):
            longueur, largeur, epaisseur = self._get_dimensions()
            unite = self._get_type_unite()
            qty = 0
            if unite=='Unité':
                if self.is_surface>0:
                    qty = self.is_surface_totale/self.is_surface
            if unite=='Longueur/distance':
                if self.is_surface>0:
                    qty = self.is_surface_totale/self.is_surface
            if unite=='Surface':
                qty = self.is_surface_totale 
            if unite=='Volume':
                if epaisseur>0:
                    qty = self.is_surface_totale*epaisseur/1000
            longueur_totale = 0
            if  largeur>0:
                longueur_totale = 1000*self.is_surface_totale / largeur
            volume = self.is_surface_totale * epaisseur/1000
            self.product_uom_qty    = qty
            self.is_longueur_totale = longueur_totale
            self.is_volume_total    = volume


    @api.onchange('is_volume_total')
    def _onchange_is_volume_total(self):
        if self._onchange_autorise('is_volume_total'):
            longueur, largeur, epaisseur = self._get_dimensions()
            unite = self._get_type_unite()
            qty = longueur_totale = surface = 0
            if unite=='Unité':
                if self.is_volume>0:
                    qty = self.is_volume_total/self.is_volume
            if unite=='Longueur/distance':
                if epaisseur>0 and largeur>0:
                    qty = 1000 * 1000 * self.is_volume_total / epaisseur / largeur
            if unite=='Surface':
                if epaisseur>0:
                    qty = 1000  * self.is_volume_total / epaisseur 
            if unite=='Volume':
                qty = self.is_volume_total
            if epaisseur>0 and largeur>0:
                longueur_totale = 1000*1000*self.is_volume_total / largeur / epaisseur
            if epaisseur>0:
                surface = 1000 * self.is_volume_total / epaisseur
            self.product_uom_qty    = qty
            self.is_longueur_totale = longueur_totale
            self.is_surface_totale  = surface


    def _compute_is_composants(self):
        for obj in self:
            t=[]
            for line in obj.is_composants_ids:
                t.append("<div>- %s x %s</div>"%(line.qty, line.composant_id.name))
            html = "\n".join(t)
            obj.is_composants = html


    @api.onchange('is_quantite_saisie','is_largeur_saisie', 'is_epaisseur_saisie','is_longueur_saisie')
    def _onchange_is_quantite_saisie(self):
        unite = self._get_type_unite()
        if unite=='Unité':
            self.product_uom_qty = self.is_quantite_saisie
        if unite=='Volume':
            self.product_uom_qty = self.is_quantite_saisie * self.is_volume
        if unite=='Surface':
            self.product_uom_qty = self.is_quantite_saisie * self.is_surface
