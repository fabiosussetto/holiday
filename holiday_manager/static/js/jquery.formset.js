/**
 * jQuery Formset 1.2
 * @author Stanislaus Madueke (stan DOT madueke AT gmail DOT com)
 * @requires jQuery 1.2.6 or later
 *
 * Copyright (c) 2009, Stanislaus Madueke
 * All rights reserved.
 *
 * Licensed under the New BSD License
 * See: http://www.opensource.org/licenses/bsd-license.php
 */
;(function($) {
    $.fn.formset = function(opts)
    {
        var options = $.extend({}, $.fn.formset.defaults, opts),
            $$ = $(this),

            updateInputIndexes = function(row, form_index) {
                var replace_func = function(index, prev_val) {
                    return prev_val.replace('__prefix__', form_index);
                };
                var to_update = ['for', 'id', 'name'];
                $.each($(':input, label', row), function() {
                    var elem = $(this);
                    $.each(to_update, function(index, attr_name) {
                        if (elem.attr(attr_name)) elem.attr(attr_name, replace_func);
                    });    
                });
            },
            
            addForm = function() {
                var template = (options.formTemplate instanceof $) ? options.formTemplate : $(options.formTemplate);
                var $management_form_total = $('#id_' + options.prefix + '-TOTAL_FORMS')
                var formCount = parseInt($management_form_total.val());
                
                if (!options.beforeAdd(formCount)) {
                    return false;
                }
                
                var row = $(template.html()).clone(true).addClass(options.formCssClass).show();
                
                updateInputIndexes(row, formCount);
                row = options.beforeRender(row, formCount);
                $(options.fieldsetContainer).append(row);
                $management_form_total.val(formCount + 1);
            };

        if ($$.length) {
            $(options.addSelector).click(function(e) {
                e.preventDefault();
                addForm();
            });
        }
        return $$;
    }

    /* Setup plugin defaults */
    $.fn.formset.defaults = {
        deleteSelector: '.delete-formset',
        addSelector: '.add-form',
        fieldsetContainer: '.myform',
        
        prefix: 'form',                  // The form prefix for your django formset
        formTemplate: null,              // The jQuery selection cloned to generate new form instances
        addCssClass: 'add-row',          // CSS class applied to the add link
        deleteCssClass: 'delete-row',    // CSS class applied to the delete link
        formCssClass: 'dynamic-form',    // CSS class applied to each form in a formset
        beforeAdd: function(form_count) { return true; },                     // Function called each time a new form is added
        beforeRender: function(row, form_count) { return row; },                     // Function called each time a new form is added
        afterAdd: function() {},
        removed: null                    // Function called each time a form is deleted
    };
})(jQuery)
