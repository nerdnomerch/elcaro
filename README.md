# elcaro oracle

_Note: Work in progress. As of now only a hacky prototype is available. No incentivation mechanism for node operators is implemented yet._

The elcaro oracle is a generic decentralised oracle that can be used to trigger arbitrary off-chain script functions that may call on-chain contract methods.

## What?

The implemented prototype can be used trigger the execution of arbitrary Python functions from a smart-contract, where the result of that Python function can be used to call back into a specific contract method.

The execution of the Python script will take place within a network of specific nodes, where a node (or nodes) are selected for the execution of the specified function. After execution the node will finally create a response transaction that will contain the execution result. The result can then be easily accessed within the specified contract method.

As of now, no mechanism was yet implemented to incentivise node operators. 

## How?

As an example we want to call a Python script containing a function `get_price(currency)` that will do a query the current price of that `currency` in `EUR`. We will see how we can trigger the execution of that function from a contract and how the contract is able to access the retrieved price.

### Python Script
Let's at first take a look to a very simple Python script `get_price.py` that defines a function `get_price(currency)`.

```python
def get_price(currency):
    URL = "https://api.coinbase.com/v2/exchange-rates?currency=" + currency
    r = requests.get(url = URL)
    data = r.json()
    print(json.dumps(data, indent=4))
    eur_price = data['data']['rates']['EUR']
    print(currency + ": " + eur_price + " EUR")
    
    return int(decimal.Decimal(eur_price) * 1000)
```

The `get_price(currency)` function will return the current price of the specified currency `currency` in `EUR` by using an API provided by Coinbase.

### Add the script to IPFS

```bash
$ cat get_price.sh
def get_price(currency):
    URL = "https://api.coinbase.com/v2/exchange-rates?currency=" + currency
    r = requests.get(url = URL)
    data = r.json()
    print(json.dumps(data, indent=4))
    eur_price = data['data']['rates']['EUR']
    print(currency + ": " + eur_price + " EUR")
    
    return int(decimal.Decimal(eur_price) * 1000)

$ ipfs add get_price.sh
added QmVLnxTdjKYjYYzuxsfCeULnP3SvikpM9M324Bate98KQM get_price.py
 334 B / 334 B [========================================] 100.00%
```

After adding the script to IPFS, the returned content-identifier `QmVLnxTdjKYjYYzuxsfCeULnP3SvikpM9M324Bate98KQM` can be used to refer to our Python script `get_price.sh`.

### Write a smart-contract

```solidity
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
    
    function query_price(string memory _currency) external payable returns (bool) {
        return Elcaro.request(
            "ipfs://QmVLnxTdjKYjYYzuxsfCeULnP3SvikpM9M324Bate98KQM/get_price(string)", abi.encode(_currency),
            address(this), "update_price(uint256)"
        );
    }
}
```
<sup>1</sup> _The script uses an already deployed `Elcaro` contract. This contract was deployed on the **goerli testnet** at address `0x6a1c553b61db4183640707E9DdE365A6c05DF1C3`._

The contract defines three methods:

- `update_price(uint256 _eur_price)`
This method is just used to update the storage variable `eur_price`.

- `get_price()`
This method just returns the value of the storage variable `eur_price`.

- `query_price(string memory _currency)`
This method will trigger an Elcaro request. This request will be processed by a network of nodes, that are managed by the specified Elcaro contract, e.g. at **goerli testnet** at address `0x6a1c553b61db4183640707E9DdE365A6c05DF1C3`.

Let's take a brief look to the signature of the `request(..)` method.

```solidity
function request(
    string memory request_url, bytes calldata request_arguments, 
    address response_contract, string memory response_method
  ) external payable returns (bool);
```

The `request` method defines the following parameters:

- `request_url`
The parameter `request_url` defines the location of the function that need to be called. In our example we use `ipfs://QmVLnxTdjKYjYYzuxsfCeULnP3SvikpM9M324Bate98KQM/get_price(string)`, where `QmVLnxTdjKYjYYzuxsfCeULnP3SvikpM9M324Bate98KQM` refers to the IPFS content identifier of our Python script `get_price.py`. The path defines what function need to be called within that script. In our case, we want to call the function `get_price(currency)`. In contrast the original function parameter name `currency`, we need to define the types of the parameters that are used: here our parameter `currency` is of type `string`. This information is used by the processing node to decode the supplied parameters correctly. 

