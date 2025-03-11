// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.7.0;
pragma experimental ABIEncoderV2;

import "./IElcaro.sol";

contract UserContract {
    IElcaro Elcaro;
    
    constructor(address elcaro) {
        Elcaro = IElcaro(elcaro);
    }

    event HelloWorld(string);
    event GetUint256(uint256);
    event GetString(string);
    event GetTupleStringUint256(string, uint256);
    event GetTupleUint256String(uint256, string);

    function hello_world(string memory _data) external {
        emit HelloWorld(_data);
    }
    
    function getUint256(uint256 _data) external {
        emit GetUint256(_data);
    }

    function getString(string memory _data) external {
        emit GetString(_data);
    }

    function getTupleStringUint256(string memory _data0, uint256 _data1) external {
        emit GetTupleStringUint256(_data0, _data1);
    }

    function getTupleUint256String(uint256 _data0, string memory _data1) external {
        emit GetTupleUint256String(_data0, _data1);
    }

    function test_hello_world() external payable returns (bool) {
        return Elcaro.request(
            "ipfs://Qmat7MMWMt6vthLJXeAngRYyuMGU3Fq1La4Ui8e2yiMLkr/hello_world(string)", abi.encode("Alex"),
            address(this), "hello_world(string)"
        );
    }

    function test_get_uint256() external payable returns (bool) {
        return Elcaro.request(
            "ipfs://Qmat7MMWMt6vthLJXeAngRYyuMGU3Fq1La4Ui8e2yiMLkr/get(uint256)", abi.encode(1),
            address(this), "getUint256(uint256)"
        );
    }

    function test_get_string() external payable returns (bool) {
        return Elcaro.request(
            "ipfs://Qmat7MMWMt6vthLJXeAngRYyuMGU3Fq1La4Ui8e2yiMLkr/get(string)", abi.encode("Hello"),
            address(this), "getString(string)"
        );
    }

    function test_get_tuple_uint256_string() external payable returns (bool) {
        return Elcaro.request(
            "ipfs://Qmat7MMWMt6vthLJXeAngRYyuMGU3Fq1La4Ui8e2yiMLkr/get_tuple(uint256,string)", abi.encode(23, "Hello"),
            address(this), "getTupleUint256String(uint256,string)"
        );
    }

    function test_get_tuple_string_uint256() external payable returns (bool) {
        return Elcaro.request(
            "ipfs://Qmat7MMWMt6vthLJXeAngRYyuMGU3Fq1La4Ui8e2yiMLkr/get_tuple(string,uint256)", abi.encode("Hello", 23),
            address(this), "getTupleStringUint256(string,uint256)"
        );
    }

    function test_n(uint256 count) external payable returns (bool) {
        return Elcaro.request_n(
            count,
            "ipfs://Qmat7MMWMt6vthLJXeAngRYyuMGU3Fq1La4Ui8e2yiMLkr/get(uint256)", abi.encode(count),
            address(this), "getUint256(uint256)"
        );
    }
}
