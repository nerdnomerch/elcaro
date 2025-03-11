// SPDX-License-Identifier: MIT
pragma solidity 0.7.0;

interface OwnedInterface {
    function getOwner() external view returns(address owner);
    function changeOwner(address newOwner) external returns (bool success);
}

contract Owned is OwnedInterface {
    
    address private contractOwner;
  
    event LogOwnerChanged(
        address newOwner);

    modifier onlyOwner {
        require(msg.sender == contractOwner);
        _;
    } 
  
    constructor() {
        contractOwner = msg.sender;
    }

    function getOwner() public override view returns(address owner) {
        return contractOwner;
    }
  
    function changeOwner(address newOwner) 
        public
        override
        onlyOwner 
        returns(bool success) 
    {
        require(newOwner != address(0));
        emit LogOwnerChanged(newOwner);
        contractOwner = newOwner;
        return true;
    }
}
