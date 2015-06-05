'use strict';

var gabblerControllers =
angular.module(
    'gabbler.controllers',
    [
    'gabbler.services'
    ]
    );

gabblerControllers.controller('ParserCmdCtrl', ['$scope', 'ParserCmd', '$sce', '$http', function($scope, ParserCmd, $sce, $http) {

  $scope.parser_cmd = new ParserCmd({ 'text': '' });
  var old_parser_cmd = ""
  $scope.results = null;

  /////// speech-related code

  var icons = {
    start: 'img/mic.png',
    recording: 'img/mic-animate.gif',
    blocked: 'img/mic-slash.png'
  };

  var messages = {
    info_speak_now: 'Speak now... or click on the microphone again to cancel',
    info_stop: 'Proccessing your voice...',
    info_no_speech: 'No Speech was detected. You may need to adjust your <a href="//support.google.com/chrome/bin/answer.py?hl=en&amp;answer=1407892">microphone settings</a>.',
    info_no_mic: 'No microphone was found. Ensure that a microphone is installed.',
    info_blocked: 'Permission to use microphone is blocked. To change, go to <a href="chrome://settings/contentExceptions#media-stream">chrome://settings/contentExceptions#media-stream</a>.',
    info_denied: 'Permission to use microphone was denied.',
    info_setup: 'Click on the microphone icon to enable Web Speech.',
    info_upgrade: 'Web Speech API is not supported by this browser. Upgrade to <a href="//www.google.com/chrome" target="_blank">Chrome</a> version 25 or later.',
    info_allow: 'Click the "Allow" button above to enable your microphone.'
  };

  var first_char = /\S/;
  var init, onresult, onstart, recognition, recognizing, reset, safeApply, setIcon, setMsg, upgrade, capitalize, clearCache;

  recognizing = false;
  recognition = null;
  $scope.speech = {
    msg: messages.info_setup,
    icon: icons.start,
    recognizing: false,
    confidence: 0.0,
    isFinal: false
  };
  capitalize = function(s) {
    return s.replace(first_char, function(m) {
      return m.toUpperCase();
    });
  };
  safeApply = function(fn) {
    var phase;
    phase = $scope.$root.$$phase;
    if (phase === "$apply" || phase === "$digest") {
      if (fn && (typeof fn === "function")) {
        return fn();
      }
    } else {
      return $scope.$apply(fn);
    }
  };
  setMsg = function(msg) {
    return safeApply(function() {
      return $scope.speech.msg = $sce.trustAsHtml(messages[msg]);
    });
  };
  setIcon = function(icon) {
    return safeApply(function() {
      return $scope.speech.icon = icons[icon];
    });
  };

  clearCache = function() {
    $http.get('/clearcache');
  };

  init = function() {
    clearCache();
    reset();
    if ('webkitSpeechRecognition' in window) {
      recognition = new webkitSpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.onerror = onerror;
      recognition.onend = reset;
      recognition.onresult = onresult;
      return recognition.onstart = onstart;
    } else {
      recognition = {};
      return upgrade();
    }
  };
  upgrade = function() {
    setMsg('info_upgrade');
    return setIcon('blocked');
  };
  onstart = function(event) {
    var onerror;
    setIcon('recording');
    setMsg('info_speak_now');
    console.log('onstart', event);
    return onerror = function(event, message) {
      console.log('onerror', event, message);
      switch (event.error) {
        case "not-allowed":
          return setMsg('info_blocked');
        case "no-speech":
          return setMsg('info_no_speech');
        case "service-not-allowed":
          return setMsg('info_denied');
        default:
          return console.log(event);
      }
    };
  };
  onresult = function(event) {
    var i, result, resultIndex, trans, _results;
    setIcon('recording');
    setMsg('info_speak_now');
    resultIndex = event.resultIndex;
    trans = '';
    i = resultIndex;
    _results = [];
    console.log(event);
    safeApply(function() {
      return $scope.speech.interimResults = event.results[resultIndex][0];
    });
    while (i < event.results.length) {
      result = event.results[i][0];
      // trans = capitalize(result.transcript);
      trans = result.transcript;
      safeApply(function() {
        // $scope.speech.interimResults = trans;
        $scope.speech.confidence = event.results[i][0].confidence;
        $scope.speech.isFinal = event.results[i].isFinal;
        return $scope.speech.value = trans;
      });
      if (event.results[i].isFinal) {
        $scope.sendSpeechParserCmd(true);
        safeApply(function() {
          $scope.toggleStartStop();
          return $scope.speech.value = trans;
        });
      }
      _results.push(++i);
    }
    return _results;
  };
  reset = function(event) {
    console.log('reset', event);
    $scope.speech.recognizing = false;
    setIcon('start');
    setMsg('info_setup');
    return $scope.abort = function() {
      return $scope.toggleStartStop();
    };
  };
  $scope.toggleStartStop = function() {
    if ($scope.speech.recognizing) {
      recognition.stop();
      return reset();
    } else {
      recognition.start();
      $scope.speech.recognizing = true;
      return setIcon('blocked');
    }
  };

  $scope.speech = {
    continuous: true,
    interimResults: true,
    value: ''
  }

  init();

  $scope.sendSpeechParserCmd = function(is_final, text) {
    var text_save = text || $scope.speech.value.trim();
    if ($scope.speech.value.length > 0 && old_parser_cmd !== $scope.speech.value) {
      // angular-json-human sometimes acts funny, we first clear it before setting a value
      $scope.parse_tree = null;
      // send out POST request
      $scope.parser_cmd = new ParserCmd({'text': text_save, 
        "incremental": $scope.incremental, "is_final": is_final});
      $scope.parser_cmd.$save({}, function(response, headers) {
        // alert(JSON.stringify(response));
        $scope.results = response.data;
        // $scope.parse_tree = JSON.stringify(JSON.parse(response.tree), undefined, 2);
        $scope.parse_tree = response.tree;
        // console.log($scope.parse_tree);
        // $scope.speech.value = old_parser_cmd;
      });

      $scope.speech.value = text_save;
      // every time we send a parser_cmd, clear the current responses
      $scope.color_results = null;
      old_parser_cmd = $scope.speech.value;
    }
  };

  $scope.keyPress = function(keyCode){
    // when space key is pressed, send to parse
    // originally we used "keyCode == ' '.charCodeAt(0))" to detect spaces,
    // but if the user types too fast, $scope.speech.value will have changed.
    // so now we detect by the last char of $scope.speech.value
    var text = $scope.speech.value;
    if ($scope.incremental && text && text.length > 0 && text.slice(-1) === " ") {
      // console.log(text);
      $scope.sendSpeechParserCmd(false, text);
    };
  };

  $scope.incrementalClicked = function() {
    clearCache();
  };

}]);

function HeaderController($scope, $location) 
{ 
  function endsWith(str, suffix) {
    return str.indexOf(suffix, str.length - suffix.length) !== -1;
  }

  $scope.isActive = function (viewLocation) { 
    // return viewLocation === $location.path();
    return endsWith($location.path(), viewLocation);
  };
}

