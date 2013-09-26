$(function() {
    $(document).pjax('a', '#target');

    $(document).ready(function(){
            config = {
                        days: ['Sonntag', 'Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag'],
                        months: ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'],
                        show_select_today: false,
                        show_clear_date: false,
                        show_icon: false,
                        direction: true,
                        format: 'j. M Y'
                     };
        
            $('#from.datepicker').Zebra_DatePicker(config);
            $('#until.datepicker').Zebra_DatePicker(config);
    }) // document.ready
    
    // Provide "deselecting"/
    $(document).on('click', 'body', function(){
        $('#sidebar').empty();
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

    $('#search').bind('change paste keyup', function() {
        filter_list( $(this).val() ); 
    });

})

/*
(function( app, $, undefined ) {

    dispatch = function( resource ){
        console.log('dispatching '+resource+'.');
        $.getJSON($ROOT + resource, {json: true}, function(response){
            html = $(response.html);
            history.pushState(response.resource, 'Stock', response.resource);
            html.each( function(index, chunk){
                chunk = $(chunk);
                target = chunk.attr('id');
                if (chunk.is('div') && target){ 
                    console.log('dispatch target: '+target);
                    $('#'+target).replaceWith(chunk);
                }
            });
        });
    }

    // bind post link handler (leaving of page)
    //$(document).on('click', 'a[target="post"]', function(){

    app.post = function(ev){
        console.log('post');
        data = $('input, textarea').serialize()
        $('.post').each( function(){
            data += $(this).attr('name')+'='+$(this).html()+'&'
        });
        $.post($ROOT+window.location.pathname, data, function(){
            going_to = $(document).data('get');
            alert('aye!'+going_to);
        });
        ev.preventDefault();
    }

    // bind ajax link handler
    //$(document).on('click', 'a[target="ajax"]', function(){

    app.get = function(ev){
        console.log('get');
        dispatch( $(this).attr('href') );
        ev.preventDefault();
    }

    app.sync_post_get = function(ev){
        console.log('sync post get');
        data = $('input, textarea').serialize()
        $(document).data('get', $(this).attr('href') );
        $('.post').each( function(){
            data += $(this).attr('name')+'='+$(this).html()+'&'
        });
        $.post($ROOT+window.location.pathname, data, function(){
            dispatch( $(document).data('get') );
        });
        ev.preventDefault();
    }

    $(document).on('click', 'a[target="post"]', app.post ); 
    $(document).on('click', 'a[target="get"]', app.get ); 
    $(document).on('click', 'a[target="get post"]', app.sync_post_get ); 


    // bind browser-back event
    $(window).bind('popstate', function(event){
        if (event.originalEvent.state){
            dispatch( event.originalEvent.state );
        }
    });

    // dispatch current location url after load
    dispatch( window.location.pathname );

    app.ready = function(){
    }

}( window.app = window.app || {}, jQuery ));
*/
