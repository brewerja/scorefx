function setStartDate(m, d, y) {
    $("#month").val(m);        
    $("#day").val(d);
    $("#year").val(y);
}

function dateChange(form) {
    // Clear the game drop-down
    $("#gameID").find("option").remove();

    // Request the list of games for the new date
    var url = "getgames?";
    url += "month=" + $("#month").val();
    url += "&day=" + $("#day").val();
    url += "&year=" + $("#year").val();

    var req = new XMLHttpRequest();
    req.open("GET",url,false);
    req.send("");
    games = req.responseText;

    gameList = eval("(" + games + ")");
    for (i = 0; i < gameList.length; i++) {
        $("#gameID").append($('<option>').attr('value', gameList[i].url).text(gameList[i].away + " @ " + gameList[i].home));
    }

}

function updateScorecard(event) {
    event.preventDefault();
    var url = "scorecard?";
    url += "month=" + $("#month").val();
    url += "&day=" + $("#day").val();
    url += "&year=" + $("#year").val();
    url += "&gameID=" + $("#gameID").val();
    $("#scorecard").html('<embed class="scorecard" src="' + url + '" />');
}
