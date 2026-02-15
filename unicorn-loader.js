// UnicornStudio loader - инициализация UnicornStudio анимаций
!function(){
  var u=window.UnicornStudio;
  if(u&&u.init){
    if(document.readyState==="loading"){
      document.addEventListener("DOMContentLoaded",function(){u.init()})
    }else{
      u.init()
    }
  }else{
    window.UnicornStudio={isInitialized:!1};
    var i=document.createElement("script");
    i.src="https://cdn.jsdelivr.net/gh/hiunicornstudio/unicornstudio.js@v2.0.5/dist/unicornStudio.umd.js",
    i.onload=function(){
      if(document.readyState==="loading"){
        document.addEventListener("DOMContentLoaded",function(){UnicornStudio.init()})
      }else{
        UnicornStudio.init()
      }
    },(document.head||document.body).appendChild(i)
  }
}();
