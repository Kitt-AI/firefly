'use strict';

var gabbler =
  angular.module(
    'gabbler',
    [
      'gabbler.services',
      'gabbler.controllers',
      'ngRoute',
      'yaru22.jsonHuman'
    ]
  );

gabbler.config(['$routeProvider', function($routeProvider) {
  $routeProvider // .when('/', { templateUrl: 'partials/home.html', controller: 'HomeCtrl' })
    .when('/', { templateUrl: 'partials/lightparser.html'})
    .when('/lightparser', { templateUrl: 'partials/lightparser.html'})
    .otherwise({ redirectTo: '/' });
}])
.filter('unsafe', function($sce) { return $sce.trustAsHtml; });
