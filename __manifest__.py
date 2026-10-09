# -*- coding: utf-8 -*-
{
    'name'     : 'InfoSaône - Module Odoo 16 pour Jurabotec',
    'version'  : '0.1',
    'author'   : 'InfoSaône',
    'category' : 'InfoSaône',
    'description': """
InfoSaône - Module Odoo 16 pour Jurabotec
===================================================
""",
    'maintainer' : 'InfoSaône',
    'website'    : 'http://www.infosaone.com',
    'depends'    : [
        'base',
        "sale_management",
        "purchase",
        "account",
    ],
    'data' : [
        "security/ir.model.access.csv",
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
        "views/is_scan_inventaire_view.xml",
        "views/is_scan_deplacement_charge_view.xml",
        "views/menu.xml",
        "report/conditions_generales_de_vente_templates.xml",
        "report/is_sale_order_colis_report.xml",
        "report/is_stock_quant_report.xml",
        "report/is_stock_location_report.xml",
        "report/sale_report_templates.xml",
        "report/report_deliveryslip.xml",
        "report/report_stockpicking_operations.xml",
        "report/report_invoice.xml",
        "report/report.xml",
    ],
    'installable': True,
    'application': True,
    'qweb': [
    ],
   'assets': {
        'web.assets_backend': [
            'is_jurabotec/static/src/scss/styles.scss',
            'is_jurabotec/static/src/script.js',
            'is_jurabotec/static/src/templates.xml',
        ],

        'web.report_assets_common': [
            'is_jurabotec/static/src/scss/report.scss',

        ]




   },
    'license': 'LGPL-3',
}

