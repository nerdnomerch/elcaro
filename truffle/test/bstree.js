const HitchensOrderStatisticsTree = artifacts.require("HitchensOrderStatisticsTree");

contract('HitchensOrderStatisticsTree', function(accounts) {
  it("root() empty", function() {
    return HitchensOrderStatisticsTree.deployed().then(function(instance) {
      return instance.treeRootNode();
    }).then(function(root) {
      assert.equal(root.valueOf(), 0, "root was not empty.");
    });
  });

  it("insert some values", function() {
    return HitchensOrderStatisticsTree.deployed().then(function(instance) {
      instance.insertKeyValue("0x00", 2);
      instance.insertKeyValue("0x00", 3);
      instance.insertKeyValue("0x00", 5);
      instance.insertKeyValue("0x00", 110);
      instance.insertKeyValue("0x00", 130);
      instance.insertKeyValue("0x00", 170);
      return instance.treeRootNode();
    }).then(function(root) {
      assert.equal(root.valueOf(), 3, "root was not empty.");
    });
  });

  it("nextMatch(1)", function() {
    return HitchensOrderStatisticsTree.deployed().then(function(instance) {
      return instance.nextMatch(1);
    }).then(function(root) {
      assert.equal(root.valueOf(), 2, "root was not empty.");
    });
  });
  it("nextMatch(2)", function() {
    return HitchensOrderStatisticsTree.deployed().then(function(instance) {
      return instance.nextMatch(2);
    }).then(function(root) {
      assert.equal(root.valueOf(), 2, "root was not empty.");
    });
  });
  it("nextMatch(3)", function() {
    return HitchensOrderStatisticsTree.deployed().then(function(instance) {
      return instance.nextMatch(3);
    }).then(function(root) {
      assert.equal(root.valueOf(), 3, "root was not empty.");
    });
  });
  it("nextMatch(10)", function() {
    return HitchensOrderStatisticsTree.deployed().then(function(instance) {
      return instance.nextMatch(10);
    }).then(function(root) {
      assert.equal(root.valueOf(), 110, "root was not empty.");
    });
  });
  it("nextMatch(140)", function() {
    return HitchensOrderStatisticsTree.deployed().then(function(instance) {
      return instance.nextMatch(140);
    }).then(function(root) {
      assert.equal(root.valueOf(), 130, "root was not empty.");
    });
  });
  it("nextMatch(180)", function() {
    return HitchensOrderStatisticsTree.deployed().then(function(instance) {
      return instance.nextMatch(180);
    }).then(function(root) {
      assert.equal(root.valueOf(), 170, "root was not empty.");
    });
  });
  it("nextMatch(18220)", function() {
    return HitchensOrderStatisticsTree.deployed().then(function(instance) {
      return instance.nextMatch(18220);
    }).then(function(root) {
      assert.equal(root.valueOf(), 170, "root was not empty.");
    });
  });
});
