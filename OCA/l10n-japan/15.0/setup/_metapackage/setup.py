import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-l10n-japan",
    description="Meta package for oca-l10n-japan Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-l10n_jp_address_layout>=15.0dev,<15.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 15.0',
    ]
)
