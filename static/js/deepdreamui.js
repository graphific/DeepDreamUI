/*!
* DeepDream UI
*/


// main param Json
var params_view = { 
  params: {
  	jobname:"",
    presets: ["full", "medium","low"],
    network: ["googlelenet", "placesnet"],
    layers: "inception_3b/output",
    octaves: 4,
    octavescale: 1.4,
    itterations: 10,
    jitter: 32,
    stepsize: 1.5,
    blend: 0.5,
    opticalflow: 1,
    guide: "",
    gpu: 1,
    input:"static/input/mydir/",
    output:"static/output/mydir/",
    author:"authorname",
    date:''
  }
};
var selectedFiles = [];

// list directories & files
function get_directory(id,type) {  
  console.log("get_directory: dir: " + id + " type: " + type);

  // check if file is image
  function checkURLImg(url) { return(url.match(/\.(jpeg|jpg|png)$/) != null); }
  function checkURLVid(url) { return(url.match(/\.(mp4|mov)$/) != null); }
  
  // capitalize First Letter
  function capitalizeFirstLetter(string) { return string.charAt(0).toUpperCase() + string.slice(1);}

  // select/deselect files
  selectedFiles = [];
  function imageselector(obj,file){
    if(!obj.hasClass("input_img_selected") ) {
      obj.addClass("input_img_selected");

      selectedFiles.push(file);
    } 
    else {
      obj.removeClass("input_img_selected");
      
      var index = selectedFiles.indexOf(file);
      selectedFiles.splice(index, 1);
    }
    //console.log(selectedFiles);
  }

  // directory click handler
  function directoryClickHandler(obj,dir,type,container,doublclick){
    if(doublclick){
      if(type === "input"){ 
        $(obj).click(function(){ imageselector($(this),dir); }).dblclick(function(){ get_directory(dir,type); }).appendTo("#"+container);

      }
      if(type === "output"){ 
        $(obj).click(function(){ imageselector($(this),dir); }).dblclick(function(){ get_directory(dir,type); }).appendTo("#"+container);
      }   
    }
    else{
      if(type === "input"){ $(obj).click(function(){ get_directory(dir,type); }).appendTo("#"+container);}
      if(type === "output"){ $(obj).click(function(){ get_directory(dir,type); }).appendTo("#"+container);}   
    }   
  }

  function popupimage(file,container,image) {
    $('.popup-gallery').magnificPopup({
      delegate: 'a',
      type: 'image',
      tLoading: 'Loading image #%curr%...',
      mainClass: 'mfp-img-mobile',
      gallery: {
        enabled: true,
        navigateByImgClick: true,
        preload: [0,1] // Will preload 0 - before current, and 1 after the current image
      },
      image: {
        tError: '<a href="%url%">The image #%curr%</a> could not be loaded.',
        titleSrc: function(item) {
          return item.el.attr('title'); //+ '<small>by Marsel Van Oosten</small>';
        }
      }
    });

    $('.popup-gallery').html('');

    $(container).find(image).each(function( index, value ) {
      $('.popup-gallery').append('<a href="'+value.src+'" title="'+value.title+'"><img src="'+value.src+'" height="75" width="75"></a>');
    });


    $(container).find(image).each(function( index, value ) {
      if(file === value.title){
        console.log("magnificPopup open index: " + index + " filename: " + value.title);
        $('.popup-gallery').magnificPopup('open', index); // Will open popup with 5th item
      }
    });
  }

  function imageClickHandler(obj,type,container,file){       

    // click/doubleclick handler
    if(type === "input"){ 
      $(obj).click(function(){ imageselector($(this),file); }).dblclick(function(){ popupimage(file,'#container_input','.frame_input'); }).appendTo("#"+container);
    }
    if(type === "output"){ 
      $(obj).click(function(){ imageselector($(this),file); }).dblclick(function(){ popupimage(file,'#container_output','.frame_output'); }).appendTo("#"+container);
    }        
  }

  function videoClickHandler(obj,type,container,file){
    if(type === "input"){ $(obj).click(function(){ imageselector($(this),file); }).appendTo("#"+container);}
    if(type === "output"){ $(obj).click(function(){ imageselector($(this),file); }).appendTo("#"+container);}      
  }
  
  // clear divs
  if(type === "input"){
    $("#container_input").html("");
    $("#input_dir_display").html("");
    params_view.params.input = id;
  }
  if(type === "output"){
    $("#container_output").html("");
    $("#output_dir_display").html("");
    params_view.params.output = id;
  }

  function directoryTextDisplay(txt){
    txt = txt.split("/");
    txt = txt[txt.length-1];
    var shortText = jQuery.trim(txt).substring(0, 25).trim(this);
    return shortText;
  }

  // get from server
  $.ajax({
    type: "POST",
    contentType: "application/json; charset=utf-8",
    url: "/api/v1.0/getdirectory",
    data: JSON.stringify({id:id, type:type}),
    success: function (data) {
    
      // append directories
      for(var i=0; i<data.dirs.length;i++){
        var dir ='<div class="input_img_container data_img"><img title="'+data.dirs[i]+'" class="input_img" src="static/img/folder.png" /><div class="data_img_text">'+directoryTextDisplay(data.dirs[i])+'</div></div>';
        if(type === "input"){ directoryClickHandler(dir,data.dirs[i],"input","container_input",true); }
        if(type === "output"){ directoryClickHandler(dir,data.dirs[i],"output","container_output",true); }
      }

      // append video
      for(var i=0; i<data.files.length;i++){
        if(checkURLVid(data.files[i])){
          var vid ='<div class="input_img_container data_img"><img title="'+data.files[i]+'" class="input_img" src="static/img/video.png" /><div class="data_img_text">'+directoryTextDisplay(data.files[i])+'</div></div>';

          if(type === "input"){ videoClickHandler(vid,"input","container_input",data.files[i]); }
          if(type === "output"){ videoClickHandler(vid,"output","container_output",data.files[i]); }
        }
      }

      var foundimgcount = 0;
      $('.popup-gallery').html('');
      // append images
      for(var i=0; i<data.files.length;i++){

        if(checkURLImg(data.files[i])){
          var timestamp = new Date().getTime();

          foundimgcount++;

          if(type === "input"){ 
            var newimg ='<div class="input_img_container"><img title="'+data.files[i]+'" class="input_img frame_input" src="'+ data.files[i] +'?'+timestamp+' " /></div';
            imageClickHandler(newimg,"input","container_input",data.files[i]); }
          if(type === "output"){ 
            var newimg ='<div class="input_img_container"><img title="'+data.files[i]+'" class="input_img frame_output" src="'+ data.files[i] +'?'+timestamp+' " /></div';
            imageClickHandler(newimg,"output","container_output",data.files[i]); 
          }
        }
      }

      // directory path display tool
      function directoryDisplay(container, amount, dirdisplay,type){
        // split incoming directory string
        splitdir = id.split("/");
        splitdir.splice(0, 2);
        if(splitdir[0].length <= 0){splitdir.pop();}

        // append root directory
        //$("#"+dirdisplay).html('<span><a href="">'+capitalizeFirstLetter(type)+'</a></span>');
        var dir = '<span class="clickable">'+capitalizeFirstLetter(type)+'</span>'
        var finaldir = 'static/'+type+'/';
        directoryClickHandler(dir,finaldir,type,dirdisplay,false);

        // append sub-directories
        for(var i=0;i<splitdir.length;i++){
          var dir = '<span class="clickable"> > '+splitdir[i]+'</span>'
          
          // get global path for all directories in current path
          var finaldir = 'static/'+type;
          for(var x=0;x<splitdir.length;x++){ 
            finaldir += '/'+splitdir[x];
            if(splitdir[x] === splitdir[i]){break;}
          }

          // hook up to clickhandler
          directoryClickHandler(dir,finaldir,type,dirdisplay,false);
        }

        // append image count
        $("#"+dirdisplay).append('<span class="imgcount">'+foundimgcount+' img</span>');
      }

      // display directories & path info
      if(type === "input"){ directoryDisplay("container_input","input_amount","input_dir_display","input"); }
      if(type === "output"){ directoryDisplay("container_output","output_amount","output_dir_display","output"); }
    },
    dataType: "json"
  });
}

