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
            var from = $('#from').val();
            var until = $('#until').val();

            from = from.replace(/ /g, '_');
            until = until.replace(/ /g, '_');

            if (from && until){
                var url = '/filter/between/'+from+'/and/'+until; 
                $.pjax({url: url, container:'#target'});
            }
        }
    };

    conf2 = $.extend(true, {}, config);
    conf2.onSelect = null;
        
    $(document).ready(function(){
        $('#from.datepicker').Zebra_DatePicker(config);
        $('#until.datepicker').Zebra_DatePicker(config);
        $(document).trigger('pjax:end');
    })

    $(document).on('pjax:end', function() {
        $('#search').trigger('change');
        $('#sidebar .datepicker').Zebra_DatePicker(conf2);
    })
        
    
    // Provide "deselecting"/
    $(document).on('click', 'body', function(e){
        if (e.target.nodeName == 'BODY'){ // filter out all delegated events
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

    $('#search').on('change paste keyup', function(e) {
        var search = $(this)
        if (e.keyCode == 27) { // Escape
            search.val('');
            search.blur();
            search_list( $(this).val() );
        }
        else if (e.keyCode == 13) { // Enter
            search.blur();
        } else {
            search_list( $(this).val() );
        }
    });
    
    $('#list_category').on('change', function(e) {
        if ($(this).val()){
            url = '/filter/category/'+$(this).val();
        } else {
            url = '/filter/category/all';
        }
        $.pjax({url: url, container:'#target'});
    });

    $('#list_group').on('change', function(e) {
        url = '/filter/group/'+$(this).val();
        $.pjax({url: url, container:'#target'});
    });


    $('.reset').on('click', function(e) {
        var t = $(this).data('target');
        $(t).val('');
        $(t).trigger('change');

        var url = $(this).data('url');
        if (url){
            $.pjax({url: url, container:'#target'});
        }
    });

    $('.completion').on('change paste keyup', function(e) {
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
