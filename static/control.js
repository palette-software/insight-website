$( document ).ready(function() {
    var setProgress = function(progressBar, value) {
        progressBar.attr("aria-valuenow", value);
        progressBar.attr("style", "width: " + value + "%;");
    };

    var getProgress = window.setInterval(function() {
        $.ajax({
            url: "/control/update/progress"
        })
        .done(function( data ) {
            statusContent = $('#status');
            if (data != undefined && data.line != "") {
                statusContent.html(data.line);
            } else {
                statusContent.html("");
            }
        });
    }, 1000);

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
            statusContent.html("");

            delayedHide = window.setTimeout(function() {
                progressCtl.addClass("hidden");
                delayedHide = window.clearTimeout();
            }, 1500);
        });
    });
});
