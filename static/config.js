$(function(){
    var currentHost = "";
    var addHost = function(hostname) {
        $('#hostnames ul').append('<li><a href="#">' + hostname + '</a></li>');
    };

    var getHosts = function() {
        $.ajax({
            url: "http://localhost:9000/api/v1/agents"
        })
        .done(function( data ) {
            var agentList = JSON.parse(data);
            for (hostname in agentList) {
                addHost(hostname);
            }

            $(".dropdown-menu li a").click(function(){
                currentHost = $(this).text();
                $('#hostnames').find('.dropdown-toggle').html(currentHost + ' <span class="caret"></span>');
                loadConfig(currentHost);
            });
        })
    }

    var loadConfig = function(hostname) {
        $.ajax({
            url: 'http://localhost:9000/api/v1/config?hostname=' + hostname,
        })
        .done(function( data ) {
            editor.session.setValue(data);
        })
    }

    window.saveConfig = function() {
        hostname = currentHost;
        var content = editor.session.getValue();
        var formData = new FormData();
        var blob = new Blob([content], { type: "text/xml"});
        formData.append("uploadfile", blob);

        $.ajax({
            url: 'http://localhost:9000/api/v1/config?hostname=' + hostname,
            data: formData,
            processData: false,
            contentType: false,
            type: 'PUT',
        })
        .done(function( data ) {
            var getConfigCommand = {
                command: "GET-CONFIG"
            }
            $.ajax({
                url: 'http://localhost:9000/api/v1/command',
                data: getConfigCommand,
                type: 'PUT',
            });
        });
    }

    var editor = ace.edit("editor");
    editor.setTheme("ace/theme/clouds");
    editor.session.setMode("ace/mode/yaml");
    editor.$blockScrolling = Infinity;
    getHosts();
});


