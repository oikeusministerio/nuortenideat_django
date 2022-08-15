$(function () {

    "use strict";

    var changeDisplayType = function(type) {
        $('.initiative-boxes-wrap').toggleClass('list', type === 'list');
        $('.user-elements').toggleClass('list', type === 'list');
        $('.organization-elements').toggleClass('list', type === 'list');
        $('.title-magenta').toggleClass('list', type === 'list');
        $('.title-blue').toggleClass('list', type === 'list');
        $(document).trigger('display-type-has-changed');
    };
    $(document).on('click', '.idea-display-button', function() {
        $(this).addClass('active');
        $(this).siblings('.idea-display-button').removeClass('active');

        if ($(this).data('display-type')) {
            changeDisplayType($(this).data('display-type'));
        }
    });

    $(document).on('ajaxy-refreshed', function() {
        var display_type = $('.idea-display-button.active[data-display-type]').data('display-type');
        changeDisplayType(display_type);
    });
});