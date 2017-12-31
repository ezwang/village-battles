$(document).ready(function() {
    var countdowns = $(".countdown").filter(function() { return $(this).attr("datetime"); });
    function doCountdowns() {
        var now = new Date();
        countdowns.each(function() {
            var ele = $(this);
            var time = new Date(ele.attr("datetime"));
            if (time < now) {
                window.location.reload();
            }
            var diff = Math.floor((time.getTime() - now.getTime()) / 1000);
            if (diff < 0) {
                return;
            }
            var hours = Math.floor(diff / 3600);
            if (hours < 10) {
                hours = "0" + hours;
            }
            diff %= 3600;
            var mins = Math.floor(diff / 60);
            if (mins < 10) {
                mins = "0" + mins;
            }
            var secs = diff % 60;
            if (secs < 10) {
                secs = "0" + secs;
            }
            $(this).text(hours + ":" + mins + ":" + secs);
        });
    }
    setInterval(doCountdowns, 1000);
    doCountdowns();

    var tickers = $(".ticker").children().filter(function() { return $(this).attr("data-rate"); });
    var lastUpdate = new Date();
    var realValues = {};
    var wood_max = parseInt($(".ticker .wood-cap").text());
    var clay_max = parseInt($(".ticker .clay-cap").text());
    var iron_max = parseInt($(".ticker .iron-cap").text());
    function doTickers() {
        var now = new Date();
        var diff = (now.getTime() - lastUpdate.getTime()) / 1000;
        lastUpdate = now;
        tickers.each(function() {
            var id = $(this).attr("class");
            var value = realValues[id] || parseInt($(this).text());
            var rate = parseInt($(this).attr("data-rate"));
            var added = diff * rate / parseFloat(3600);
            realValues[id] = value + added;
            var value = Math.floor(value + added);
            var type_max;
            if ($(this).hasClass("wood")) {
                type_max = wood_max;
            }
            else if ($(this).hasClass("clay")) {
                type_max = clay_max;
            }
            else {
                type_max = iron_max;
            }
            if (value >= type_max) {
                $(this).css("color", "red");
            }
            else if (value > type_max * 0.8) {
                $(this).css("color", "yellow");
            }
            $(this).text(Math.min(value, type_max));
        });
    }
    setInterval(doTickers, 1000);
    doTickers();

    $(".quest").click(function(e) {
        e.preventDefault();
        $.get("/game/quest/" + encodeURIComponent($(this).attr("data-type")), function(data) {
            $("#quest-modal input[name='id']").val(data.id);
            $("#quest-modal .modal-title").text(data.name + " - Quest");
            var body = $("<p />").text(data.body);
            $("#quest-modal .modal-body").html("").append(body);
            $("#quest-modal .modal-body").append("<div>Reward: <span class='wood'>" + data.reward[0] + "</span><span class='clay'>" + data.reward[1] + "</span><span class='iron'>" + data.reward[2] + "</span></div>");
            $("#claim").prop("disabled", !data.done);
            $("#quest-modal").modal("show");
        });
    });
});
