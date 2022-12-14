import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-helpdesk",
    description="Meta package for oca-helpdesk Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-helpdesk_mgmt',
        'odoo13-addon-helpdesk_mgmt_crm',
        'odoo13-addon-helpdesk_mgmt_partner_sequence',
        'odoo13-addon-helpdesk_mgmt_project',
        'odoo13-addon-helpdesk_mgmt_rating',
        'odoo13-addon-helpdesk_mgmt_sla',
        'odoo13-addon-helpdesk_mgmt_timesheet',
        'odoo13-addon-helpdesk_mgmt_timesheet_time_control',
        'odoo13-addon-helpdesk_mgmtsystem_nonconformity',
        'odoo13-addon-helpdesk_motive',
        'odoo13-addon-helpdesk_type',
        'odoo13-addon-website_helpdesk_mgmt',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 13.0',
    ]
)
