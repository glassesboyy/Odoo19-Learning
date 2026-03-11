{
    'name': 'Asset Request',
    'version': '19.0.2.0.0',
    'summary': 'Asset Request Form with Dynamic Multi-Level Approval',
    'description': 'Custom module for managing asset requests with configurable approval flows, '
                   'multi-level routing based on brand/model/quantity rules, delegation approvers, '
                   'and comprehensive approval history tracking.',
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
        'data/approval_flow_data.xml',
        # Views
        'views/asset_brand_views.xml',
        'views/asset_brand_model_views.xml',
        'views/approval_flow_views.xml',
        'views/approval_level_views.xml',
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
