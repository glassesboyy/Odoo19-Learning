{
    'name': 'Loan Amortization',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Finance',
    'summary': 'Loan Amortization Schedule Calculator',
    'description': """
        Loan Amortization Schedule Calculator
        ======================================
        Calculate amortization schedules based on loan information parameters.

        Features:
        - Create and manage multiple loan records
        - Auto-calculate monthly payment using PMT formula
        - Generate full amortization schedule with one click
        - Track loan status (Draft → Confirmed → Done)
        - Print PDF amortization schedule report
        - Mail thread integration for activity tracking
    """,
    'author': 'Custom',
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'report/loan_amortization_report_action.xml',
        'report/loan_amortization_report.xml',
        'views/loan_amortization_views.xml',
        'views/loan_amortization_menu.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
