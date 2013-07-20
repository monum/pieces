function zoomByAbout(e) {
    var x = .5*$('#map').width(),
      y = .5*$('#map').height(),
      mouse_point = e.containerPoint,
      new_center_point = new L.Point((x + mouse_point.x) / 2, (y + mouse_point.y) / 2),
      new_center_location = map.containerPointToLatLng(new_center_point);
             
    map.setView(new_center_location, map.getZoom() + 1); 
}

//http://stackoverflow.com/questions/3505320/div-get-css-attributes-from-java-script
var getStyle = function(el,styleProp) {
    //el = document.getElementById(el);
    var result;
    if(el.currentStyle) {
        result = el.currentStyle[styleProp];
    } else if (window.getComputedStyle) {
        result = document.defaultView.getComputedStyle(el,null).getPropertyValue(styleProp);
    } else {
        result = 'unknown';
    }
    return result;
}

//https://github.com/ausi/Feature-detection-technique-for-pointer-events/blob/master/modernizr-pointerevents.js
var isPeSupported = function() {
    /* Test for pointer event support in the browser. */

    var element = document.createElement('x'),
        documentElement = document.documentElement,
        getComputedStyle = window.getComputedStyle,
        supports;

    if(!('pointerEvents' in element.style)){
        return false;
    }

    element.style.pointerEvents = 'auto';
    element.style.pointerEvents = 'x';
    documentElement.appendChild(element);
    supports = getComputedStyle && 
        getComputedStyle(element, '').pointerEvents === 'auto';
    documentElement.removeChild(element);
    return !!supports;
}

//http://stackoverflow.com/questions/2745432/best-way-to-detect-that-html5-canvas-is-not-supported
var isCanvasSupported = function() {
    /* Test for canvas element support in the browser. */

    var elem = document.createElement('canvas');
    return !!(elem.getContext && elem.getContext('2d'));
}

// http://stackoverflow.com/questions/5898656/test-if-an-element-contains-a-class
var hasClass = function(element, cls) {
    return (' ' + element.className + ' ').indexOf(' ' + cls + ' ') > -1;
}

var getDistance = function(x1,y1,x2,y2) {
    return Math.sqrt((x1-x2)*(x1-x2) + (y1-y2)*(y1-y2));
}

var sinh = function(value){
    var a = Math.pow(Math.E, value),
        b = Math.pow(Math.E, -1*value);

    return .5*(a-b);
}

var convertTileXYToLatLng = function(zoom, xTile, yTile) {
    var n = Math.pow(2, zoom),
        lonDeg = (xTile / n) * 360.0 - 180.0,
        latRad = Math.atan(sinh(Math.PI * (1 - 2 * yTile/n))),
        latDeg = latRad * 180.0 / Math.PI;

    return [lonDeg,latDeg];
}

var normalizeNeighborhoodName = function(neighborhood) {
    return neighborhood.toLowerCase().split(/[\s/]+/).join('_');
}
