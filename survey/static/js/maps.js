var map = L.map('completion_map').setView([0,32.683525], 7, {zoomControl: true, doubleClickZoom: false, scrollWheelZoom:false}),
  osmUrl='http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
  osmAttrib='Mics survey  © Mics';
  layer = new L.TileLayer(osmUrl, {minZoom: 6, maxZoom: 12, attribution: osmAttrib});

map.addLayer(layer);
   
$(function(){
    $.getJSON("/survey/3/completion/json/", function (rate_data) {
        $.getJSON("/static/map_resources/uganda_districts_2011_005.json", function (data) {
          $.each(data, function(element){
             data.features.map(function(feature){
              feature.properties.rate = rate_data[feature.properties['DNAME_2010']]
            })
          });
        L.geoJson(data, {style: style, onEachFeature: onEachFeature}).addTo(map); 
      });
    });
});
  
function getColorFor(rate) {
    return rate > 80 && rate <= 100 ? '#800026' :
           rate > 60 && rate <= 80  ? '#BD0026' :
           rate > 40 && rate <= 60  ? '#E31A1C' :
           rate > 20 && rate <= 40  ? '#FC4E2A' :
           rate > 0  && rate <= 20  ? '#FD8D3C' : 
           '#FFFFFF';
    }

function style(feature) {
    return {
        fillColor: getColorFor(feature.properties.rate),
        weight: 5,
        opacity: 0.65,
        color: '#333',
        dashArray: '3',
        fillOpacity: 0.7
    };
}

function onEachFeature(feature, layer) {
  layer.on({
      mouseover: showCompletionRate
  });
}


var info = L.control();

info.onAdd = function (map) {
  this._div = L.DomUtil.create('div', 'info'); 
  this.update();
  return this._div;
};
info.update = function (props) {
  this._div.innerHTML = '<h1>Completion rates:</h1> <br />';
  if(typeof props != 'undefined'){
    this._div.innerHTML += props['DNAME_2010'] +': '+ props.rate + '%';
  }
};

info.addTo(map);

function showCompletionRate(e){
  var layer = e.target;
  var property = layer.feature.properties
  info.update(property)
}