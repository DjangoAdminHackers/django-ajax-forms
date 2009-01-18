(function($) {

    $.fn.validation = function(fields, options) {
        // Setup options
        opts = $.extend({}, $.fn.validation.defaults, options);

        function validate_field(field) {
            var parent = opts.callbacks.get_parent_element(field, opts.format);
            parent.removeClass(opts.style.valid);
            parent.removeClass(opts.style.invalid);

            var field_valid = true;
            var validation = field.data('validation');
            var raw_value = $(field).val();

            if (validation.required && raw_value.length == 0) {
                field_valid = false;
            } else {
                // TODO: Datatype check

                for (type in validation.rules) {
                    rule_func = $.fn.validation.rules[type]
                    if (rule_func) {
                        try {
                            rule_func(validation.rules[type], raw_value, raw_value, validation.msgs);
                        } catch (e) {
                            // Make sure error was thrown by validation.
                            if (e.name && e.name == 'ValidationError') {
                                field_valid = false;
                            }
                        }
                    }
                }
            }

            if (field_valid) {
                parent.addClass(opts.style.valid);
            } else {
                parent.addClass(opts.style.invalid);
            }
            return field_valid;
        }

        function validate_field_onblur() {
            validate_field($(this));
        }

        function validate_form_onsubmit() {
            var first_fail = null;
            var form = $(this);

            $.each(fields, function() {
                var field = form.find(':input[name='+this.name+']');
                if (field) {
                    if (!validate_field(field)) {
                        if (first_fail == null) {
                            first_fail = field;
                        }
                    }
                }
            });

            if (first_fail) {
                first_fail.focus();
                return false;
            }
            return true;
        }

        return $(this).each(function() {
            var form = $(this);

            // Setup fields
            for (name in fields) {
                var field = form.find(':input[name='+name+']');
                if (field) {
                    $(field)
                        .data('validation', fields[name])
                        .blur(validate_field_onblur);
                }
            }

            // Setup form events
            form.submit(validate_form_onsubmit);
        });
    };

    // Default settings
    $.fn.validation.defaults = {
        // Type of form layout to interact with;
        // p | ul | table
        format: 'table',

        // Show errors prior to field
        show_errors_inline: true,

        // Show an error summary (use jQuery selector syntax)
        error_summary: null,

        // Classes applied in various states
        style: {
            valid: 'valid',
            invalid: 'invalid',
            processing: 'processing'
        },

        // Callback methods
        callbacks: {
            get_parent_element: function(field, format) {
                switch(format) {
                    case 'table':
                        return field.parent().parent();
                    default:
                        return field.parent();
                }
            }
        }
    };

    // Custom error object
    $.fn.validation.ValidationError = function(msg, params) {
        params = params || [];
        for(idx in params) {
            msg = msg.replace(idx, params[idx]);
        }
        var err = new Error(msg);
        err.name = "ValidationError";
        return err;
    }
    var ValidationError = $.fn.validation.ValidationError;

    /* Validation methods, additional functions can be added to preform
     * custom validation eg:
     * $.fn.validation.rules['foo'] = function(arg, value, raw_value, msgs) {
     *     if (validation fail) {
     *         throw new ValidationError(msgs['msg_code']);
     *     }
     * };
     */
    $.fn.validation.rules = {

        'min_length': function(arg, value, raw_value, msgs) {
            if (raw_value.length < arg) {
                throw new ValidationError(msgs['min_length'], {
                    '%(min)d': arg,
                    '%(length)d': raw_value.length
                });
            }
        },

        'max_length': function(arg, value, raw_value, msgs) {
            if (raw_value.length > arg) {
                throw new ValidationError(msgs['max_length'], {
                    '%(max)d': arg,
                    '%(length)d': raw_value.length
                });
            }
        },

        'min_value': function(arg, value, raw_value, msgs) {
            if (value < arg) {
                throw new ValidationError(msgs['min_value'], {
                    '%s': arg
                });
            }
        },

        'max_value': function(arg, value, raw_value, msgs) {
            if (value > arg) {
                throw new ValidationError(msgs['max_value'], {
                    '%s': arg
                });
            }
        },

        'regex': function(arg, value, raw_value, msgs) {
        },

        'equal_to_field': function(arg, value, raw_value, msgs) {
            /* HACK: Assumes only one field in this document has passed in name */
            var other = $(':input[name='+arg+']').val();
            if (other != value) {
                throw new ValidationError(msgs['equal_to_field']);
            }
        }

    };

})(jQuery);
