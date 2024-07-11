# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
import sys
import types
from unittest.mock import Mock

module_name = "lux"
lux_module = types.ModuleType(module_name)
sys.modules[module_name] = lux_module
this_module = sys.modules[module_name]
# Usage: set mocked names here, set mocked return values/properties in unit tests.
# Mocked names
setattr(this_module, "getSceneInfo", Mock(name=module_name + ".getSceneInfo"))
setattr(this_module, "getExternalFiles", Mock(name=module_name + ".getExternalFiles"))
setattr(this_module, "getAnimationFrame", Mock(name=module_name + ".getAnimationFrame"))
setattr(this_module, "savePackage", Mock(name=module_name + ".savePackage"))
