'use strict';

var gabblerServices =
  angular.module(
    'gabbler.services',
    [
      'ngResource',
      'ui.bootstrap'
    ]
  );


gabblerServices.factory(
  'ParserCmd',
  ['$resource', function($resource) {
    return $resource('lightparser');
  }]);
