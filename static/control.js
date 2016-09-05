$( document ).ready(function() {
    var setProgress = function(progressBar, value) {
        progressBar.attr("aria-valuenow", value);
        progressBar.attr("style", "width: " + value + "%;");
    };

    var statusContent = $('#status');
    var statusPanel = $('#statusPanel');
    var progressCtl = $('#progress');

    var completed = function() {
        var delayedHide = window.setTimeout(function() {
            progressCtl.addClass("hidden");
            delayedHide = window.clearTimeout();
        }, 1500);
    };

    var getProgress = window.setInterval(function() {
        $.ajax({
            url: "/control/update/progress"
        })
        .done(function( data ) {
            if (data == undefined) {
                return;
            }

            data = JSON.parse(data);
            if (data != undefined && data.length != null && data.length > 0) {
                var content = "";
                var progress = 0;
                for (var i = 0; i < data.length; i++) {
                    content += data[i].line + "\n";
                    progress = data[i].progress;
                }
                var progressBar = $('#progressBar');
                setProgress(progressBar, progress);
                if (progress == 100) {
                    completed();
                }
                statusContent.html(content);
                statusPanel.removeClass("hidden");
            } else {
                    completed();
                    statusContent.html("");
                    statusPanel.addClass("hidden");
            }
        });
    }, 1000);

    $('.cmd-btn').click(function(e){
        e.preventDefault();
        var $this = $(this);
        var targetUrl = $this.attr('href');

        if ($this.attr("id") == 'update') {
            progressCtl.removeClass("hidden");
            var progressBar = $('#progressBar');
            var progress = 0;
            setProgress(progressBar, 1);
        }

        $.ajax({
            url: targetUrl,
        })
        .done(function( data ) {
        });
    });
});
