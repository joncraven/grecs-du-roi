# Payment publish gate (t_1259dd7a)

Payment buttons on greek.craven.fr are **off** until a human explicitly
re-enables Polar. `deploy/deploy.sh` runs `deploy/gate_payment_publish.py`
on the staged tree and refuses PayPal, Stripe, or any Polar checkout URL
unless `deploy/PAYMENT_PUBLISH_APPROVED` exists with provider=polar and
the exact approved Checkout Link.

See library-site `docs/payment-gating.md` for the allowfile format.
