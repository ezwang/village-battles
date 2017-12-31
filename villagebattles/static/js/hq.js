function get_resources(element) {
    var wood = parseInt(element.find(".wood").text());
    var clay = parseInt(element.find(".clay").text());
    var iron = parseInt(element.find(".iron").text());
    return [wood, clay, iron];
}

$(document).ready(function() {
    function update_buttons() {
        var res = get_resources($("#resources"));
        $("#upgrades tbody tr").each(function() {
            var button = $(this).find("button");
            if (!button.length) {
                return;
            }
            var need = get_resources($(this));
            var unmet = need[0] > res[0] || need[1] > res[1] || need[2] > res[2];
            button.prop("disabled", unmet);
        });
    }
    setInterval(update_buttons, 10000);
    update_buttons();
});
