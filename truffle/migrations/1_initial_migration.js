const Migrations = artifacts.require("Migrations");
const HitchensOrderStatisticsTreeLib = artifacts.require("HitchensOrderStatisticsTreeLib")
const HitchensOrderStatisticsTree = artifacts.require("HitchensOrderStatisticsTree")

module.exports = function (deployer) {
  deployer.deploy(Migrations);
  deployer.deploy(HitchensOrderStatisticsTreeLib);
  deployer.link(HitchensOrderStatisticsTreeLib, HitchensOrderStatisticsTree);
  deployer.deploy(HitchensOrderStatisticsTree);
};
