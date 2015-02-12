$(function() {
    $(document).pjax('a', '#target', {scrollTo: false});

    // Configure date picker for selection
    config = {
        days: ['Sonntag', 'Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag'],
        months: ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'],
        show_select_today: false,
        show_clear_date: false,
        show_icon: false,
        direction: true,
        default_position: 'below',
        format: 'j. M Y',
        
        onSelect: function(){
            $(this).trigger('change');
        }
    };
        
    $(document).ready(function(){
        $(document).trigger('pjax:end');
        $('header .datepicker').Zebra_DatePicker(config);
    })

    // Document-Ready with pjax
    $(document).on('pjax:end', function() {
        // Activate datepickers in reloaded area
        $('#target .datepicker').Zebra_DatePicker(config);

        // Distribute stickers
        $('.sticker').each( function() {
            $(this).css({'top': Math.random()*300+150+'px',
                         'right': Math.random()*300+20+'px',
                         'transform': 'rotate('+Math.random()*360+'deg)' });
        });

        $('#search').trigger('change');

        // Distribute flashed messages
        $('#flashs .flash').each( function(){
            var sel = $(this).data('selector');
            if (sel != 'message'){
                $(sel).after($(this));
            }
        });
    })
        
    
    // Provide deselecting
    $(document).on('click', 'body', function(e){
        if (e.target.nodeName == 'BODY'){  // test for un-bubbled events
            $.pjax({url: '/', container:'#target'});
        }
    }); 

    
    search_list = function(query) {
        fuzzy = function(needle, hay){
            return hay.toLowerCase().search(needle.toLowerCase()) > -1
        }
        $('.items li a').each(function(){
            self = $(this);
            hit = query == '' || fuzzy(query, self.attr('title')) || fuzzy(query, self.text());
            if (hit){
                self.removeClass('hidden');
            } else {
                self.addClass('hidden');
            }
        });
    }

    // Search field
    $('#search').on('change paste keyup', function(e) {
        var search = $(this)
        if (e.keyCode == 27) { // Escape
            search.val('');
            search.blur();
            search_list( '' );
        }
        else if (e.keyCode == 13) { // Enter
            search.blur();
        } else {
            search_list( search.val() );
        }
    });
    

    $('#list_group').on('change', function(e) {
        url = '/filter/group/'+$(this).val();
        $.pjax({url: url, container:'#target'});
    });


    $('.reset').on('click', function(e) {
        var t = $( $(this).data('target') );
        t.val('');
        t.filter('select').each( function() {
            var val = $(this).children().first().val();
            $(this).val( val );
        });
        t.trigger('change');

        var url = $(this).data('url');
        if (url){
            $.pjax({url: url, container:'#target'});
        }
    });

    
    //
    // Delegated Event Handlers
    //


    // Autosend
    //

    $('body').on('change', '.autosend input, .autosend select, .autosend textarea', function(){
        var as = $(this).parents('.autosend');
        var url = as.data('target');
        var complete = true;
        var sync = as.data('sync');
        as.find('input,select,textarea').each( function() {
            var name = $(this).attr('name');
            if (name == undefined){ return }
            var val = $(this).val();
            if (val == ''){
                complete = false;
                return
            }
            url = url.replace('['+name+']', val.replace(/ /g, '_'));
            
            // Feature: Sync fields with identical name
            if (sync){
                $('[name="'+name+'"]').val(val);
            }
        });

        if (complete){
            $.pjax({url: url, container:'#target'});
        }
    });


    // Autocompletion
    //

    $('body').on('keyup', '.completion', function(e) {
        var items = $(this).data('items').split(' ');
        var current_input = $(this).val().match(/[^, ]*$/)[0];
        if (current_input == '' || e.keyCode == 8){ return; }

        var l = current_input.length
        var completion = '';
        for (var i=0; i<items.length; i++){
            if (current_input == items[i].substring(0,l)){
                completion = items[i].substring(l, 99)+', ';
                break;
            }
        }
        $(this).val($(this).val()+completion);
        this.setSelectionRange($(this).val().length-completion.length,99);
    });

})