function get_console(id) {
  var timestamp = new Date().getTime();
  jQuery.get('static/render.log?t='+ timestamp, function(data) {
    $("#output_console").val(data); 
  });
}

function display_job(fileId){
	console.log(fileId);

	$.getJSON( fileId, function( d ) {
	  	console.log(d);
	 	$("#jobs_table").append("<tr><td>"+d.jobname+"</td><td>"+d.date+"</td><td>"+d.author+"</td><td><a href='" + fileId + "'><span class='glyphicon glyphicon-circle-arrow-down'></span> Load</a></td><td><a href=''><span class='glyphicon glyphicon-remove'></span> Delete</a></td></tr>");
	 		
	});
}

function get_jobs(){
	$("#jobs_table").empty();
  $.ajax({
    type: "POST",
    contentType: "application/json; charset=utf-8",
    url: "/api/v1.0/getjobs",
    success: function (data) {

      for(var i=0;i<data.files.length;i++){
      	display_job(data.files[i]);
      }
    },
    dataType: "json"
  });
}

function stop_render(){
  $("#render_final").show();
  $("#render_final_stop").hide();

  $.ajax({
    type: "POST",
    contentType: "application/json; charset=utf-8",
    url: "/api/v1.0/stoprender",
    data: JSON.stringify(params_view.params),
    success: function (data) {
      console.log(data);
    },
    dataType: "json"
  });
}

