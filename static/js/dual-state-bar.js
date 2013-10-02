function dualStateBarChart() {
    var daysToDisplay = 7,
        inactiveBarColor = "#E7E7E7",
        openBarColor = "#BBBBBB",
        closedBarColor = "#888888",
        openBarBaseY = 80,
        barHeight = 80,
        maxBarHeight = .75*56, // could scale this ****
        barPadding = 1,
        verticalPadding = 1,
        innerStrokeWidth = 1,
        duration = 400,
        barWidth = 13, ///
        tooltipOffsetsY = {'top': 40, 'bottom': -27};
        
    var dailyCount,
        slider,
        selectedRange;
    
    // Rewrite this
    var calculateMax = function() {
        var maxOpen = d3.max(dailyCount, function(d) { return d.open; }),
            maxClosed = d3.max(dailyCount, function(d) { return d.closed; });
        
        return d3.max([maxOpen, maxClosed]);
    }
    
    function resetBarColors(selectedRange) {
        d3.selectAll(".open")
            .attr("fill", function(d, i) { 
                if ((i < selectedRange[0]) || (i > selectedRange[1])) { 
                    return inactiveBarColor;
                } else { 
                    return openBarColor; 
                } 
        });
        
        d3.selectAll(".closed")
            .attr("fill", function(d, i) { 
                if ((i < selectedRange[0]) || (i > selectedRange[1])) { 
                    return inactiveBarColor;
                } else { 
                    return closedBarColor; 
                } 
        });
    }
    
    // External or Internal function?  
    // Rewrite     
    function setStatusCounts(selectedRange) {
        var totalOpen = 0,
            totalClosed = 0;
                        
        for (var i=selectedRange[0],limit=selectedRange[1]; i<=limit; i++) {
            totalOpen = totalOpen + dailyCount[i]['open'];
            totalClosed = totalClosed + dailyCount[i]['closed'];
        }
                            
        d3.select("#open-count")
            .html(totalOpen);
            
        d3.select("#closed-count")
            .html(totalClosed);
    }
    
    function redrawBars() {                        
        var max = calculateMax();
        
        d3.selectAll(".open")
            .data(dailyCount)
            .transition()
                .duration(duration)
                .attr("y", function(d) { return openBarBaseY- maxBarHeight*d['open']/max - verticalPadding; })
                .attr("height", function(d) { return maxBarHeight*d['open']/max; });
        
        d3.selectAll(".closed")
            .data(dailyCount)
            .transition()
                .duration(duration)
                .attr("height", function(d) { return maxBarHeight*d['closed']/max; });
        
        setStatusCounts(selectedRange);
    }
                  
    function chart(selection) {
        selection.each(function(data) {
            if (dailyCount) {
                dailyCount = data;
                redrawBars();
                
                return;
            }
             
            dailyCount = data;
            
            var numDays = dailyCount.length; /**/
            
            selectedRange = [numDays - daysToDisplay, numDays - 1];
            setStatusCounts(selectedRange);
        
            var chartCountsContainer = d3.select("#chart-counts-container"),
                chartContainer = d3.select("#chart-container"),
                chartContainerWidth = numDays * barWidth + (numDays - 1) * barPadding;
                                    
            chartContainer.style("width", chartContainerWidth + "px");
            
            d3.select("#slider-track").style("width", chartContainerWidth + 1 * innerStrokeWidth + "px");
            
            chartCountsContainer.style("display", "block"); // Just one node, CHANGE
            
            var tooltip = chartCountsContainer
                .append("div")
                    .attr("class", "tooltip");
            
            var prepareTooltip = function(tooltip, tooltipText, offsetY) {
                //console.log(d3.mouse(document.getElementById('chart-container')));
                
                var mouse_coords = d3.mouse(document.getElementById('chart-counts-container'));
                
                tooltip.style("display", "block")
                            .text(tooltipText)
                            .style("left", mouse_coords[0] - .5 * parseInt(tooltip.style("width"), 10) + "px")
                            .style("top", (mouse_coords[1] - offsetY) + "px");
            };
            
            var barMouseOver = function(d, elem, tooltipText, tooltipOffset) {
                d3.select(elem)
                  .classed("active", true);
                        
                prepareTooltip(tooltip, tooltipText, tooltipOffset);
            }
            
            var barMouseOut = function(elem) {
                d3.select(elem)
                  .classed("active", false);
                          
                tooltip.style("display", "none");
            }
            
            var dailyCountFormat = d3.time.format('%Y-%m-%d');
            
            var tooltipDateFormat = d3.time.format('%m/%-d/%Y'); // Change this on the server
                                
            var setBarMouseHandlers = function() {
                d3.selectAll(".open")
                    .on("mouseover", function(d) {
                        barMouseOver(d, this, d.open + ' Open from '
                         + tooltipDateFormat(dailyCountFormat.parse(d.date)), tooltipOffsetsY.top);
                      })
                    .on("mouseout", function(){
                        
                        barMouseOut(this);      
                    });
                
                d3.selectAll(".closed")
                    .on("mouseover", function(d) { 
                        barMouseOver(d, this, d.closed + ' Closed from ' 
                        + tooltipDateFormat(dailyCountFormat.parse(d.date)), tooltipOffsetsY.bottom);
                    })
                    .on("mouseout", function(){
                        barMouseOut(this);
                    });
            }
                                    
            var max = calculateMax();
                                
            var drawRect = function(selection, elemClass, color, y) {                                            
                selection
                    .attr("class", elemClass)
                    .attr("fill", function(d, i) { 
                        if (i < selectedRange[0]) { return inactiveBarColor; } else { return color; } 
                    })
                    .attr("x", function(d, i) {
                        return i * (barWidth + barPadding);
                    })
                    .attr("y", y)
                    .attr("height", 0)
                    .attr("width", barWidth)
                    .attr("fill-opacity", .0001)
                    .transition()
                        .duration(duration)
                        .delay(function(d, i) { return .25*i*numDays; })
                        .attr("fill-opacity", 1)
                        .attr("y", function(d) { 
                            if (elemClass === "open") {
                                return openBarBaseY - 2 - maxBarHeight*d[elemClass]/max - verticalPadding;
                                //return barHeight - (maxBarHeight*d[elemClass]/max) - verticalPadding;
                            } else {
                                return y;
                            }
                        })
                        .attr("height", function(d) { return 2 + maxBarHeight*d[elemClass]/max; });
                        //.attr("height", function(d) { return maxBarHeight*d[elemClass]/max; });
            }
            
            var x = d3.scale.linear().domain([0, numDays]).range([0, chartContainerWidth]);
            
            // Always make sure eastern time zone?
            var firstDay = dailyCount[0]['date'];
                                    
            var firstDayDate = dailyCountFormat.parse(firstDay);
            var dayOfWeek = firstDayDate.getDay();
                                
            var firstTick = 3;
                                
            var ticks = [];
            var tick = firstTick;
            
            while (tick < numDays) {
                ticks.push(tick);
                
                tick += 7;
            }
            
            var printedFormat = d3.time.format('%b %-d');
                                
            theChart = d3.select("#the-chart")
                    .attr("class", "chartArea");
                    
            theChart.append("div")
                .attr("id", "date-label-container")
                .selectAll("div")
                .data(ticks)
                .enter()
                .append("div")
                .attr("class", "date-label")
                .style("left", function(d) {
                    //return Math.ceil(x(d)) - 21 + "px";
                    return Math.ceil(x(d)) - 10 + "px";
                })
                .text(function(d) { return printedFormat(dailyCountFormat.parse((dailyCount[d]['date']))); });
                
            var chartSvg = theChart.append("svg")
                    .attr("width", chartContainerWidth)
                    .attr("height", 2*barHeight + 10 + 2);
                                                                        
            var openGroup = chartSvg.append("g"),
                closedGroup = chartSvg.append("g").attr("transform", "translate(0,92)");
                                
            openGroup.selectAll("rect")
                    .data(dailyCount)
                .enter()
                .append("rect")
                    .call(function(d) { drawRect(this, "open", openBarColor, openBarBaseY - verticalPadding) });
            
            closedGroup.selectAll("rect")
                    .data(dailyCount)
                .enter()
                .append("rect")
                    .call(function(d) { drawRect(this, "closed", closedBarColor, 0 + verticalPadding) });
            
            setBarMouseHandlers();
                                
            d3.select("#slider-track")
                .style("border", "1px solid #d6d6d6")
                .style("left", "6px");
            
            var slider = d3.select("#slider")
                .append("svg");
            
            slider
              .attr("class", "brush extent")
              .attr("display", "block")
              .attr("width", chartContainerWidth + 50)
              .attr("height", 10);
                                
            var brush = d3.svg.brush2()
                .x(x);
            
            var a = slider.append("g")
                .attr("transform", "translate(6, 0)")
                .attr("class", "brush extent")
                .call(brush
                    .extent([numDays - daysToDisplay, numDays])
                .on("brushstart", brushstart)
                .on("brush", brushmove)
                .on("brushend", brushend))
              .selectAll("rect")
                .attr("height", 10);
            
            var setBrush = function(xOffset, width) {
                brush.extent([xOffset, xOffset+width]);
                
                d3.select('rect.extent')
                    .attr("x", x(xOffset))
                    .attr("width", x(width));
                
                d3.select('g.resize.w')
                    .attr("transform", "translate(" + x(xOffset) + ",0)");
                
                d3.select('.resize.e')
                    .attr("transform", "translate(" + x(xOffset + width) + ",0)");
            }
            
            var setChart = function(xOffset, width) {
                selectedRange = [xOffset, xOffset + width - 1];
                
                resetBarColors(selectedRange);
                                                                   
                setStatusCounts(selectedRange);
            }
                
            d3.selectAll(".date-label")
                .on("click", function(d) {
                    var extent = brush.extent();
                    var currentExtentWidth = extent[1] - extent[0];
                    
                    var offset = Math.floor(.5*currentExtentWidth);
                                                
                    if (d-offset < 0) {
                        offset = d;
                    } else if ((d - offset + currentExtentWidth) > dailyCount.length) {
                        offset = d - dailyCount.length + currentExtentWidth;
                    }
                                                
                    setBrush(d-offset, currentExtentWidth);
                                                
                    setChart(d-offset, currentExtentWidth);
                });
                                
            function brushstart() {
                // Cancel the events on the bars
                d3.selectAll(".open")
                    .on("mouseover", null)
                    .on("mouseout", null);
                
                d3.selectAll(".closed")
                    .on("mouseover", null)
                    .on("mouseout", null);
            }
                                      
            function brushmove() {                      
                var extent = brush.extent();
                
                var firstDay = Math.round(extent[0]);
                
                // Clamping
                if (firstDay < 0) {
                    firstDay = 0;
                } else if (firstDay > numDays - 1) {
                    firstDay = numDays - 1;
                }
                
                var numDaysDisplayed = Math.round(extent[1] - extent[0]);
                
                if (numDaysDisplayed < 1) {
                    numDaysDisplayed = 1;
                } else if (firstDay + numDaysDisplayed > numDays) {
                    numDaysDisplayed = numDays - firstDay;
                }
                                        
                setBrush(firstDay, numDaysDisplayed);
                                        
                setChart(firstDay, numDaysDisplayed);
            }
                                
            function brushend() {                       
                setBarMouseHandlers();
            }
        });
    }
    
    return chart;
}