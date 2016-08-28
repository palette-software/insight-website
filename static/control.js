$(function(){
    var setProgress = function(progressBar, value) {
        progressBar.attr("aria-valuenow", value);
        progressBar.attr("style", "width: " + value + "%;");
    };

    $('.cmd-btn').click(function(e){
        e.preventDefault();
        var $this = $(this);
        var $loaderArea = $('#loader');
        var targetUrl = $this.attr('href');
        var progressCtl = $('#progress');
        progressCtl.removeClass("hidden");
        var progressBar = $('#progressBar');
        var progress = 0;
        setProgress(progressBar, 1);
        var ticker = window.setInterval(function() {
            if (progress < 95) {
                progress += 1;
                setProgress(progressBar, progress);
            }
        }, 400);
        $.ajax({
            url: targetUrl,
        })
        .done(function( data ) {
            setProgress(progressBar, 100);
            window.clearInterval(ticker);
            delayedHide = window.setTimeout(function() {
                progressCtl.addClass("hidden");
                delayedHide = window.clearTimeout();
            }, 1500);
        });
    });
});
