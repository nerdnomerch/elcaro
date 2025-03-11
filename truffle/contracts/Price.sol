// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.7.0;
pragma experimental ABIEncoderV2;

import "./IElcaro.sol";

contract Price {
    IElcaro Elcaro = IElcaro(0x6a1c553b61db4183640707E9DdE365A6c05DF1C3);
    
    uint256 eur_price;

    function get_price() external view returns (uint256)  {
        return eur_price;
    }
    
    function update_price(uint256 _eur_price) external {
        eur_price = _eur_price;
    }
    
    function query_price(string memory name) external payable returns (bool) {
        return Elcaro.request(
            "ipfs://QmVLnxTdjKYjYYzuxsfCeULnP3SvikpM9M324Bate98KQM/get_price(string)", abi.encode(name),
            address(this), "update_price(uint256)"
        );
    }
}
