ARCHITECTURES = { ARCH_IA64 => "ia64", ARCH_X86 => "x86", ARCH_X86_64 => "x86_64"}

#hard-coding for now
VALID_TARGETS = { 0 => "Bare Metal",
                  1 => "Virtual",
                  2 => "Either"}
#VALID_TARGETS = { IMAGE_TYPE_BAREMETAL => "Bare Metal",
#                  IMAGE_TYPE_VIRT => "Virtual",
#                  IMAGE_TYPE_EITHER => "Either"}

ARCHITECTURES_SELECT = ARCHITECTURES.invert
VALID_TARGETS_SELECT = VALID_TARGETS.invert
BOOLEAN_SELECT = { "Yes" => true, "No" => false }

ERRORS = { ERR_INTERNAL_ERROR => "Internal Error",
           ERR_INVALID_ARGUMENTS => "Invalid Arguments",
           ERR_NO_SUCH_OBJECT => "No Such Object",
           ERR_ORPHANED_OBJECT => "Orphaned Object",
           ERR_PASSWORD_INVALID => "Invalid Password",
           ERR_SQL => "SQL Error",
           ERR_SUCCESS => "Success",
           ERR_TOKEN_EXPIRED => "Expired Token",
           ERR_TOKEN_INVALID => "Invalid Token",
           ERR_UNCAUGHT => "Uncaught exception",
           ERR_USER_INVALID => "Invalid User"}



