"Constant values."

import re

IUID_RX       = re.compile(r'^[a-f0-9]{32,32}$')
IDENTIFIER_RX = re.compile(r'^[a-z][a-z0-9_]*$', re.I)

# User statuses and roles
ENABLED = 'enabled'
DISABLED = 'disabled'
USER_STATUSES = (ENABLED, DISABLED)
ADMIN     = 'admin'
USER      = 'user'
USER_ROLES = (ADMIN, USER)
