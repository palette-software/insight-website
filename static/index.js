$(function(){
    var $loaderArea = $('#loader');
    var $targetPre = $('#cmd-results-pre');
    var $targetArea = $('#cmd-results-pre');
    $loaderArea.hide();
    $targetPre.hide();
    
    $.ajax({
        url: "/status",
    })
    .done(function( data ) {
        $targetArea.text( $targetArea.text() + data );
        $targetPre.show('fast');
        // hide the loader
        $loaderArea.hide();
    });
    //
    // replace the result with the remote one
    // $targetArea.load(targetUrl, function(){
    // });
});


