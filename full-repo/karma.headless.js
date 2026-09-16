const base = require('./karma.conf.js');
module.exports = function (config) {
  base(config);
  config.set({
    browsers: ['ChromeHeadlessNoSandbox'],
    customLaunchers: { ChromeHeadlessNoSandbox: { base: 'ChromeHeadless', flags: ['--no-sandbox', '--disable-gpu'] } },
    singleRun: true,
  });
};
