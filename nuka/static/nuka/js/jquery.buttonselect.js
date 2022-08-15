/*global jQuery*/

(function ($) {

    "use strict";

    $.fn.buttonSelect = function (opts) {

        var defaults = {
            wrapTag: '<div class="form-control btn-group-input" />',
            groupTag: '<div class="btn-group" data-toggle="buttons" />',
            buttonTag: '<button type="button" class="btn btn-default" />',
            labelTag: '<label>',
            checkboxInputTag: '<input type="checkbox" tabindex="-1">',
            radioInputTag: '<input type="radio" tabindex="-1">',
            activeClass: 'active',
            multiple: null,
            changeEvent: null
        };

        opts = $.extend({}, defaults, opts);

        return this.each(function () {
            var select = $(this),
                multiple = opts.multiple !== null ? opts.multiple : select.prop('multiple'),
                btnGroup = $(opts.groupTag),
                wrap = $(opts.wrapTag),
                sthSelected = $(this).find(':selected').length > 0;

            select.find('option').each(function () {
                var opt = $(this),
                    btn = $(opts.buttonTag),
                    input, label;

                input = $(multiple ? opts.checkboxInputTag : opts.radioInputTag);

                label = $(opts.labelTag);
                label.text(opt.text());
                label.prepend(input);
                btn.append(label);

                if($(this).prop('selected') || (!sthSelected && $(this).val() === '')) {
                    btn.addClass(opts.activeClass);
                }

                input.on('change', function () {
                    console.log('fire');
                    var selected = $(this).prop('checked');
                    if(multiple) {
                        opt.prop('selected', selected);
                    } else {
                        select.val(opt.val());
                    }
                    if (opts.changeEvent !== null) {
                        select.triggerHandler(opts.changeEvent);
                    }
                });

                btnGroup.append(btn);
            });

            select.before(wrap.append(btnGroup)).hide();

        });

    };

}(jQuery));
