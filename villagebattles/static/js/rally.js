$(document).ready(function() {
    if (window.location.hash) {
        var coords = window.location.hash.substring(1).split("-");
        $("#x").val(coords[0]);
        $("#y").val(coords[1]);
    }
    $("#x, #y").blur(function() {
        var x = $("#x").val();
        var y = $("#y").val();
        if (x && y) {
            $.get(COORD_ENDPOINT + "?x=" + encodeURIComponent(x) + "&y=" + encodeURIComponent(y), function(data) {
                if (!data.exists) {
                    $("#info").css("color", "red").text("Nonexistent Village!");
                }
                else {
                    var owned;
                    if (data.owner) {
                        owned = " (owned by " + data.owner + ")";
                    }
                    else {
                        owned = " (Abandoned)";
                    }
                    $("#info").css("color", "black").text(" - " + data.name + owned);
                }
            });
        }
        else {
            $("#info").css("color", "red").text("Invalid Coordinates!");
        }
    });
    if ($("#x").val().length) {
        $("#x").blur();
    }
    $("#select_none").click(function(e) {
        e.preventDefault();
        $("#recruit input[type=number]").each(function() {
            $(this).val(0);
        });
    });
    $("#select_all").click(function(e) {
        e.preventDefault();
        var troops = {};
        $("#troops tbody tr").each(function() {
            var info = $(this).find("td").map(function() { return $(this).text(); });
            troops[info[0]] = info[1];
        });
        $("#recruit tbody tr").each(function() {
            var troop = $(this).find("td:first-child").text();
            var input = $(this).find("input[type=number]");
            input.val(troops[troop]);
        });
    });
});
