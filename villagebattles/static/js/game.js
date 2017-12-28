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
    var max = parseInt($(".ticker .wood-cap").text());
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
            $(this).text(Math.min(Math.floor(value + added)));
        });
    }
    setInterval(doTickers, 1000);
    doTickers();
});
