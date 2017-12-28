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
});
