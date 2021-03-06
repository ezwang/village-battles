var size = 50;
var selected = -1;
var village_info = {};

function addVillage(x, y, id) {
    var vil = $("<div class='village' />").attr("data-id", id).css("left", (x*size) + "px").css("top", (y*size) + "px");
    $("#world").append(vil);
    return vil;
}

function loadVillages() {
    $.get(MAP_ENDPOINT, function(data) {
        data.villages.forEach(function(v) {
            var vil = addVillage(v.x, v.y, v.id);
            village_info[v.id] = v;
            if (v.x == coords[0] && v.y == coords[1]) {
                vil.click();
            }
            if (!v.owner) {
                vil.addClass("abandoned");
            }
            else if (v.owner && v.owner.id == userid) {
                vil.addClass("owned");
            }
            else if (v.owner.tribe && v.owner.tribe == tribeid) {
                vil.addClass("tribe");
            }
        });
    });
}

$(document).ready(function() {

    if (window.location.hash) {
        var temp = window.location.hash.substring(1).split("-");
        coords[0] = parseInt(temp[0]);
        coords[1] = parseInt(temp[1]);
    }

    $("#x").val(coords[0]);
    $("#y").val(coords[1]);
    $("#map").scrollLeft(coords[0] * size - ($("#map").width() - size) / 2).scrollTop(coords[1] * size - ($("#map").height() - size) / 2);
    $("#map").scroll(function() {
        var x = $(this).scrollLeft();
        var y = $(this).scrollTop();
        var realX = Math.round((x + ($("#map").width() - size) / 2) / size);
        var realY = Math.round((y + ($("#map").height() - size) / 2) / size);
        $("#x").val(realX);
        $("#y").val(realY);
    });

    $("#world").on("click", ".village", function() {
        selected = $(this).attr("data-id");
        var vil = village_info[selected];
        var owner_text;
        if (vil.owner) {
            owner_text = " owned by <a href='user/" + vil.owner.id + "'>" + $("<div />").text(vil.owner.name).html() + "</a>";
        }
        else {
            owner_text = " (Abandoned Village)";
        }
        $("#info").html("<a class='village' href='village/" + selected + "'>" + $("<div />").text(vil.name).html() + " (" + vil.x + "|" + vil.y + ")</a>" + owner_text);
        $("#world .village").removeClass("selected");
        $(this).addClass("selected");
    });

    $("#attack").click(function(e) {
        e.preventDefault();
        if (selected >= 0) {
            window.location.href = RALLY_ENDPOINT + "#" + village_info[selected].x + "-" + village_info[selected].y;
        }
    });

    $("#x, #y").keypress(function(e) {
        if (e.keyCode == 13) {
            e.preventDefault();
            var x = parseInt($("#x").val());
            var y = parseInt($("#y").val());
            if (x && y) {
                $("#map").scrollLeft(x * size - ($("#map").width() - size) / 2).scrollTop(y * size - ($("#map").height() - size) / 2);
            }
            history.replaceState(undefined, undefined, "#" + realX + "-" + realY);
        }
    });

    loadVillages();
});
