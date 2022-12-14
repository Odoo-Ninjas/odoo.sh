This module will require registering in eCommerce PagSeguro https://acesso.pagseguro.uol.com.br/

To configure your API keys go to Invoicing -> Configuration -> Payment Acquirers -> PagSeguro.
Then insert your token on the credentials page, as shown below:

.. figure:: ../static/description/payment_acquirer_01.png
    :alt: Payment acquirer pagseguro
    :width: 600 px

Under the configuration page, select your payment journal.
On the upper right corner buttons you can publish on your website and change the environment.

.. figure:: ../static/description/payment_acquirer_02.png
    :alt: Payment acquirer pagseguro
    :width: 600 px

The credential Token and can only be acquired via the PagSeguro user account.
On your account, go to "Venda Online" > "Integrações". Then, click on "Gerar Token".

.. figure:: ../static/description/pagseguro_website.png
    :alt: Payment acquirer pagseguro
    :width: 600 px

Still on the configuration tab, you can configure the maximum amount
of installments available for your clients to select at the
payment.

So far, we only support up to 12 installments, setting a value higher than
that will lead to possible errors on payment.

.. figure:: ../static/description/payment_acquirer_03.png
    :alt: Pagseguro max installments configuration
    :width: 600 px


* full manual for API:

https://dev.pagseguro.uol.com.br/reference/pagseguro-reference-intro
