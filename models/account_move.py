# -*- coding: utf-8 -*-
from odoo import models,fields,api


class is_account_move_valobat(models.Model):
    _name='is.account.move.valobat'
    _description = "Synthèse eco-contribution pour Valobat"
    _order='valobat_id'

    move_id           = fields.Many2one('account.move', 'Facture', required=True, ondelete='cascade')
    valobat_id        = fields.Many2one('is.bareme.valobat', 'Code Valobat', required=True)
    currency_id       = fields.Many2one(related='move_id.currency_id')
    eco_contribution  = fields.Monetary("Eco contribution", currency_field='currency_id', required=True)


class AccountMove(models.Model):
    _inherit = "account.move"

    is_export_compta_id     = fields.Many2one('is.export.compta', 'Folio', copy=False)
    is_volume_total         = fields.Float(string="Volume total", digits='Volume', compute='_compute_is_volume_total', store=True, readonly=False)
    is_eco_contribution_ids = fields.One2many('is.account.move.valobat', 'move_id', 'Synthèse Valobat', compute='_compute_is_eco_contribution_ids', store=True, readonly=True)




    # def write(self, vals):
    #     res = super(AccountMove, self).write(vals)
    #     self.maj_synthese_valobat()
    #     return res




    @api.depends('invoice_line_ids','invoice_line_ids.quantity')
    def _compute_is_volume_total(self):
        for obj in self:
            volume = 0
            for line in obj.invoice_line_ids:
                volume+=line.product_id.is_volume*line.quantity
            obj.is_volume_total = volume



    def mise_en_page_hekipia_action(self):
        for obj in self:
            domain=[
                ('move_id','=',obj.id),
                ('display_type', 'in', ('product', 'line_section', 'line_note')),
            ]
            lines= self.env['account.move.line'].search(domain,order="sequence,id")
            for line in lines:
                moves= self.env['stock.move'].search(domain,order="sequence,id")



    @api.depends('invoice_line_ids','state')
    def _compute_is_eco_contribution_ids(self):
        for obj in self:
            valobat_dict={}
            for move_line in obj.invoice_line_ids:
                for sale_line in move_line.sale_line_ids:
                    if sale_line.is_eco_contribution>0:
                        valobat_id = sale_line.is_bareme_valobat_id.id
                        if valobat_id not in valobat_dict:
                            valobat_dict[valobat_id]=0
                        valobat_dict[valobat_id]+=sale_line.is_eco_contribution
            lines=[]
            for key in valobat_dict:
                vals={
                    'move_id'         : obj.id,
                    'valobat_id'      : key,
                    'eco_contribution': valobat_dict[key],
                }
                lines.append([0,0,vals])
            obj.is_eco_contribution_ids.unlink()
            obj.is_eco_contribution_ids = lines
                                                



    

