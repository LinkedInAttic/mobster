// Info table superclass - provides a way to define columns and functions to calculate column values
var BasicHARInfoTable = Class.extend({
    init: function(elementId, harFiles, fields) {
        self.table = document.getElementById(elementId)
        self.thead = document.createElement("thead")
        this.addHeaderRow(fields)
        self.table.appendChild(self.thead)
        self.tbody = document.createElement("tbody")
        for (i in harFiles) {
            this.addDataRow(harFiles[i], i, fields)
        }
        self.table.appendChild(self.tbody)
    },
    addHeaderRow: function(fields) {
       var row = document.createElement("tr")

       for (field in fields) {
           var cell = document.createElement("th")
           cell.appendChild(document.createTextNode(field))
           row.appendChild(cell)
       }
       self.thead.appendChild(row)
    },

    addDataRow: function(harFile, index, fieldFuncs) {
        var row = document.createElement("tr")

        for (field in fieldFuncs) {
            var cell = document.createElement("td")
            var textNode = document.createTextNode(fieldFuncs[field](harFile))
            cell.appendChild(textNode)
            row.appendChild(cell)
        }

        self.tbody.appendChild(row)
    },

    getPageKey: function(harFile) {
        var name = harFile["log"]["pages"][0]["_pageName"]
        if(name.length > 15) {
            name = name.substr(0, 15) + "..."
        }
        return name
    }
})

// Shows information about the device, e.g. Browser, OS name
var DeviceInfoTable = BasicHARInfoTable.extend({
    init: function(elementId, harFiles) {
        var fields = {
            "OS Name": this.getOSName,
            "OS Version": this.getOSVersion,
            "Browser Name": this.getBrowserName,
            "Browser Version": this.getBrowserVersion
        }
        this._super(elementId, [harFiles[0]], fields)
    },

    getOSName: function(harFile) {
        return harFile.log._os._name
    },

    getOSVersion: function(harFile) {
        return harFile.log._os._version
    },

    getBrowserName: function(harFile) {
        return harFile.log.browser.name
    },

    getBrowserVersion: function(harFile) {
        return harFile.log.browser.version
    }
})

// Abstract info table class which contains a final column containing a link to the respective waterfall for the harFile
var PageLinkedInfoTable = BasicHARInfoTable.extend({
    addDataRow: function(harFile, index, fieldFuncs) {
        var row = document.createElement("tr")

        for (field in fieldFuncs) {
            var cell = document.createElement("td")
            var textNode = document.createTextNode(fieldFuncs[field](harFile))
            cell.appendChild(textNode)
            row.appendChild(cell)
        }

        var linkCell = document.createElement("td")
        var link = document.createElement("a")
        link.setAttribute("href", "#waterfall")
        link.appendChild(document.createTextNode("Waterfall"))
        link.onclick = function() {
            var waterfallContainer = document.getElementById("waterfall-container")
            waterfallContainer.removeChild(document.getElementById("waterfall-canvas"))
            new HTTPWaterfallDrawing("waterfall-canvas", "waterfall-container", harFile)
            $("#waterfall-label").text(harFile.log.pages[0]._pageName)
        }
        linkCell.appendChild(link)
        row.appendChild(linkCell)

        self.tbody.appendChild(row)
    },

    addHeaderRow: function(fields) {
        var row = document.createElement("tr")

        for (field in fields) {
            var cell = document.createElement("th")
            cell.appendChild(document.createTextNode(field))
            row.appendChild(cell)
        }

        var linkCell = document.createElement("th")
        linkCell.appendChild(document.createTextNode("Link to Waterfall"))
        row.appendChild(linkCell)

        self.thead.appendChild(row)
    }
})

var PageTimingTable = PageLinkedInfoTable.extend({
    init: function(elementId, harFiles) {
        var fields = {
            "Page Key":                     this.getPageKey,
            "OnContentLoad Time":           this.getOnContentLoad,
            "OnLoad Time":                  this.getOnLoad,
            "Total CSS Time":               this.getCSSTotalTime
        }
        this._super(elementId, harFiles, fields)
    },

    getCSSTotalTime: function(harFile) {
        return harFile["log"]["pages"][0]["_cssStats"]["_totalTime"]
    },

    getOnContentLoad: function(harFile) {
        return harFile["log"]["pages"][0]["pageTimings"]["onContentLoad"] + "ms"
    },

    getOnLoad: function(harFile) {
        return harFile["log"]["pages"][0]["pageTimings"]["onLoad"] + "ms"
    }
})

var PageMetricsTable = PageLinkedInfoTable.extend({
    init: function(elementId, harFiles) {
        var fields = {
            "Page Key":                     this.getPageKey,
            "Number of Style Recalculates": this.getStyleRecalculates,
            "Number of Paints":             this.getPaints,
            "Total Page Weight":            this.getTotalPageWeight
        }
        this._super(elementId, harFiles, fields)
    },

    getStyleRecalculates: function(harFile) {
        return harFile["log"]["pages"][0]["_eventStats"]["_styleRecalculates"]
    },

    getPaints: function(harFile) {
        return harFile["log"]["pages"][0]["_eventStats"]["_paints"]
    },

    getTotalPageWeight: function(harFile) {
        var total = 0
        for (i in harFile["log"]["entries"]) {
            var entry = harFile["log"]["entries"][i]
            total += entry["response"]["bodySize"]
        }
        return formatAsSizeStr(total)
    }
})

// Metrics table containing information about memory utilization and garbage collection
var MemoryMetricsTable = PageLinkedInfoTable.extend({
    init: function(elementId, harFiles) {
        var fields = {
            "Page Key":                     this.getPageKey,
            "Maximum Used Heap":            this.getMaxUsedHeap,
            "Average Used Heap":            this.getAvgUsedHeap,
            "Number of Nodes":              this.getNumNodes,
            "Number of GC Events":          this.getGCEvents
        }
        this._super(elementId, harFiles, fields)
    },

    getMaxUsedHeap: function(harFile) {
        return formatAsSizeStr(harFile.log.pages[0]._memoryStats._maxUsedHeapSize)
    },

    getAvgUsedHeap: function(harFile) {
        return formatAsSizeStr(harFile.log.pages[0]._memoryStats._avgUsedHeapSize)
    },

    getNumNodes: function(harFile) {
        var nodeCountObj = harFile["log"]["pages"][0]["_domNodeStats"]
        var total = 0
        for (i in nodeCountObj["domGroups"]) {
            total += nodeCountObj["domGroups"][i]["size"]
        }
        return total
    },

    getGCEvents: function(harFile) {
        return harFile["log"]["pages"][0]["_eventStats"]["_gcEvents"]
    }
})
