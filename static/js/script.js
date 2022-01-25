function generateGraph(symbol, time) {
    var xml = new XMLHttpRequest();
    xml.onreadystatechange = function() {
        if (xml.status == 200) {
            var timestamp = new Date().getTime();
            var image = document.getElementById('history-graph'); 
            image.src = "../static/history.png?t=" + timestamp;
            document.getElementById("title").innerText = "Previous " + time + " days:"
        }
    }
    xml.open("POST", "/lookup?symbol=" + symbol + "&time=" + time + "d", true);
    xml.send();
}