- `request_arguments`
The parameter `request_arguments` contains the parameters that need to be used to call the Python function. As you can see, `request_arguments` is just an `bytes` array. The supplied parameters need to be _ABI encoded_. If you look to our example contract again, `abi.encode(..)` is used to encode the function arguments into the needed `bytes` array.

- `response_contract`
The argument `response_contract` defines the address of the contract that shall receive the response of the defined request.

- `response_method`
The `response_method` argument refers to the method signature of the method that should be called. The contract address defined by `response_contract`.

After calling `Elcaro.request` a request will be send to a network of nodes. A request will be processed by exactly one selected node of the network. This node will be responsible to create the response transaction that contains the result of the executed Python function.

So in our case after executing the contract method `query_price(..)` the defined callback `update_price(uint256 _eur_price)` will be called, where `_eur_price` will contain the result of the execution of the Python function `get_price(currency)` defined within the script `get_price.py`. 

## Running a node

### Docker image

A simple docker image was prepared that contains `ipfs` and `geth`. `geth` is preconfigured to use the goerli testnet as a light client. Additionally a simple text-based ui can be used to manage the elcaro node.

```docker
docker run --rm -it aarlt/elcaro:develop
```

#### Login

The private key of the node will be derived from the username-password pair that you will enter. That means, if you use a weak username-password pair someone else may have control over the node.

```text
$ docker run --rm -it aarlt/elcaro:develop

                          .__
                     ____ |  |   ____ _____ _______  ____
                   _/ __ \|   _/ ___\\__  \\_   __ \/  _ \
                   \  ___/|  |_\  \___ / __ \|  | \(  <_> )
                    \___  >____/\___  >____  /__|   \____/
                        \/          \/     \/

     ATTENTION  The private key of the node will be derived from
                the username and the password you enter. That means,
                if you use a weak username-password pair others may
                be able to access the node account.

 !! THIS IS HIGHLY EXPERIMENTAL SOFTWARE AND TO BE USED AT YOUR OWN RISK !!

 - Login:
 - Password:
```

#### Funding your node

