$(document).ready(function() {
    $(".max").click(function(e) {
        e.preventDefault();
        var res = get_resources($("#resources"));
        var need = get_resources($(this).closest("tr"));
        var amt = Math.floor(Math.min(res[0] / need[0], res[1] / need[1], res[2] / need[2]));
        $(this).closest("tr").find("input").val(amt);
    });
});
