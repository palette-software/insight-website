$(function(){
    $('.cmd-btn').click(function(e){
        e.preventDefault();
        var $this = $(this);
        var $loaderArea = $('#loader');
        var targetUrl = $this.attr('href');
        $.ajax({
            url: targetUrl,
        })
        .done(function( data ) {
            console.log(data);
        });
    });
});
