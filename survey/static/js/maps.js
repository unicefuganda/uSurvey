var map = L.map('completion_map').setView([1.34,32.683525], 7, {zoomControl: true, doubleClickZoom: false, scrollWheelZoom:false}),
    osmUrl='http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    info = L.control(),
    legend = L.control({position: 'bottomright'}),
    geojson;
  osmAttrib='Mics survey  © Mics';
  layer = new L.TileLayer(osmUrl, {minZoom: 6, maxZoom: 12, attribution: osmAttrib});

map.addLayer(layer);

$(function(){
    $("#surveys").on('change', function(){
        getCompletionFor($(this).val())

    })
});

function getCompletionFor(survey_id){
    $.getJSON("/survey/"+ survey_id +"/completion/json/", function (rate_data) {
        $.getJSON("/static/map_resources/uganda_districts_2011_005.json", function (data) {
          $.each(data, function(element){
             alert(JSON.stringify(data));
             data.features.map(function(feature){
              feature.properties.rate = rate_data[feature.properties['DNAME_2010']]
            })
          });
       geojson = L.geoJson(data, {style: style, onEachFeature: onEachFeature}).addTo(map);
      });
    });
}

function getColorFor(rate) {
    return rate > 80 && rate <= 100 ? '#800026' :
           rate > 60 && rate <= 80  ? '#BD0026' :
           rate > 40 && rate <= 60  ? '#E31A1C' :
           rate > 20 && rate <= 40  ? '#FC4E2A' :
           rate > 0  && rate <= 20  ? '#FD8D3C' :
           rate == 0 ? '#FFFFFF':
           '#D1D0CE';
    }

function style(feature) {
    return {
        fillColor: getColorFor(feature.properties.rate),
        weight: 2,
        opacity: 0.55,
        color: '#FD8D3C',
        dashArray: '3',
        fillOpacity: 0.7
    };
}

function onEachFeature(feature, layer) {
    layer.on({
      mouseover: highlightDistrict,
      click: zoomDistrict,
      mouseout: resetDistrictHighlight
  });
}

info.onAdd = function (map) {
  this._div = L.DomUtil.create('div', 'info');
  this.update();
  return this._div;
};
info.update = function (props) {
  this._div.innerHTML = '<h1>Completion rates:</h1>';
  if(typeof props != 'undefined'){
    rate = props.rate >-1 ? props.rate + '%' : 'Survey not opened.';
    this._div.innerHTML += props['DNAME_2010'] +': '+ rate;
  }
};

var legend = L.control({position: 'bottomright'});

legend.onAdd = function (map) {
    var div = L.DomUtil.create('div', 'info legend'),
        grades = [0,20, 40, 60, 80, 100];
    div.innerHTML += "<h1>Key</h1>"
        + '<i style="background:' + getColorFor(-1) + '"></i>'+ " Survey not opened<br/>";
    for (var i = 0; i < grades.length; i++) {
        div.innerHTML +=
            '<i style="background:' + getColorFor(grades[i] + 1) + '"></i> ';
        if(typeof  grades[i] != 'undefined' && typeof  grades[i +1] != 'undefined'){
            div.innerHTML += grades[i] +" &mdash; "+ (grades[i + 1]) + "% <br/>"
        }
    }
    return div;
};

var survey_selector = L.control({position: 'topleft'});

    survey_selector.onAdd = function(map){
        var selector_div = L.DomUtil.create('div', 'survey');
        var surveysHtml = $('#completion_form');
        $(selector_div).html(surveysHtml.html());
        $(surveysHtml).removeAttr('class', 'hide')
        $(surveysHtml).remove()
        return selector_div;
    }

legend.addTo(map);
info.addTo(map);
survey_selector.addTo(map)

function highlightDistrict(event){
    var layer = event.target
    layer.setStyle({
        weight: 3,
        color:'#666',
        dashArray: '',
        fillOpacity: 0.3
    })
   if (!L.Browser.ie && !L.Browser.opera) {
        layer.bringToFront();
    }

    info.update(layer.feature.properties)
}

function zoomDistrict(event){
    map.fitBounds(event.target.getBounds())
}

function resetDistrictHighlight(event){
    geojson.resetStyle(event.target)
}