# this file contains numerous codes and strings that are internal to the WUI implementation.
# TODO: not important now, but strings eventually ought to be more i18n-able.

# ==============================================
# display names for the various codes

ARCHITECTURES = { 
    ARCH_IA64    => "ia64", 
    ARCH_X86     => "x86", 
    ARCH_X86_64  => "x86_64"
}

VALID_TARGETS = { 
    PROFILE_IS_BAREMETAL => "Bare-metal",
    PROFILE_IS_VIRT      => "Virtual",
    PROFILE_IS_EITHER    => "Any"
}

#================================================
# mapping of display fields to form values

ARCHITECTURES_SELECT = ARCHITECTURES.invert
VALID_TARGETS_SELECT = VALID_TARGETS.invert

BOOLEAN_SELECT = { 
    "Yes" => true, 
    "No" => false 
}

BOOLEAN_INT_SELECT = { 
    "Yes" => MACHINE_IS_CONTAINER, 
    "No" => MACHINE_IS_NOT_CONTAINER 
}

# =================================================
# Mapping of backend error codes to display strings

ERRORS = { 
    ERR_INTERNAL_ERROR => "Internal Error",
    ERR_MISCONFIGURED => "The shadow XMLRPC interface is not set up yet. Please consult the installation instructions",
    ERR_INVALID_ARGUMENTS => "Invalid Arguments",
    ERR_NO_SUCH_OBJECT => "No Such Object",
    ERR_ORPHANED_OBJECT => "Orphaned Object",
    ERR_PASSWORD_INVALID => "Invalid Password",
    ERR_SQL => "SQL Error",
    ERR_SUCCESS => "Success",
    ERR_TOKEN_EXPIRED => "Expired Token",
    ERR_TOKEN_INVALID => "Invalid Token",
    ERR_UNCAUGHT => "Uncaught exception",
    ERR_USER_INVALID => "Invalid User"
}




