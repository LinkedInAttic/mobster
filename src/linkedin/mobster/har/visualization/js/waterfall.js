
var HTTPWaterfallDrawing = Class.extend({
    init: function(canvasId, httpArchive) {
        this.httpArchiveLog = httpArchive.log
        this.resourceBounds = []
        this.canvas = $("#" + canvasId)
        this.stage = new Stage(this.canvas[0])
        this.computeTime()
        this.computeSizes()
        this.initColors()
        this.initResourceInfoTable()
        this.initTimeBarTooltipTable()
        this.initMouseMoveListener()

        for (i in this.httpArchiveLog.entries) {
            this.drawEntry(this.httpArchiveLog.entries[i], i)
        }

        this.drawRectangle(0,0, this.getCanvasWidth(), this.getCanvasHeight(), Graphics.getRGB(0,0,0))
        this.drawPageTimings()

        // Draw to the canvas
        this.stage.update();

        Ticker.setFPS(50)
        Ticker.addListener(this)
        this.update = false
    },

    initMouseMoveListener: function() {
        this.stage.enableMouseOver()
        var waterfallDrawing = this
        this.stage.onMouseMove = function(e) {
          var targetedEntry = waterfallDrawing.getMouseEntryTarget()
          if (e.stageX < waterfallDrawing.urlAreaWidth && targetedEntry) {
            if (targetedEntry)  {
              waterfallDrawing.showURLTooltip(targetedEntry, e.stageX, e.stageY)

                if (waterfallDrawing.urlTooltipTimeout) {
                  clearTimeout(waterfallDrawing.urlTooltipTimeout)
                }
                waterfallDrawing.urlTooltipTimeout = setTimeout(function() {
                  waterfallDrawing.fadeOutURLTooltip()
                    }, 4000)
                }
            } else {
                waterfallDrawing.hideURLTooltip()
            }

            if (waterfallDrawing.currentTargetedTimeBar) {
                waterfallDrawing.showTimeBarTooltip(waterfallDrawing.currentTargetedTimeBar, e.stageX, e.stageY)

                if (waterfallDrawing.timeBarTooltipTimeout) {
                    clearTimeout(waterfallDrawing.timeBarTooltipTimeout)
                }
                waterfallDrawing.timeBarTooltipTimeout = setTimeout(function() {
                    waterfallDrawing.fadeOutTimeBarTooltip()
                }, 4000)


            } else {
                waterfallDrawing.hideTimeBarTooltip()
            }
        }
    },

    initResourceInfoTable: function() {
        var tableBody = $("<tbody/>")
        var infoTableRows = ["URL", "Resource Size", "Request Method", "HTTP Response"]

        for (i in infoTableRows) {
            tableBody.append($("<tr/>")
                                .append(($("<td class='key'/>"))
                                    .append(infoTableRows[i]))
                                .append($("<td class='value'/>")))
        }

        $("<table id='resource-info-table'/>").append(tableBody)
                                              .css("position", "absolute")
                                              .css("visibility", "hidden")
                                              .css("opacity", "1.0")
                                              .insertAfter(this.canvas)
    },

    initTimeBarTooltipTable: function() {

        var tableBody = $("<tbody/>")

        for (var color in this.timeColors) {
            tableBody.append($("<tr/>")
                                .append($("<td class='color'/>")
                                    .css("background-color", this.timeColors[color]))
                                .append($("<td class='duration'/>"))
                                .append($("<td class='label'/>")
                                    .append(color)))
        }

        $("<table id='timebar-tooltip-table'/>").append(tableBody)
                                                .css("position", "absolute")
                                                .css("visibility", "hidden")
                                                .css("opacity", "1.0")
                                                .insertAfter(this.canvas)
    },

    getMouseEntryTarget: function() {
        return this.currentTargetedEntry
    },

    computeTime: function() {
        this.startTime = Date.parse(this.httpArchiveLog.entries[0].startedDateTime)
        this.endTime = -1

        for (i in this.httpArchiveLog.entries) {
            var currentEntry = this.httpArchiveLog.entries[i]
            this.endTime = Math.max(this.endTime, Date.parse(currentEntry.startedDateTime) + currentEntry.time)
        }

        this.endTime = Math.max(this.endTime, this.httpArchiveLog.pages[0].pageTimings["onLoad"])

        this.totalTime = this.endTime - this.startTime
    },

    computeSizes: function() {
        this.resourceHeight = (4 * this.getCanvasHeight()) / (5* this.httpArchiveLog.entries.length - 1)
        this.resourceSpacing = this.resourceHeight / 4

        this.urlAreaWidth = 300
        this.rightLabelAreaWidth = 50
    },

    initColors: function() {
        this.timeColors = {}
        // Colors are listed in chronological order of their keys. Order is important.
        this.timeColors["blocked"] = Graphics.getRGB(0xCD5C5C)
        this.timeColors["dns"]     = Graphics.getRGB(0x87CEEB)
        this.timeColors["connect"] = Graphics.getRGB(0x98FB98)
        this.timeColors["send"]    = Graphics.getRGB(0xE9967A)
        this.timeColors["wait"]    = Graphics.getRGB(0x9370DB)
        this.timeColors["receive"] = Graphics.getRGB(0xCDC9C9)
    },

    //
    tick: function() {
        if(this.update) {
            this.update = false;
            this.stage.update();
        }
    },


    // Converts the given number of millis to a number of pixels, where pixels/totalPixels = millis/totalTime
    scaleToSize: function(millis, totalPixels) {
        return (millis/this.totalTime) * totalPixels
    },

    getMaxUrlChars: function() {
        return Math.round((this.urlAreaWidth / 300) * 33)
    },

    drawEntry: function(entryObj, index) {
        var container = new Container()

        var yCoord =  index * (this.resourceHeight + this.resourceSpacing)

        var backgroundFill = new Shape()
        backgroundFill.graphics.beginFill(index % 2 == 0 ? Graphics.getRGB(245,245,245): Graphics.getRGB(255,255,255))
        backgroundFill.graphics.drawRect(0, yCoord - this.resourceSpacing / 2, this.getCanvasWidth(), this.resourceHeight + this.resourceSpacing)
        backgroundFill.mouseEnabled = true
        var waterfallDrawing = this
        backgroundFill.onMouseOver = function(e) {
            waterfallDrawing.currentTargetedEntry = entryObj
        }

        backgroundFill.onMouseOut = function(e) {
            waterfallDrawing.currentTargetedEntry = null
        }

        container.addChild(backgroundFill)


        this.resourceBounds.push(yCoord - this.resourceSpacing / 2)
        this.resourceBounds.push(yCoord + this.resourceHeight + this.resourceSpacing / 2)

        var shortenedURL = shortenURL(entryObj.request.url, this.getMaxUrlChars())
        var urlLabel = new Text(shortenedURL, "12px Courier", "#000")
        urlLabel.textAlign = "left"
        urlLabel.textBaseline = "middle"
        urlLabel.x = 0
        urlLabel.y = yCoord + (this.resourceHeight / 2)
        urlLabel.mouseEnabled = true
        container.addChild(urlLabel)




        var sizeLabel = new Text(formatAsSizeStr(entryObj.response.bodySize), "12px Courier", "#000")
        sizeLabel.textAlign = "left"
        sizeLabel.textBaseline = "middle"
        sizeLabel.x = stringOfLength(this.getMaxUrlChars()).width("12px Courier") + 10
        sizeLabel.y = yCoord + (this.resourceHeight / 2)
        container.addChild(sizeLabel)

        var timeOffset = Date.parse(entryObj.startedDateTime) - this.startTime
        var scaledBarOffset = this.urlAreaWidth + this.scaleToSize(timeOffset, this.getBarAreaWidth())
        var resourceBar = this.makeResourceBar(scaledBarOffset, yCoord, entryObj)
        container.addChild(resourceBar)

        var durationLabel = new Text(entryObj.time + "ms", "13px Courier", "#000")
        durationLabel.x = this.timeBarSize(entryObj.time) + scaledBarOffset + 3
        durationLabel.y = yCoord + this.resourceHeight / 2
        durationLabel.textBaseline = "middle"
        container.addChild(durationLabel)

        this.stage.addChild(container);
        return container
    },

    makeResourceBar: function(x,y, entry) {
        var bar = new Shape()
        var scaledBarWidth = this.timeBarSize(entry.time)
        bar.graphics.beginFill(Graphics.getRGB(100,105,180))
                    .drawRect(x, y, scaledBarWidth, this.resourceHeight)
        var offset = 0
        for (var section in this.timeColors) {
            var duration = entry.timings[section]

            if (duration > 0) {
                var sectionWidth = this.scaleToSize(entry.timings[section], this.getBarAreaWidth())
                bar.graphics.beginFill(this.timeColors[section])
                            .drawRect(x + offset, y, sectionWidth, this.resourceHeight)
                offset += sectionWidth
            }
        }
        var waterfallDrawing = this
        bar.onMouseOver = function(e) {
            waterfallDrawing.currentTargetedTimeBar = entry
        }

        bar.onMouseOut = function(e) {
            waterfallDrawing.currentTargetedTimeBar = null
        }

        return bar
    },

    timeBarSize: function(duration) {
        return Math.max(this.scaleToSize(duration, this.getBarAreaWidth()), 1)
    },

    drawPageTimings: function() {

        var domContentTime = this.httpArchiveLog.pages[0].pageTimings.onContentLoad

        if (domContentTime > 0) {
          var domContentX = this.urlAreaWidth + this.scaleToSize(domContentTime, this.getBarAreaWidth())

          var domContentLine = new Shape()
          domContentLine.graphics.moveTo(domContentX, 0)
                                 .setStrokeStyle(1)
                                 .beginStroke(Graphics.getRGB(0,0,255))
                                 .lineTo(domContentX, this.getCanvasHeight())
          this.stage.addChild(domContentLine)
        }
        var onLoadTime = this.httpArchiveLog.pages[0].pageTimings.onLoad

        if (onLoadTime > 0) {
          var onLoadX = this.urlAreaWidth + this.scaleToSize(onLoadTime, this.getBarAreaWidth())

          var onLoadLine = new Shape()
          onLoadLine.graphics.moveTo(onLoadX, 0)
                             .setStrokeStyle(1)
                             .beginStroke(Graphics.getRGB(255,0,0))
                             .lineTo(onLoadX, this.getCanvasHeight())
          this.stage.addChild(onLoadLine)
        }
    },

    drawRectangle: function(x,y, width, height, rgbColor) {
        var shape = new Shape()
        shape.graphics.setStrokeStyle(2)
                      .beginStroke(rgbColor)
                      .drawRect(x, y, width, height)
        this.stage.addChild(shape)
    },

    /*
     * Shows the url tooltip for the given entry at (x, y), where x and y are relative to the canvas
     */
    showURLTooltip: function(entry, x, y) {
        var fieldValues = {
            "URL": entry.request.url,
            "Resource Size": formatAsSizeStr(entry.response.bodySize),
            "HTTP Response": entry.response.status + " " + entry.response.statusText,
            "Request Method": entry.request.method
        }

        $("#resource-info-table tr").each(function() {
            var name = $(this).find(".key").html()
            $(this).find(".value").html(fieldValues[name])
        })

        if (x > this.getCanvasWidth() / 2) {
            x -= $("#resource-info-table").width()
        }

        y -= $("#resource-info-table").height()

        var offset = this.canvas.offset()
        $("#resource-info-table").css("left", x + offset.left + "px")
        $("#resource-info-table").css("top", y + offset.top + "px")
        $("#resource-info-table").css("visibility", "visible")
        $("#resource-info-table").css("display", "inline")
    },

    hideURLTooltip: function() {
        $("#resource-info-table").css("visibility", "hidden")
    },

    fadeOutURLTooltip: function() {
        $("#resource-info-table").fadeOut('slow')
    },

    /*
     * Shows the timebar tooltip for the given entry at (x, y), where x and y are relative to the canvas
     */
    showTimeBarTooltip: function(entry, x, y) {
        $("#timebar-tooltip-table tr").each(function() {
            var labelCell = $(this).find(".label")
            var durationCell = $(this).find(".duration")
            durationCell.html(entry.timings[labelCell.html()])
        })

        if (x > this.getCanvasWidth() / 2) {
            x -= $("#timebar-tooltip-table").width()
        }

        y -= $("#timebar-tooltip-table").height()

        var offset = this.canvas.offset()
        $("#timebar-tooltip-table").css("left", x + offset.left + "px")
        $("#timebar-tooltip-table").css("top", y + offset.top + "px")
        $("#timebar-tooltip-table").css("visibility", "visible")
        $("#timebar-tooltip-table").css("display", "inline")
    },

    hideTimeBarTooltip: function() {
        $("#timebar-tooltip-table").css("visibility", "hidden")
    },

    fadeOutTimeBarTooltip: function() {
        $("#timebar-tooltip-table").fadeOut('slow')
    },

    getCanvasHeight: function() {
        return this.canvas.attr("height")
    },

    getCanvasWidth: function() {
        return this.canvas.attr("width")
    },

    getBarAreaWidth: function() {
        return this.getCanvasWidth() - this.urlAreaWidth - this.rightLabelAreaWidth
    }
})