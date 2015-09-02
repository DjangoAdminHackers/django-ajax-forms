# Copyright 2009 Tim Savage <tim.savage@poweredbypenguins.org>
# Licensed under the terms of the BSD License (see LICENSE)
import re
from decimal import Decimal
from django import forms
from django.core import validators
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext as _

__all__ = (
    'AlreadyRegistered', 'register', 'factory',
    'AjaxField', 'AjaxDateField', 'AjaxDateTimeField', 
    'AjaxDecimalField', 'AjaxEmailField', 'AjaxFloatField', 
    'AjaxIntegerField', 'AjaxNumericField', 'AjaxTimeField'
)

class AlreadyRegistered(Exception):
    """
    An attempt was made to register a form field more than once
    """
    pass


# Registration and creation of fields

registry = {}

def register(field, ajax_field):
    """
    Register an ajax_field for a field
    """
    if field in registry:
        raise AlreadyRegistered(
            _('The form field %s has already been registered.') % field.__name__)
    registry[field] = ajax_field

def factory(field_instance):
    """
    Get an ajax_field instance for a field instance
    """
    ajax_field = registry.get(type(field_instance), AjaxField)
    return ajax_field(field_instance)


# Built in fields

# These fields require nothing specialised they will be assigned AjaxField by
# default in the factory method:
#   CharField, EmailField, IPAddressField, RegexField, URLField BooleanField, NullBooleanField, 
#   ChoiceField, MultipleChoiceField, TypedChoiceField
#
# File fields have limited capability for validation on the client side and
# will be treated the same as the above fields, these include:
#   FileField, FilePathField, ImageField

class AjaxField(object):
    """
    Base Ajax Field that handles most fields. 
    """
    __slots__ = ('field', '_rules', '_error_messages', )

    def __init__(self, field_instance):
        self.field = field_instance
        self._rules = None
        self._error_messages = {}

    def add_error_message(self, msg_key):
        """
        Add an error message to be sent to client
        """
        self._error_messages[msg_key] = self.field.error_messages.get(msg_key)

    def add_rule(self, rule_name, value=None, msg_key=None, cast=None):
        """
        Add a validation rule
        """
        if msg_key is None:
            msg_key = rule_name
        if value is None:
            value = getattr(self.field, rule_name, None)
        if value:
            self.add_error_message(msg_key)
            if cast:
                self._rules[rule_name] = cast(value)
            else:
                self._rules[rule_name] = value

    def parse(self):
        """
        Hook for doing any extra parsing in sub class
        """
        # Parse validator array
        for validator in self.field.validators:
            if isinstance(validator, validators.BaseValidator):
                value = validator.limit_value
                if isinstance(value, Decimal):
                    value = str(value)
                self.add_rule(validator.code, value)
            elif isinstance(validator, validators.RegexValidator):
                # Handle regex flags
                flags = []
                if validator.regex.flags & re.IGNORECASE:
                    flags.append('i')
                if validator.regex.flags & re.MULTILINE:
                    flags.append('m')
                self.add_rule('regex', (validator.regex.pattern, ''.join(flags)), 'invalid')        

    def to_ajax(self):
        """
        Convert field rules into a JSON serializable dictionary
        """
        if self._rules is None:
            self._rules = SortedDict()
            if self.field.required:
                self.add_error_message('required')
            self.parse()
        return {
            'msgs': self._error_messages,
            'required': self.field.required,
            'rules': self._rules,
        }
        
        
class AjaxFloatField(AjaxField):
    """
    Ajax Field for handling `forms.FloatField` fields.
    """
    def parse(self):
        self.add_rule('is_float', True, 'invalid')
        super(AjaxFloatField, self).parse()

register(forms.FloatField, AjaxFloatField)


class AjaxDecimalField(AjaxField):
    """
    Ajax Field for handling `forms.DecimalField` fields.
    """
    def parse(self):
        self.add_rule('is_float', True, 'invalid')
        super(AjaxDecimalField, self).parse()

        self.add_rule('max_value', cast=str)
        self.add_rule('min_value', cast=str)

        max_digits = getattr(self.field, 'max_digits', None),
        decimal_places = getattr(self.field, 'decimal_places', None)
        if not (max_digits is None or decimal_places is None):
            self._rules['decimal_length'] = (max_digits, decimal_places)

        if max_digits:
            self.add_error_message('max_digits')
        if decimal_places:
            self.add_error_message('max_decimal_places')
        if max_digits and decimal_places:
            self.add_error_message('max_whole_digits')

register(forms.DecimalField, AjaxDecimalField)


class AjaxIntegerField(AjaxField):
    """
    Ajax Field for handling `forms.IntegerField` fields.
    """
    def parse(self):
        self.add_rule('is_integer', True, 'invalid')
        super(AjaxIntegerField, self).parse()

        self.add_rule('max_value', cast=str)
        self.add_rule('min_value', cast=str)

register(forms.IntegerField, AjaxIntegerField)


class AjaxDateField(AjaxField):
    """
    Ajax Field for handling `forms.DateField` fields.
    """
    def parse(self):
        super(AjaxDateField, self).parse()
        self.add_rule('is_date', True, 'invalid')

register(forms.DateField, AjaxDateField)


class AjaxDateTimeField(AjaxField):
    """
    Ajax Field for handling `forms.DateTimeField` fields.
    """
    def parse(self):
        super(AjaxDateTimeField, self).parse()
        self.add_rule('is_datetime', True, 'invalid')

register(forms.DateTimeField, AjaxDateTimeField)


class AjaxTimeField(AjaxField):
    """
    Ajax Field for handling `forms.TimeField` fields.
    """
    def parse(self):
        super(AjaxTimeField, self).parse()
        self.add_rule('is_time', True, 'invalid')

register(forms.TimeField, AjaxTimeField)
