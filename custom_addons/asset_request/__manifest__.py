{
    'name': 'Asset Request',
    'version': '19.0.1.0.0',
    'summary': 'Asset Request Form with Multi-Level Approval',
    'description': 'Custom module for managing asset requests with approval matrix, reminders, and tracking.',
    'category': 'Operations',
    'depends': ['base', 'mail'],
    'data': [
        # Security
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        # Data
        'data/ir_sequence_data.xml',
        'data/asset_brand_data.xml',
        'data/mail_template_data.xml',
        'data/ir_cron_data.xml',
        'data/asset_approval_config_data.xml',
        # Views
        'views/asset_brand_views.xml',
        'views/asset_brand_model_views.xml',
        'views/asset_approval_config_views.xml',
        'views/asset_request_views.xml',
        'views/asset_request_menu.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