function get_render() {   
  console.log(params_view.params); 
  $("#render_final").hide();
  $("#render_final_stop").show();

  $.ajax({
    type: "POST",
    contentType: "application/json; charset=utf-8",
    url: "/api/v1.0/getrender",
    data: JSON.stringify(params_view.params),
    success: function (data) {
      console.log(data);
      $("#render_final").show();
      $("#render_final_stop").hide();
    },
    dataType: "json"
  });
}

function setupForm(){      
  // presets
  $("#params_presets").empty();
  for(var i = 0; i < params_view.params.presets.length; i++) {
    $("#params_presets").append('<option value="'+params_view.params.presets[i]+'">'+params_view.params.presets[i]+'</option>')
  }
  $('#params_octaves').on('change', function() { params_view.params.presets = this.value;});

  // network
  $("#params_network").empty();
  for(var i = 0; i < params_view.params.network.length; i++) {
    $("#params_network").append('<option value="'+params_view.params.network[i]+'">'+params_view.params.network[i]+'</option>')
  }
  $('#params_octaves').on('change', function() { params_view.params.network = this.value;});

  // layers
  $("#params_layers").val(params_view.params.layers);
  $('#params_layers').on('change', function() { params_view.params.layers = this.value;});

  // octaves
  $("#params_octaves").empty();
  for(var i = 1; i <= 5; i++) {
    var selected = ''
    if(i === params_view.params.octaves){selected = 'selected'}
    $("#params_octaves").append('<option '+selected+' value="'+i+'">'+i+'</option>')
  }
  $('#params_octaves').on('change', function() { params_view.params.octaves = this.value;});

  // octave scale
  $("#params_octavescale").empty();
  var octavescalecounter = 0;
  for(var i = 1; i <= 100; i++) {
    var selected = ''
    if(i === (params_view.params.octavescale*10) ){selected = 'selected'}
    $("#params_octavescale").append('<option '+selected+' value="'+i/10+'">'+i/10+'</option>');
  }
  $('#params_octavescale').on('change', function() { params_view.params.octavescale = this.value;});

  // itterations
  $("#params_iterations").empty();
  for(var i = 1; i <= 200; i++) {
    var selected = ''
    if(i === params_view.params.itterations){selected = 'selected'}
    $("#params_iterations").append('<option '+selected+' value="'+i+'">'+i+'</option>')
  }
  $('#params_iterations').on('change', function() { params_view.params.itterations = this.value;});

  // jitter
  $("#params_jitter").empty();
  for(var i = 1; i <= 100; i++) {
    var selected = ''
    if(i === params_view.params.jitter){selected = 'selected'}
    $("#params_jitter").append('<option '+selected+' value="'+i+'">'+i+'</option>');
  }
  $('#params_jitter').on('change', function() { params_view.params.jitter = this.value;});

  // stepsize
  $("#params_stepsize").empty();
  for(var i = 1; i <= 100; i++) {
    var selected = ''
    if(i === (params_view.params.stepsize*10) ){selected = 'selected'}
    $("#params_stepsize").append('<option '+selected+' value="'+i/10+'">'+i/10+'</option>');
  }
  $('#params_stepsize').on('change', function() { params_view.params.stepsize = this.value;});

  // blend
  $("#params_blend").empty();
  for(var i = 1; i <= 10; i++) {
    var selected = ''
    if(i === (params_view.params.blend*10) ){selected = 'selected'}
    $("#params_blend").append('<option '+selected+' value="'+i/10+'">'+i/10+'</option>');
  }
  $('#params_blend').on('change', function() { params_view.params.blend = this.value;});

  // optical flow
  $("#params_opticalflow").empty();
  for(var i = 0; i <= 1; i++) {
    var selected = ''
    if(i === params_view.params.opticalflow ){selected = 'selected'}
    $("#params_opticalflow").append('<option '+selected+' value="'+i+'">'+i+'</option>');
  }
  $('#params_opticalflow').on('change', function() { params_view.params.opticalflow = this.value;});

  // guide
  $("#params_guide").val(params_view.params.guide);
  $('#params_guide').on('change', function() { params_view.params.guide = this.value;});

  // gpu
  $("#params_gpu").empty();
  for(var i = 0; i <= 1; i++) {
    var selected = ''
    if(i === params_view.params.gpu ){selected = 'selected'}
    $("#params_gpu").append('<option '+selected+' value="'+i+'">'+i+'</option>');
  }
  $('#params_gpu').on('change', function() { params_view.params.gpu = this.value;});

}

