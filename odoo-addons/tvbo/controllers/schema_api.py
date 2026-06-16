# -*- coding: utf-8 -*-
from odoo import http
from typing import get_origin, get_args, Union

# Lazy handle to the tvbo Pydantic datamodel module (deferred to avoid a heavy
# import at addon load and any circular import with the tvbo package).
_datamodel = None

# Back-compat aliases: older schema revisions exposed Monitor / ObservationModel
# / ProcessingStep; the current schema folds these into Observation (whose
# ``pipeline`` is a list of FunctionCall). Map legacy names onto current ones so
# existing callers keep working.
_CLASS_ALIASES = {
    'Monitor': 'Observation',
    'ObservationModel': 'Observation',
    'ProcessingStep': 'FunctionCall',
}


def _get_datamodel():
    """Lazily import :mod:`tvbo.datamodel.pydantic`; ``None`` if unavailable."""
    global _datamodel
    if _datamodel is None:
        try:
            import importlib
            _datamodel = importlib.import_module('tvbo.datamodel.pydantic')
        except ImportError:
            _datamodel = False
    return _datamodel or None


def _resolve_class(model_name):
    """Resolve a (possibly legacy) class name to a current Pydantic model."""
    from pydantic import BaseModel
    mod = _get_datamodel()
    if not mod:
        return None
    cls = getattr(mod, _CLASS_ALIASES.get(model_name, model_name), None)
    if isinstance(cls, type) and issubclass(cls, BaseModel):
        return cls
    return None


class SchemaAPIController(http.Controller):

    @http.route(
        "/tvbo/api/schema/model/<string:model_name>",
        type="jsonrpc",
        auth="user",
        methods=["GET"],
    )
    def get_model_schema(self, model_name, **kwargs):
        """Get the Pydantic field schema for any tvbo datamodel class.

        Resolves legacy class names (Monitor / ObservationModel ->
        Observation, ProcessingStep -> FunctionCall) for back-compat.
        """
        if _get_datamodel() is None:
            return {"error": "tvbo datamodel not available"}

        model_class = _resolve_class(model_name)
        if model_class is None:
            return {"error": f"Model {model_name} not found"}

        return self._extract_field_schema(model_class)

    def _extract_field_schema(self, model_class):
        """Extract field information from a Pydantic model"""
        schema = {
            "name": model_class.__name__,
            "doc": model_class.__doc__,
            "fields": [],
        }

        # Get model fields
        for field_name, field_info in model_class.model_fields.items():
            field_schema = self._process_field(field_name, field_info)
            schema["fields"].append(field_schema)

        return schema

    def _process_field(self, field_name, field_info):
        """Process a single Pydantic field"""
        field_type = field_info.annotation

        # Extract base type and check if optional
        is_optional = False
        is_list = False
        base_type = field_type

        # Handle Union types (Optional is Union[T, None])
        origin = get_origin(field_type)
        if origin is Union:
            args = get_args(field_type)
            # Check if it's Optional (Union with None)
            if type(None) in args:
                is_optional = True
                # Get the non-None type
                base_type = next((arg for arg in args if arg is not type(None)), str)
                origin = get_origin(base_type)

        # Handle list types
        if origin is list:
            is_list = True
            list_args = get_args(base_type)
            if list_args:
                base_type = list_args[0]

        # Determine field type category
        type_name = self._get_type_name(base_type)

        # Get enum values if applicable
        enum_values = None
        if hasattr(base_type, "__members__"):  # It's an enum
            enum_values = [{"value": v.value, "label": v.name} for v in base_type]

        # Get description
        description = field_info.description or ""

        # Get default value
        default = None
        if field_info.default is not None and field_info.default != ...:
            default = str(field_info.default)

        return {
            "name": field_name,
            "type": type_name,
            "is_optional": is_optional,
            "is_list": is_list,
            "required": field_info.is_required(),
            "description": description,
            "default": default,
            "enum_values": enum_values,
        }

    def _get_type_name(self, python_type):
        """Convert Python type to a simple string representation"""
        if python_type is str:
            return "string"
        elif python_type is int:
            return "integer"
        elif python_type is float:
            return "float"
        elif python_type is bool:
            return "boolean"
        elif hasattr(python_type, "__name__"):
            # Check if it's an enum
            if hasattr(python_type, "__members__"):
                return "enum"
            # Check if it's a Pydantic model
            if hasattr(python_type, "model_fields"):
                return "object"
            return python_type.__name__
        else:
            return "unknown"

    @http.route("/tvbo/api/schema/enums", type="jsonrpc", auth="user", methods=["GET"])
    def get_enums(self, **kwargs):
        """Get permissible values for every enum in the tvbo datamodel."""
        import enum as _enum

        mod = _get_datamodel()
        if mod is None:
            return {"error": "tvbo datamodel not available"}

        result = {}
        for name in dir(mod):
            obj = getattr(mod, name)
            if isinstance(obj, type) and issubclass(obj, _enum.Enum):
                result[name] = [
                    {"value": v.value, "label": v.name, "doc": getattr(v, "__doc__", "")}
                    for v in obj
                ]
        return result
