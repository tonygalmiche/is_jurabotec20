# -*- coding: utf-8 -*-
{
    'name'     : 'InfoSaône - Module Odoo 20 pour Jurabotec',
    'version'  : '20.0.0.1',
    'author'   : 'InfoSaône',
    'category' : 'InfoSaône',
    'description': """
InfoSaône - Module Odoo 20 pour Jurabotec
===================================================
Reprise d'is_jurabotec (Odoo 16).
""",
    'maintainer' : 'InfoSaône',
    'website'    : 'http://www.infosaone.com',
    'depends'    : [
        'base',
        "sale_management",
        "sale_stock",       # sale_line_id sur stock.move
        "purchase",
        "purchase_stock",   # purchase_line_id sur stock.move
        "account",
        "mrp",              # mrp.bom
        "l10n_fr_account",  # siret sur res.partner (rapport facture)
    ],
    'data' : [
        "security/ir.access.csv",

        "views/product_view.xml",
        "views/product_pricelist_view.xml",
        "views/purchase_view.xml",
        "views/sale_view.xml",
        "views/stock_view.xml",
        "views/stock_quant_view.xml",
        "views/stock_lot_view.xml",
        "views/res_partner_view.xml",
        "views/account_move_view.xml",
        "views/is_export_compta.xml",
        "views/res_bank_views.xml",
        "views/stock_inventory_view.xml",

        # Migration v20 : vues, menus et rapports désactivés pour installer d'abord les modèles
        # "views/is_scan_inventaire_view.xml",
        # "views/is_scan_deplacement_charge_view.xml",
        # "views/menu.xml",
        # "report/conditions_generales_de_vente_templates.xml",
        # "report/is_sale_order_colis_report.xml",
        # "report/is_stock_quant_report.xml",
        # "report/is_stock_location_report.xml",
        # "report/sale_report_templates.xml",
        # "report/report_deliveryslip.xml",
        # "report/report_stockpicking_operations.xml",
        # "report/report_invoice.xml",
        # "report/report.xml",
    ],
    'installable': True,
    'application': True,
   'assets': {
        'web.assets_backend': [
            'is_jurabotec20/static/src/scss/styles.scss',

            # Migration v20 : composants OWL désactivés en attendant leur migration
            # 'is_jurabotec20/static/src/script.js',
            # 'is_jurabotec20/static/src/templates.xml',
        ],

        'web.report_assets_common': [
            'is_jurabotec20/static/src/scss/report.scss',

        ]




   },
    'license': 'LGPL-3',
}

