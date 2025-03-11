// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.7.0;
pragma experimental ABIEncoderV2;

interface IElcaro {
    // events
    event onRequest(address indexed node_account, bytes32 indexed request_hash, bytes data);
    event onMultiRequest(address indexed node_account, bytes32 indexed request_hash, uint256 index, uint256 count, bytes data);
    event onRegister(address indexed node_account, uint256 node_count);
    event onUnregister(address indexed node_account, uint256 node_count);
    event onResponse(address indexed node_account, bytes32 indexed request_hash, address contract_address, string signature, bytes data, string stdout, string stderr);

    // node management
    function register() external payable returns (bool);
    function unregister() external returns (bool);
    function nodeCount() external view returns (uint256);
    function isRegistered(address _id) external view returns (bool);

    // requests
    function request(string memory _function, bytes calldata _arguments, address _contract, string memory _callback) external payable returns (bool);
    function request_n(uint256 count, string memory _function, bytes calldata _arguments, address _contract, string memory _callback) external payable returns (bool);

    // responses
    function response(bytes memory _request, bytes memory _response, string memory stdout, string memory stderr) external returns (bool);
}
