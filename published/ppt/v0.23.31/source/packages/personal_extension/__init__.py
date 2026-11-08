# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Personal Extension Profile foundation for private, host-portable composition."""

from .resolver import (
    PERSONAL_EXTENSION_PROFILE_CONTRACT,
    PERSONAL_EXTENSION_RUNTIME_CONTRACT,
    PROVIDER_MANIFEST_CONTRACT,
    PersonalExtensionError,
    build_provider_manifest,
    required_provider_bindings,
    resolve_logical_uri,
    resolve_personal_extension,
    validate_personal_extension_runtime,
    validate_provider_manifest,
    validate_profile,
)

__all__ = [
    "PERSONAL_EXTENSION_PROFILE_CONTRACT",
    "PERSONAL_EXTENSION_RUNTIME_CONTRACT",
    "PROVIDER_MANIFEST_CONTRACT",
    "PersonalExtensionError",
    "build_provider_manifest",
    "required_provider_bindings",
    "resolve_logical_uri",
    "resolve_personal_extension",
    "validate_personal_extension_runtime",
    "validate_provider_manifest",
    "validate_profile",
]
