import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-l10n-brazil",
    description="Meta package for oca-l10n-brazil Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-l10n_br_base>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_crm>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_stock>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_zip>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
