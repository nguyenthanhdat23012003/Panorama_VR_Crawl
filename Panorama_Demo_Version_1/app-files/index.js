/*
 * Copyright 2016 Google Inc. All rights reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
'use strict';

(function() {
  var Marzipano = window.Marzipano;
  var bowser = window.bowser;
  var screenfull = window.screenfull;
  var data; // Will be set when data is loaded
  var viewer;
  var scenes = [];

  // Lấy product key hiện tại
  function getProductKey() {
    // Nếu router.js đã được tải, sử dụng hàm từ đó
    if (typeof getCurrentProduct === 'function') {
      return getCurrentProduct();
    }
    
    // Nếu không, thực hiện logic riêng
    var params = new URLSearchParams(window.location.search);
    var productParam = params.get('product');
    if (productParam) {
      return productParam;
    }
    
    // Mặc định trả về product đầu tiên
    return '1a5ab6424adfa1e1';
  }

  // Lấy product key
  var productKey = getProductKey();

  // Grab elements from DOM.
  var panoElement = document.querySelector('#pano');
  var sceneNameElement = document.querySelector('#titleBar .sceneName');
  var sceneListElement = document.querySelector('#sceneList');
  var sceneElements = document.querySelectorAll('#sceneList .scene');
  var sceneListToggleElement = document.querySelector('#sceneListToggle');
  var autorotateToggleElement = document.querySelector('#autorotateToggle');
  var fullscreenToggleElement = document.querySelector('#fullscreenToggle');

  // Detect desktop or mobile mode.
  if (window.matchMedia) {
    var setMode = function() {
      if (mql.matches) {
        document.body.classList.remove('desktop');
        document.body.classList.add('mobile');
      } else {
        document.body.classList.remove('mobile');
        document.body.classList.add('desktop');
      }
    };
    var mql = matchMedia("(max-width: 500px), (max-height: 500px)");
    setMode();
    mql.addListener(setMode);
  } else {
    document.body.classList.add('desktop');
  }

  // Detect whether we are on a touch device.
  document.body.classList.add('no-touch');
  window.addEventListener('touchstart', function() {
    document.body.classList.remove('no-touch');
    document.body.classList.add('touch');
  });

  // Use tooltip fallback mode on IE < 11.
  if (bowser.msie && parseFloat(bowser.version) < 11) {
    document.body.classList.add('tooltip-fallback');
  }

  // Initialize viewer when data is loaded
  function initViewer() {
    if (viewer) {
      return; // Already initialized
    }

    // Viewer options.
    var viewerOpts = {
      controls: {
        mouseViewMode: data.settings.mouseViewMode || 'drag'
      }
    };

    // Initialize viewer.
    viewer = new Marzipano.Viewer(panoElement, viewerOpts);
  }

  // Create scenes
  function initScenes() {
    // Clear existing scenes if any
    if (scenes.length > 0) {
      scenes.forEach(function(scene) {
        // Remove hotspots
        scene.scene.hotspotContainer().destroyHotspots();
        // Destroy scene
        scene.scene.destroy();
      });
      scenes = [];
    }

    // Create scenes.
    scenes = data.scenes.map(function(sceneData) {
      var urlPrefix = "product-tiles/" + productKey;
      var source = Marzipano.ImageUrlSource.fromString(
        urlPrefix + "/tile/{z}/{f}/{y}/{x}.jpg",
        { cubeMapPreviewUrl: urlPrefix + "/preview.jpg" });
      var geometry = new Marzipano.CubeGeometry(sceneData.levels);

      var limiter = Marzipano.RectilinearView.limit.traditional(sceneData.faceSize, 100*Math.PI/180, 120*Math.PI/180);
      var view = new Marzipano.RectilinearView(sceneData.initialViewParameters, limiter);

      var scene = viewer.createScene({
        source: source,
        geometry: geometry,
        view: view,
        pinFirstLevel: true
      });

      // Create link hotspots.
      if (sceneData.linkHotspots && Array.isArray(sceneData.linkHotspots)) {
        sceneData.linkHotspots.forEach(function(hotspot) {
          var element = createLinkHotspotElement(hotspot);
          scene.hotspotContainer().createHotspot(element, { yaw: hotspot.yaw, pitch: hotspot.pitch });
        });
      }

      // Create info hotspots.
      if (sceneData.infoHotspots && Array.isArray(sceneData.infoHotspots)) {
        sceneData.infoHotspots.forEach(function(hotspot) {
          var element = createInfoHotspotElement(hotspot);
          scene.hotspotContainer().createHotspot(element, { yaw: hotspot.yaw, pitch: hotspot.pitch });
        });
      }

      return {
        data: sceneData,
        scene: scene,
        view: view
      };
    });

    // Update scene list
    updateSceneList();

    // Display the initial scene.
    if (scenes.length > 0) {
      switchScene(scenes[0]);
    }
  }

  // Update the scene list
  function updateSceneList() {
    // Clear existing scenes in the list
    var scenesList = sceneListElement.querySelector('.scenes');
    while (scenesList.firstChild) {
      scenesList.removeChild(scenesList.firstChild);
    }
    
    // Add new scenes to the list
    scenes.forEach(function(scene) {
      var li = document.createElement('a');
      li.classList.add('scene');
      li.setAttribute('data-id', scene.data.id);
      li.href = 'javascript:void(0)';
      
      var text = document.createElement('li');
      text.classList.add('text');
      text.textContent = scene.data.name;
      
      li.appendChild(text);
      
      li.addEventListener('click', function() {
        switchScene(scene);
        hideSceneList();
      });
      
      scenesList.appendChild(li);
    });
    
    // Update sceneElements
    sceneElements = document.querySelectorAll('#sceneList .scene');
  }

  // Handle product data loading event
  function handleProductDataLoaded(event) {
    data = window.APP_DATA;
    console.log('Product data loaded:', data);
    
    // Initialize viewer if not yet initialized
    initViewer();
    
    // Create scenes
    initScenes();
    
    // Update title
    document.title = data.name || 'Panorama Viewer';
    
    // Setup UI elements based on settings
    setupUI();
  }

  // Register product data loading event listener
  document.addEventListener('productDataLoaded', handleProductDataLoaded);

  // Set up autorotate, if supported
  var autorotate = Marzipano.autorotate({
    yawSpeed: 0.03,
    targetPitch: 0,
    targetFov: Math.PI/2
  });

  // Setup UI elements based on settings
  function setupUI() {
    // Set up autorotate - always enable it
    autorotateToggleElement.classList.add('enabled');
    startAutorotate();

    // Set up fullscreen button - always show if supported
    if (screenfull.enabled) {
      document.body.classList.add('fullscreen-enabled');
      fullscreenToggleElement.style.display = 'block';
    } else {
      document.body.classList.add('fullscreen-disabled');
      fullscreenToggleElement.style.display = 'none';
    }

    // Set up view control buttons - always enable
    document.body.classList.add('view-control-buttons');
    
    // Set up dynamic view controls
    if (viewer) {
      // Dynamic parameters for controls.
      var velocity = 0.7;
      var friction = 3;

      // Associate view controls with elements.
      var controls = viewer.controls();
      controls.registerMethod('upElement', new Marzipano.ElementPressControlMethod(viewUpElement, 'y', -velocity, friction), true);
      controls.registerMethod('downElement', new Marzipano.ElementPressControlMethod(viewDownElement, 'y', velocity, friction), true);
      controls.registerMethod('leftElement', new Marzipano.ElementPressControlMethod(viewLeftElement, 'x', -velocity, friction), true);
      controls.registerMethod('rightElement', new Marzipano.ElementPressControlMethod(viewRightElement, 'x', velocity, friction), true);
      controls.registerMethod('inElement', new Marzipano.ElementPressControlMethod(viewInElement, 'zoom', -velocity, friction), true);
      controls.registerMethod('outElement', new Marzipano.ElementPressControlMethod(viewOutElement, 'zoom', velocity, friction), true);
    }
  }

  function sanitize(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function switchScene(scene) {
    stopAutorotate();
    scene.view.setParameters(scene.data.initialViewParameters);
    scene.scene.switchTo();
    startAutorotate();
    updateSceneName(scene);
    updateSceneList(scene);
  }

  function updateSceneName(scene) {
    sceneNameElement.innerHTML = sanitize(scene.data.name);
  }

  function updateSceneList(scene) {
    for (var i = 0; i < sceneElements.length; i++) {
      var el = sceneElements[i];
      if (el.getAttribute('data-id') === scene.data.id) {
        el.classList.add('current');
      } else {
        el.classList.remove('current');
      }
    }
  }

  function showSceneList() {
    sceneListElement.classList.add('enabled');
    sceneListToggleElement.classList.add('enabled');
  }

  function hideSceneList() {
    sceneListElement.classList.remove('enabled');
    sceneListToggleElement.classList.remove('enabled');
  }

  function toggleSceneList() {
    sceneListElement.classList.toggle('enabled');
    sceneListToggleElement.classList.toggle('enabled');
  }

  function startAutorotate() {
    if (!autorotateToggleElement.classList.contains('enabled') || !viewer) {
      return;
    }
    viewer.startMovement(autorotate);
    viewer.setIdleMovement(3000, autorotate);
  }

  function stopAutorotate() {
    if (!viewer) {
      return;
    }
    viewer.stopMovement();
    viewer.setIdleMovement(Infinity);
  }

  function toggleAutorotate() {
    if (autorotateToggleElement.classList.contains('enabled')) {
      autorotateToggleElement.classList.remove('enabled');
      stopAutorotate();
    } else {
      autorotateToggleElement.classList.add('enabled');
      startAutorotate();
    }
  }

  function createLinkHotspotElement(hotspot) {
    // Create wrapper element to hold icon and tooltip.
    var wrapper = document.createElement('div');
    wrapper.classList.add('hotspot');
    wrapper.classList.add('link-hotspot');

    // Create image element.
    var icon = document.createElement('img');
    icon.src = 'img/link.png';
    icon.classList.add('link-hotspot-icon');

    // Set rotation transform.
    var transformProperties = [ '-ms-transform', '-webkit-transform', 'transform' ];
    for (var i = 0; i < transformProperties.length; i++) {
      var property = transformProperties[i];
      icon.style[property] = 'rotate(' + hotspot.rotation + 'rad)';
    }

    // Add click event handler.
    wrapper.addEventListener('click', function() {
      if (hotspot.target) {
        var targetScene = findSceneById(hotspot.target);
        if (targetScene) {
          switchScene(targetScene);
        }
      }
    });

    // Prevent touch and scroll events from reaching the parent element.
    // This prevents the view from shifting when the hotspot is tapped on touch devices.
    stopTouchAndScrollEventPropagation(wrapper);

    // Create tooltip element.
    var tooltip = document.createElement('div');
    tooltip.classList.add('hotspot-tooltip');
    tooltip.classList.add('link-hotspot-tooltip');
    
    // Find the target scene data and set tooltip text
    var targetSceneData = findSceneDataById(hotspot.target);
    if (targetSceneData) {
      tooltip.innerHTML = sanitize(targetSceneData.name);
    }

    wrapper.appendChild(icon);
    wrapper.appendChild(tooltip);

    return wrapper;
  }

  function createInfoHotspotElement(hotspot) {
    // Create wrapper element to hold icon and tooltip.
    var wrapper = document.createElement('div');
    wrapper.classList.add('hotspot');
    wrapper.classList.add('info-hotspot');

    // Create hotspot/tooltip header.
    var header = document.createElement('div');
    header.classList.add('info-hotspot-header');

    // Create image element.
    var iconWrapper = document.createElement('div');
    iconWrapper.classList.add('info-hotspot-icon-wrapper');
    var icon = document.createElement('img');
    icon.src = 'img/info.png';
    icon.classList.add('info-hotspot-icon');
    iconWrapper.appendChild(icon);

    // Create title element.
    var titleWrapper = document.createElement('div');
    titleWrapper.classList.add('info-hotspot-title-wrapper');
    var title = document.createElement('div');
    title.classList.add('info-hotspot-title');
    title.innerHTML = sanitize(hotspot.title);
    titleWrapper.appendChild(title);

    // Create close element.
    var closeWrapper = document.createElement('div');
    closeWrapper.classList.add('info-hotspot-close-wrapper');
    var closeIcon = document.createElement('img');
    closeIcon.src = 'img/close.png';
    closeIcon.classList.add('info-hotspot-close-icon');
    closeWrapper.appendChild(closeIcon);

    // Construct header element.
    header.appendChild(iconWrapper);
    header.appendChild(titleWrapper);
    header.appendChild(closeWrapper);

    // Create text element.
    var text = document.createElement('div');
    text.classList.add('info-hotspot-text');
    text.innerHTML = sanitize(hotspot.text);

    // Place header and text into wrapper element.
    wrapper.appendChild(header);
    wrapper.appendChild(text);

    // Create a modal for the hotspot content to appear on mobile mode.
    var modal = document.createElement('div');
    modal.innerHTML = wrapper.innerHTML;
    modal.classList.add('info-hotspot-modal');
    document.body.appendChild(modal);

    var toggle = function() {
      wrapper.classList.toggle('visible');
      modal.classList.toggle('visible');
    };

    // Show content when hotspot is clicked.
    wrapper.querySelector('.info-hotspot-header').addEventListener('click', toggle);

    // Hide content when close icon is clicked.
    modal.querySelector('.info-hotspot-close-wrapper').addEventListener('click', toggle);

    // Prevent touch and scroll events from reaching the parent element.
    // This prevents the view from shifting when the hotspot is tapped on touch devices.
    stopTouchAndScrollEventPropagation(wrapper);
    stopTouchAndScrollEventPropagation(modal);

    return wrapper;
  }

  // Prevent touch and scroll events from reaching the parent element.
  function stopTouchAndScrollEventPropagation(element, eventList) {
    var eventList = [ 'touchstart', 'touchmove', 'touchend', 'touchcancel',
                      'wheel', 'mousewheel' ];
    for (var i = 0; i < eventList.length; i++) {
      element.addEventListener(eventList[i], function(event) {
        event.stopPropagation();
      });
    }
  }

  function findSceneById(id) {
    for (var i = 0; i < scenes.length; i++) {
      if (scenes[i].data.id === id) {
        return scenes[i];
      }
    }
    return null;
  }

  function findSceneDataById(id) {
    if (!data || !data.scenes) {
      return null;
    }
    for (var i = 0; i < data.scenes.length; i++) {
      if (data.scenes[i].id === id) {
        return data.scenes[i];
      }
    }
    return null;
  }

  // Set up event handlers for UI elements
  
  // Set handler for autorotate toggle
  autorotateToggleElement.addEventListener('click', toggleAutorotate);
  
  // Set up fullscreen mode, if supported
  if (screenfull.enabled) {
    fullscreenToggleElement.addEventListener('click', function() {
      screenfull.toggle();
    });
    screenfull.on('change', function() {
      if (screenfull.isFullscreen) {
        fullscreenToggleElement.classList.add('enabled');
      } else {
        fullscreenToggleElement.classList.remove('enabled');
      }
    });
  }
  
  // Set handler for scene list toggle
  sceneListToggleElement.addEventListener('click', toggleSceneList);
  
  // Start with the scene list open on desktop
  if (!document.body.classList.contains('mobile')) {
    showSceneList();
  }
  
  // Set up dynamic view controls
  var viewUpElement = document.querySelector('#viewUp');
  var viewDownElement = document.querySelector('#viewDown');
  var viewLeftElement = document.querySelector('#viewLeft');
  var viewRightElement = document.querySelector('#viewRight');
  var viewInElement = document.querySelector('#viewIn');
  var viewOutElement = document.querySelector('#viewOut');
  
  // Set view control event handlers
  if (viewUpElement) {
    viewUpElement.addEventListener('click', function() {
      if (!viewer) return;
      var activeScene = scenes.find(function(scene) {
        return scene.scene._state === 'active';
      });
      if (activeScene) {
        var view = activeScene.view;
        view.setPitch(view.pitch() + Math.PI/10);
      }
    });
  }
  
  if (viewDownElement) {
    viewDownElement.addEventListener('click', function() {
      if (!viewer) return;
      var activeScene = scenes.find(function(scene) {
        return scene.scene._state === 'active';
      });
      if (activeScene) {
        var view = activeScene.view;
        view.setPitch(view.pitch() - Math.PI/10);
      }
    });
  }
  
  if (viewLeftElement) {
    viewLeftElement.addEventListener('click', function() {
      if (!viewer) return;
      var activeScene = scenes.find(function(scene) {
        return scene.scene._state === 'active';
      });
      if (activeScene) {
        var view = activeScene.view;
        view.setYaw(view.yaw() - Math.PI/10);
      }
    });
  }
  
  if (viewRightElement) {
    viewRightElement.addEventListener('click', function() {
      if (!viewer) return;
      var activeScene = scenes.find(function(scene) {
        return scene.scene._state === 'active';
      });
      if (activeScene) {
        var view = activeScene.view;
        view.setYaw(view.yaw() + Math.PI/10);
      }
    });
  }
  
  if (viewInElement) {
    viewInElement.addEventListener('click', function() {
      if (!viewer) return;
      var activeScene = scenes.find(function(scene) {
        return scene.scene._state === 'active';
      });
      if (activeScene) {
        var view = activeScene.view;
        view.setFov(Math.max(view.fov() - Math.PI/10, Math.PI/10));
      }
    });
  }
  
  if (viewOutElement) {
    viewOutElement.addEventListener('click', function() {
      if (!viewer) return;
      var activeScene = scenes.find(function(scene) {
        return scene.scene._state === 'active';
      });
      if (activeScene) {
        var view = activeScene.view;
        view.setFov(Math.min(view.fov() + Math.PI/10, Math.PI));
      }
    });
  }
  
  // Check if data is already loaded (for example, if router hasn't been initialized)
  if (window.APP_DATA) {
    data = window.APP_DATA;
    initViewer();
    initScenes();
    setupUI();
  }
})();
