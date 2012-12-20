/*
 * Shortens URL to the given size, attempting to provide the most useful part, e.g.:
 * "http://google.com/asdf/f/d/as/df/a/f/your_profile.html" -> "your_profile.html"
 */
var shortenURL = function(url, size) {

    if (url.length < size) {
        return url
    } else if (/^data:.*/.test(url)) {
        return url.substr(url, size - 3) + "..."
    } else {
        var parts = url.split("/")
        var shortened = ""

        for (i = parts.length - 1; i >= 0; i--) {
            if (parts[i].length + "/".length + shortened.length > size - 3) {
                if (shortened.length == 0) {
                    shortened = "/" + parts[i].substr(0, size - 7) + "..."
                } else {
                    break
                }
            } else {
                shortened = "/" + parts[i] + shortened
            }
        }
        if (shortened.length > size) {
            alert("incorrectly shortened url: " + url)
        }
        return "..." + shortened
    }
}

/*
 * Converts # of bytes to a human-readable equivalent, e.g.:
 * 4096 -> "4KB"
 */
var formatAsSizeStr = function(bytes) {
    var sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    if (bytes == 0) {
        return '0B'
    } else {
        var i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)))
        return (bytes / Math.pow(1024, i)).toFixed(1) + sizes[i]
    }
}

/*
 * Creates a string of the specified length. Use case example: figure out how much space is required for a field with
 * a certain maximum length.
 */
var stringOfLength = function(n) {
    if (n == 0) {
        return ""
    } else {
        return "a" + stringOfLength(n - 1)
    }
}

String.prototype.width = function(font) {
    var f = font || '10px arial',
        o = $('<div>' + this + '</div>')
            .css({'position': 'absolute', 'float': 'left', 'white-space': 'nowrap', 'visibility': 'hidden', 'font': f})
            .appendTo($('body')),
        w = o.width();

    o.remove();

    return w;
}

/*
 * Creates a canvas DOM element with the appropriate size, given the specified number of entries
 */
function makeWaterfallCanvas(numEntries) {
    return $("<canvas/>").attr("width", Math.max(500, $(window).width() - 30)).attr("height", 27 * numEntries).attr("id", "waterfall-canvas")[0]
}