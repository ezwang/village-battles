var size = 50;
var village_info = {};

function addVillage(x, y, id) {
    $("#world").append($("<div class='village' />").attr("data-id", id).css("left", (x*size) + "px").css("top", (y*size) + "px"));
}

function loadVillages() {
    $.get(MAP_ENDPOINT, function(data) {
        data.villages.forEach(function(v) {
            addVillage(v.x, v.y, v.id);
            village_info[v.id] = v;
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

    loadVillages();

    $("#world").on("click", ".village", function() {
        var id = $(this).attr("data-id");
        var vil = village_info[id];
        $("#info").html("<a href='village/" + id + "'>" + $("<div />").text(vil.name).html() + " (" + vil.x + "|" + vil.y + ")</a> owned by <a href='user/" + vil.owner.id + "'>" + $("<div />").text(vil.owner.name).html() + "</a>");
        $("#world .village").removeClass("selected");
        $(this).addClass("selected");
    });
});