After logging in, your node address will be shown. To be able to register your node you will need to send some balance to your node address. As already described, the node will synchronise with the goerli testnet. To get some test ethers, you can use a faucet like [goerli-faucet.slock.it](https://goerli-faucet.slock.it/).

```
       .__
    ____ |  |   ____ _____ _______  ____
  _/ __ \|   _/ ___\\__  \\_   __ \/  _ \
  \  ___/|  |_\  \___ / __ \|  | \(  <_> )
   \___  >____/\___  >____  /__|   \____/
       \/          \/     \/
     Chain          Peers          Block
       5              0             #0
                  Contract
 0x6a1c553b61db4183640707E9DdE365A6c05DF1C3
  Active Nodes     Requests      Responses
       ?              ?              ?
                    Node
 0xB78E6e12549e701A37aD3c89C102ee26022cC504  <<<<<<<<<<<< NODE ADDRESS
    Balance        Requests      Responses
       ?              ?              ?

< One Request ><             ><  F8|Exit   >
< Encoding    >
 21 < Req(s). >
```


You will need to wait until your node is synchronised with the test-net. If you received the fundings, your node can get registered by using the `Register` button. This button will only be visible if you're fully synchronised with the network. 

### How does it work?

This section will describe the whole system in more detail. The interface to an Elcaro contract is defined in [`IElcaro.sol`](https://github.com/aarlt/elcaro/blob/develop/truffle/contracts/IElcaro.sol). Also see the prototype implementation of [`Elcaro.sol`](https://github.com/aarlt/elcaro/blob/develop/truffle/contracts/Elcaro.sol).

#### Node Registration

The contract defines two functions that are responsible for registration or unregistration of a particular node.

```solidity
function register() external payable returns (bool);
function unregister() external returns (bool);
```

Both functions use `tx.origin` to identify the corresponding caller. OpenZeppelin's [EnumerableSet.sol](https://github.com/aarlt/elcaro/blob/develop/truffle/contracts/EnumerableSet.sol) is used to keep track of the registered nodes. A node can only be registered once. All registered nodes are items within an `EnumerableSet` called `nodes`.

#### Request Events

As already described, a request contains a `request_url`,  `request_arguments`, `response_contract` and `response_method`.  Additionally to these parameters `block.number`, `tx.origin` and `msg.sender` will be used to calculate the `request_hash`.

```solidity
bytes memory data = abi.encode(request_url, request_arguments, response_contract, response_method, block.number, tx.origin, msg.sender);
bytes32 request_hash = keccak256(data);
```

##### Node selection

The `request_hash` will be used to specify the node that is responsible for serving the request. This is done by calculating the `request_hash` modulo the length of the registered nodes array `nodes`. 

```solidity
address responsible_node = nodes.at(uint256(request_hash) % nodes.length());
```

To ensure that the contract will be able to identify what node was responsible for what request, the `requests` mapping is used to keep track of responsible nodes. `

```solidity
requests[request_hash] = responsible_node;
```

##### Request Event Creation

Finally the request event `onRequest` is emitted that contains the address of responsible node, the request hash and the data of the request.

```solidity
emit onRequest(responsible_node, request_hash, data);
```

#### Listening to Request Events

A node will continuously listening to all `onRequest` events that the contract is emitting. A particular node will get active, if its node address is the same as the `responsible_node` defined within the `onRequest` event.

#### Script execution 

If a node detects a request event that need to be fulfilled by the node itself, it will at first extract all needed information from the event data. The extraction will reveal `request_url`,  `request_arguments`, `response_contract` and `response_method`. The request url `request_url` will be analysed. Right now only IPFS is supported. However, the node will then extract the content-identifier of the script and the function that need to be executed. The node will download the data corresponding to the content-identifier. The supplied `request_arguments` will be extracted by _ABI decoding_ the supplied bytes with the types defined in the function definition (e.g. in the context of our example it's `string`, because of `get_price(string)` because of `ipfs://QmVLnxTdjKYjYYzuxsfCeULnP3SvikpM9M324Bate98KQM/get_price(string)`).

So the Python function `get_price(currency)` will get called, where the type of `currency` is `string`. After _ABI decoding_ of the `request_arguments` corresponding to the defined types. We call the `get_price` function with the corresponding argument value. 

The result of this function will be _ABI encoded_ with the types defined in the `response_method`. In the context of our example `response_method="update_price(uint256)"`, so the result value will be _ABI encoded_ as an `uint256`.

#### Response Transactions

After a successful execution of the defined Python function, a node will create a response transaction that will call back into the elcaro contract, that will finally call the contract method defined within the corresponding request.

```solidity
function response(bytes memory _request, bytes memory _response, string memory stdout, string memory stderr) external returns (bool);
```

To save expensive storage, the node supplies all information used by the original request `_request`. The method will then calculate the hash of the supplied request data. If the request data was initially defined by a real request, the hash must be a known request hash, wherefore the supplied request data can be trusted. Only responses will be accepted, if they where sent by exactly the node that initially selected to serve the request.

```solidity
function response(bytes memory _request, ..) external override returns (bool) {
        bytes32 hash = keccak256(_request);
        if (requests[hash] == tx.origin) {
           ...
        }
        return false;
 }
```

The contract will then extract the response contract address `response_contract` and the response method `response_method` from the supplied `_request` parameter.

```solidity
(,,address response_contract, string memory response_method,,,) =
                abi.decode(_request, (string, bytes, address, string, uint256, address, address));
```

Now the function selector need to get calculated.

```solidity
bytes4 selector = bytes4(keccak256(bytes(response_method)));
```

The call data need to get prepared.

```solidity
bytes memory data = new bytes(4 + _response.length);
data[0] = selector[0];
data[1] = selector[1];
data[2] = selector[2];
data[3] = selector[3];         
for (uint i = 0; i < _response.length; ++i) {
  data[4 + i] = _response[i];
}
```

Remember that `_response` is already the _ABI encoded_ version of the returned script function result.

Now we just need to call the defined contract method `response_method` on a contract at address `response_contract`.

```solidity
(bool status,) = contract_address.call(data);
```

If the call was successful, the elcaro contract will emit an `onResponse` event.

```solidity
if (status) {
  emit onResponse(tx.origin, hash, contract_address, callback, _response, stdout, stderr);
}
```

One thing to mention here, `stdout` and `stderr` is pointing to the IPFS content-identifier of `stdout` and `stderr` that was produced during the script execution. This makes it very easy to investigate the script function execution: `ipfs cat <content-hash>`.

```text
$ ipfs cat QmcdRSRKZ1oXsrCEy61Zwj68nWBAa77ShZoiekQxoEVj12
// elcaro execution log [stdout]
// ipfs://QmSLj7iKnDpDjGog7NddFgUs6ebKr5AxxwXAUZvmGVuAUP/hello_world(string)['das ist ein test'] -> Hello das ist ein test!
Hello das ist ein test

$ ipfs cat QmTfY9N1SFivnShrTepqnyDzkfxkPR97GjipakYUiSpA6G
// elcaro execution log [stderr]
// get_tuple[23, 'Hello'] -> [23, 'Hello']
```

## Gas measurements

No gas optimisation was done yet. Also the gas costs presented here may change with the corresponding payload size - e.g. size of request parameters, size of response result. Also the complexity of the final response method will have impact on the gas cost.

| Operation | Gas Cost |
|-----------|----------|
| `register a node`  | `86.845 gas` |
| `unregister a node`  | `23.105 gas` |
| `sending a request` | `62.470 gas` |
| `sending a response` |  `40.831 gas` |
| `sending a multi-request for 21 nodes` | `773.204 gas -> 36.819 gas/node `|
| `sending a multi-request for 100 nodes` | `3.495.860 gas -> 34.958 gas/node` |

## Random Notes

### TODO 

- additionally realise the node management & communication off-chain. With this arbiritrary off-chain services may be able trigger on-chain requests. This may be particularly interesting to enable meta-transactions. Also simple alarm-clock services could be implemented - e.g. "please call my contract method every day once".

- rewrite node implementation (and of course the scripting language engine) in a language that can be compiled to wasm. with this a node could run in a web browser.

- some events can be simplified. No need for manual encoding/decoding.

- add a mechanism to incentivise node operators.

- add node implementation that does not have any UI.

- responses can only refer to contracts that where deployed on a network that a particular node is using. The response should also become an URL. With this it may be possible to refer to different systems where the response should be send. E.g. `goerli://0x6a1c553b61db4183640707E9DdE365A6c05DF1C3/update_price(uint256)` or `mailto:what@example.com`_

- add support for multiple blockchain networks at the same time. With this contracts on one network e.g. a goerli testnet contract could trigger contracts on the kotti testnet.

- implement `request_n(..)` with result aggregation and support of different aggregation strategies. To enable redundant execution by multiple nodes - one request that will be processed by the defined number of nodes - `Elcaro.request_n(..)` could be used. In addition to the parameters defined by `Elcaro.request(..)` the number of nodes can be defined that need to execute the request. A very simple version of `Elcaro.request_n(..)` is implemented, but the node implementation is not yet fully ready. Also the aggregation of multiple results within the Elcaro contract and aggregation strategies are not yet implemented. 

- the current prototype is just a hack and can be improved drastically. The prototype helped to identify different mechanisms. With this knowledge a clean implementation should be done.

- the used scripting language _Python_ may be too dangerous to be used in a productive environment - languages that where designed to get embedded like _Lua_ or _JavaScript_ are probably better suited doing this. There are also specific _Python_ interpreter implementations available that could be interesting. 

### Chainlink

- https://medium.com/@chainlinkgod/scaling-chainlink-in-2020-371ce24b4f31

    - "Currently, it costs about 2,374,048 gas (\$41.71) to request a price update from a network of 21 oracle nodes"

    - "Currently, the cost from all 21 nodes responding with data back on-chain is 1,358,377 gas (\$23.87), with an average cost of 64,684 gas per node (\$1.14)."
