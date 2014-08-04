$(function() {
    $(document).pjax('a', '#target');

    $(document).ready(function(){
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
                    var url = '/available/between/'+from+'/and/'+until; 
                    $.pjax({url: url, container:'#target'});
                }
            }
        };
        
        $('#from.datepicker').Zebra_DatePicker(config);
        $('#until.datepicker').Zebra_DatePicker(config);

        
        // Configure date picker for availability
        config.always_visible = $('#calendar_');
        config.onSelect = null;
        config.disabled_dates = ['* * * 3,6'];

        $('#calendar.datepicker').Zebra_DatePicker(config);
        

    }) // document.ready
    
    // Provide "deselecting"/
    $(document).on('click', 'body', function(e){
        if (e.target.nodeName == 'BODY'){ // filter out all delegated events
            $.pjax({url: '/', container:'#target'});
        }
    }); 

    
    filter_list = function(query) {
        fuzzy = function(needle, hay){
            return hay.toLowerCase().search(needle.toLowerCase()) > 0
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
            filter_list( $(this).val() );
        }
        else if (e.keyCode == 13) { // Enter
            search.blur();
        } else {
            filter_list( $(this).val() );
        }
    });
    
    $('#list_category').on('change', function(e) {
        if ($(this).val()){
            url = '/list/'+$(this).val();
        } else {
            url = '/list';
        }
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

})
