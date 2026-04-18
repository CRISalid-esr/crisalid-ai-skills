#!/bin/sh
# If a custom CA cert is mounted, add it to the trust store before starting.
if [ -f /usr/local/share/ca-certificates/custom-ca.crt ]; then
    update-ca-certificates
fi
exec toolbox "$@"
