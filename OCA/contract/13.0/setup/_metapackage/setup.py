import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-contract",
    description="Meta package for oca-contract Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-agreement',
        'odoo13-addon-agreement_legal',
        'odoo13-addon-agreement_maintenance',
        'odoo13-addon-agreement_rebate',
        'odoo13-addon-agreement_rebate_partner_company_group',
        'odoo13-addon-agreement_sale',
        'odoo13-addon-agreement_serviceprofile',
        'odoo13-addon-contract',
        'odoo13-addon-contract_layout_category_hide_detail',
        'odoo13-addon-contract_mandate',
        'odoo13-addon-contract_payment_mode',
        'odoo13-addon-contract_price_revision',
        'odoo13-addon-contract_sale',
        'odoo13-addon-contract_variable_qty_timesheet',
        'odoo13-addon-contract_variable_quantity',
        'odoo13-addon-product_contract',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 13.0',
    ]
)