var renderInterval;

$(function() {
  setupForm();
  get_directory("static/input/","input");
  get_directory("static/output/","output");
  get_console("idtag");
  $("#render_final").show();
  $("#render_final_stop").hide();


  get_jobs();
  
  /////// click handlers

  // start renderer
  $("#render_final").click(function(event) {
    event.preventDefault(); 
    get_render();

    // renderer feedback HACK
    clearInterval(renderInterval);
    renderInterval = setInterval(function(){ 
      get_console("idtag"); 
      setTimeout(function(){
        var textarea = document.getElementById('output_console');
        textarea.scrollTop = textarea.scrollHeight + 100;  
        get_directory(params_view.params.output,"output");
      },200);
    },5000);
  });

  // stop renderer
  $("#render_final_stop").click(function(event) {
    event.preventDefault(); 
    stop_render();
    clearInterval(renderInterval);
    renderInterval = null;
    get_directory(params_view.params.output,"output");
  });

  // save render job
  $("#render_savejob").click(function(event) {
    event.preventDefault(); 
    var jobname = prompt("Enter Job Name", "");
    if (jobname != null) {
    	params_view.params.jobname = jobname;
    	params_view.params.date = new Date();
    	$.ajax({
	        type: "POST",
	        contentType: "application/json; charset=utf-8",
	        url: "/api/v1.0/makejob",
	        data: JSON.stringify({job:params_view.params}),
	        success: function (data) {
	        	alert("Job Created: " + data.output);
	          	console.log("job created: " + data);
	          	get_jobs();
	        },
	        dataType: "json"
	    });
    }
  });

  function makefolder(type){
    var foldername = prompt("Enter Folder Name", "");
    if (foldername != null) {
      var finalfoldername;
      if(type === "input"){finalfoldername = params_view.params.input + foldername;}
      if(type === "output"){finalfoldername = params_view.params.output + foldername;}
      
      $.ajax({
        type: "POST",
        contentType: "application/json; charset=utf-8",
        url: "/api/v1.0/makefolder",
        data: JSON.stringify({id:finalfoldername}),
        success: function (data) {
          console.log("folder created: " + finalfoldername);
          if(type === "input"){get_directory(params_view.params.input,type);}
          if(type === "output"){get_directory(params_view.params.output,type);}
        },
        dataType: "json"
      });
    }
  }

  function deleteFile(file){
    $.ajax({
      type: "POST",
      contentType: "application/json; charset=utf-8",
      url: "/api/v1.0/delete",
      data: JSON.stringify({id:file}),
      success: function (data) {
        console.log("files deleted: " + file);
        get_directory(params_view.params.input,"input");
        get_directory(params_view.params.output,"output");
      },
      dataType: "json"
    });
  }


  function extractmovie(file,dir) {
    $.ajax({
      type: "POST",
      contentType: "application/json; charset=utf-8",
      url: "/api/v1.0/extractmovie",
      data: JSON.stringify({movie:file,directory:dir}),
      success: function (data) {
        console.log("frames extracted from: " + file);
        get_directory(params_view.params.input,"input");
        get_directory(params_view.params.output,"output");
      },
      dataType: "json"
    });
  }

  //extract movie
  $("#input_makemovie").click(function(event) {
    event.preventDefault();

    inputitems = []
    selectedFiles.map( function(item) {
      //alert(item);
      if(item.indexOf("static/input/") > -1 && ( item.indexOf(".mp4") > -1 || item.indexOf(".avi") > -1 ) ) 
        inputitems.push(item);
    })
    if(inputitems.length > 1)
      alert('please select only one movie at a time');
    else if(inputitems.length == 0)
      alert('nothing selected, mp4 and avi only for now');
    else {
      
    //var file = prompt("file", "");
    var dir = prompt("dir", "");
      //params_view.params.input + 
      extractmovie(inputitems[0], params_view.params.input + dir);
    }
    
  });

  // make dir
  $("#input_makefolder").click(function(event) {
    event.preventDefault();
    makefolder("input");
  });
  $("#output_makefolder").click(function(event) {
    event.preventDefault();
    makefolder("output");
  });

  // delete files
  $(".file_delete").click(function(event) {
    event.preventDefault();
    if(selectedFiles.length > 0){
      var answer = confirm("Delete "+selectedFiles.length+" files?")
      if(answer){
        console.log("delete: " + selectedFiles);
        deleteFile(selectedFiles);
      }
    }
    else{
      alert("no files or folders selected");
    }
  });

  // var source = new EventSource("/stream");
  // source.onmessage = function(event) {
  //     document.getElementById("output_console").innerHTML += event.data + "<br/>"
  // }
  

});
