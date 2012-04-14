var Class = function() {
    var klass = function() {
        this.init.apply(this, arguments);
    };
    klass.prototype.init = function(){};

    // Shortcut to access prototype
    klass.fn = klass.prototype;
    // Shortcut to access class
    klass.fn.parent = klass;

    // Adding class properties
    klass.extend = function(obj) {
        var extended = obj.extended;
        for (var i in obj) {
            klass[i] = obj[i];
        }
        if (extended) extended(klass);
    };

    // Adding instance properties
    klass.include = function(obj) {
        var included = obj.included;
        for (var i in obj) {
            klass.fn[i] = obj[i];
        }
        if (included) included(klass);
    };

    klass.proxy = function(func) {
        var self = this;
        return (function() {
            return func.apply(self, arguments);
        });
    };
    klass.fn.proxy = klass.proxy;

    return klass;
};

var Site = new Class;
Site.include({
    cur_date: "",
    init: function(dte) {
        this.cur_date = dte;
    },
    date_params: function() {
        var m = this.cur_date.getMonth() + 1;
        if (m < 10)
            m = "0" + m;
        var d = this.cur_date.getDate();
        if (d < 10)
            d = "0" + d;
        var url = "month=" + m;
        url += "&day=" + d;
        url += "&year=" + this.cur_date.getFullYear();
        return url;
    },
    game_url: function() {
        return "getgames?" + this.date_params();
    },
    scorecard_url: function() {
        return "scorecard?" + this.date_params() + "&gameID=" + $("#gameID").val();
    },
    change_date: function(dte) {
        this.cur_date = dte;
        this.show_date();
        this.get_games();
    },
    show_date: function() {
        /* Set the displayed date text. */
        var dateStr = "";
        switch (this.cur_date.getDay()) {
        case 0: dateStr += "Sunday, "; break;
        case 1: dateStr += "Monday, "; break;
        case 2: dateStr += "Tuesday, "; break;
        case 3: dateStr += "Wednesday, "; break;
        case 4: dateStr += "Thursday, "; break;
        case 5: dateStr += "Friday, "; break;
        case 6: dateStr += "Saturday, "; break;
        }
        switch (this.cur_date.getMonth()) {
        case  0: dateStr += "January "; break;
        case  1: dateStr += "February "; break;
        case  2: dateStr += "March "; break;
        case  3: dateStr += "April "; break;
        case  4: dateStr += "May "; break;
        case  5: dateStr += "June "; break;
        case  6: dateStr += "July "; break;
        case  7: dateStr += "August "; break;
        case  8: dateStr += "September "; break;
        case  9: dateStr += "October "; break;
        case 10: dateStr += "November "; break;
        case 11: dateStr += "December "; break;
        }
        dateStr += this.cur_date.getDate() + ", " + this.cur_date.getFullYear();
        $("span#dte").text(dateStr);
    },
    get_games: function() {
        // Clear the game drop-down
        $("#gameID").find("option").remove();

        // Request the list of games for the new date
        var url = this.game_url();

        var req = new XMLHttpRequest();
        req.open("GET",url,false);
        req.send("");
        games = req.responseText;

        gameList = eval("(" + games + ")");
        for (i = 0; i < gameList.length; i++) {
            $("#gameID").append($('<option>').attr('value', gameList[i].url).text(gameList[i].away + " @ " + gameList[i].home));
        }
    },
    update_scorecard: function(event) {
        event.preventDefault();
        var url = this.scorecard_url();
        $("#scorecard").html('<embed class="scorecard" src="' + url + '" />');
    },
    start: function() {
	    $("#datepicker").datepicker({
	        onSelect: this.proxy(function(dateText, inst) {
	            this.change_date(new Date(dateText));
            })
	    });
	    $("#dte").click(this.proxy(function(){
	        $("#datepicker").datepicker('show');
	    }));
	    $("#view_scorecard").click(this.proxy(function(event) {
            this.update_scorecard(event);
        }));

        this.show_date();
    }
});
