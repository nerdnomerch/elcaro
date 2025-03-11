// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.7.0;
pragma experimental ABIEncoderV2;

import "./Owned.sol";
import "./EnumerableSet.sol";
import "./IElcaro.sol";

contract Elcaro is Owned, IElcaro {
    using EnumerableSet for EnumerableSet.AddressSet;
    EnumerableSet.AddressSet private nodes;

    mapping(bytes32 => address) requests;
    mapping(bytes32 => address[]) multi_requests;

    // node management
    function register() external payable override returns (bool) {
        if (nodes.add(tx.origin) == true)
        {
            emit onRegister(tx.origin, nodes.length());
            return true;
        }
        return false;
    }

    function unregister() external override returns (bool) {
        if (nodes.remove(tx.origin) == true)
        {
            emit onUnregister(tx.origin, nodes.length());
            return true;
        }
        return false;
    }

    function nodeCount() view public override returns (uint256) {
        return nodes.length();
    }

    function isRegistered(address _id) view public override returns (bool) {
        return nodes.contains(_id);
    }

    function request(string memory _function, bytes calldata _arguments, address _contract, string memory _callback) external payable override returns (bool) {
        bytes memory data = abi.encode(_function, _arguments, _contract, _callback, block.number, tx.origin, msg.sender);
        bytes32 _hash = keccak256(data);
        address _nearestNode = nodes.at(uint256(_hash) % nodes.length());
        requests[_hash] = _nearestNode;
        emit onRequest(_nearestNode, _hash, data);
        return true;
    }

    function request_n(uint256 _count, string memory _function, bytes calldata _arguments, address _contract, string memory _callback) external payable override returns (bool) {
        bytes memory data = abi.encode(_function, _arguments, _contract, _callback, block.number, tx.origin, msg.sender);
        bytes32 hash = keccak256(data);
        for (uint i = 0; i < _count; ++i) {
            address _nearestNode = nodes.at((uint256(hash) + i) % nodes.length());
            multi_requests[hash].push(_nearestNode);
            emit onMultiRequest(_nearestNode, hash, i, _count, data);
        }
        return true;
    }

    function response(bytes memory _request, bytes memory _response, string memory stdout, string memory stderr) external override returns (bool) {
        bytes32 hash = keccak256(_request);
        if (requests[hash] == tx.origin) {
            delete requests[hash];

            (,,address contract_address, string memory  callback,,,) =
                abi.decode(_request, (string, bytes, address, string, uint256, address, address));

            bytes memory data = new bytes(4 + _response.length);
            bytes4 selector = bytes4(keccak256(bytes(callback)));

            data[0] = selector[0];
            data[1] = selector[1];
            data[2] = selector[2];
            data[3] = selector[3];
            
            for (uint i = 0; i < _response.length; ++i) {
                data[4 + i] = _response[i];
            }

            // (bool status,) = contract_address.call(abi.encodeWithSignature(callback, _response));
            (bool status,) = contract_address.call(data);

            if (status) {
                emit onResponse(tx.origin, hash, contract_address, callback, _response, stdout, stderr);
            }

            return status;
        }
        return false;
    }
}
