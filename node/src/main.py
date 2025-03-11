import argparse
import getpass
import hashlib
import json
import os
import queue
import threading
import time

from concurrent.futures import ThreadPoolExecutor

import eth_abi
import urwid
from passlib.hash import argon2
from web3 import Web3

from watcher import Watcher

elcaro_logo = u'         .__\n' \
              '    ____ |  |   ____ _____ _______  ____\n' \
              '  _/ __ \\|   _/ ___\\\\__  \\\\_   __ \\/  _ \\ \n' \
              '  \\  ___/|  |_\\  \\___ / __ \\|  | \\(  <_> )\n' \
              '   \\___  >____/\\___  >____  /__|   \\____/\n' \
              '       \\/          \\/     \\/'

elcaro_logo_centered = u'                          .__\n' \
                       '                     ____ |  |   ____ _____ _______  ____\n' \
                       '                   _/ __ \\|   _/ ___\\\\__  \\\\_   __ \\/  _ \\ \n' \
                       '                   \\  ___/|  |_\\  \\___ / __ \\|  | \\(  <_> )\n' \
                       '                    \\___  >____/\\___  >____  /__|   \\____/\n' \
                       '                        \\/          \\/     \\/'


class ViewTerminal(urwid.Terminal):
    _selectable = False


class EventViewer(urwid.WidgetWrap):
    def __init__(self, elcaro):
        self.list = urwid.SimpleListWalker([])
        self.listbox = urwid.ListBox(self.list)
        self.body = urwid.AttrWrap(self.listbox, 'body')
        self.__super.__init__(urwid.AttrWrap(self.body, 'chars'))


class SidePanel(urwid.WidgetWrap):
    def __init__(self, elcaro):
        self.elcaro = elcaro
        self.logo = urwid.Text(('logo', elcaro_logo))
        self.network_block_title = urwid.Text(('network title', u"Block..."), align=urwid.CENTER)

        self.network_chain_id = urwid.Text(('network', u"?"), align=urwid.CENTER)
        self.network_peers = urwid.Text(('network', u"?"), align=urwid.CENTER)
        self.network_block = urwid.Text(('network', u"?"), align=urwid.CENTER)

        self.active_nodes = urwid.Text(('contract', u"?"), align=urwid.CENTER)
        self.contract_address = urwid.Text(('contract', self.elcaro.config.contract), align=urwid.CENTER)
        self.contract_requests = urwid.Text(('contract', u"?"), align=urwid.CENTER)
        self.contract_responses = urwid.Text(('contract', u"?"), align=urwid.CENTER)

        self.node_address = urwid.Text(('node', self.elcaro.account.address), align=urwid.CENTER)
        self.node_requests = urwid.Text(('node', u"?"), align=urwid.CENTER)
        self.node_responses = urwid.Text(('node', u"?"), align=urwid.CENTER)
        self.node_balance = urwid.Text(('node', u"?"), align=urwid.CENTER)

        self.register_unregister_button = urwid.Button(('button', " Register  "), self.elcaro.register_unregister)
        self.pile = urwid.Pile([
            self.logo,
            urwid.Columns(
                [
                    urwid.Pile([urwid.Text(('network title', u"Chain"), align=urwid.CENTER),
                                self.network_chain_id]),
                    urwid.Pile([urwid.Text(('network title', u"Peers"), align=urwid.CENTER),
                                self.network_peers]),
                    urwid.Pile([self.network_block_title,
                                self.network_block]),
                ]),
            urwid.Text(('contract title', u"Contract"), align=urwid.CENTER),
            self.contract_address,
            urwid.Columns(
                [
                    urwid.Pile([urwid.Text(('contract title', u"Active Nodes"), align=urwid.CENTER),
                                self.active_nodes]),
                    urwid.Pile([urwid.Text(('contract title', u"Requests"), align=urwid.CENTER),
                                self.contract_requests]),
                    urwid.Pile([urwid.Text(('contract title', u"Responses"), align=urwid.CENTER),
                                self.contract_responses]),
                ]),
            urwid.Text(('node title', u"Node"), align=urwid.CENTER),
            self.node_address,
            urwid.Columns(
                [
                    urwid.Pile([urwid.Text(('node title', u"Balance"), align=urwid.CENTER),
                                self.node_balance]),
                    urwid.Pile([urwid.Text(('node title', u"Requests"), align=urwid.CENTER),
                                self.node_requests]),
                    urwid.Pile([urwid.Text(('node title', u"Responses"), align=urwid.CENTER),
                                self.node_requests]),
                ],
            ),
            urwid.Text(""),
            urwid.Columns(
                [
                    urwid.Columns([
                        urwid.Pile([
                            urwid.Button(('button', "One Request"), self.elcaro.test_request),
                            urwid.Button(('button', "Encoding"), self.elcaro.test_arguments_requests),
                            urwid.Columns([
                                ('fixed', 4, self.elcaro.n_requests),
                                urwid.Button(('button', "Req(s)."), self.elcaro.test_n_requests)
                            ])
                        ])
                    ]),
                    self.register_unregister_button,
                    urwid.Button(('button', " F8|Exit   "), self.elcaro.ask_quit),
                ], focus_column=2
            ),
        ], focus_item=9)
        fill = urwid.Filler(self.pile, valign=urwid.TOP)
        fill = urwid.AttrWrap(fill, 'body')
        self.__super.__init__(urwid.AttrWrap(fill, 'chars'))

    def refresh(self):
        self.network_chain_id.set_text(('network', str(self.elcaro.chain_id)))
        self.network_peers.set_text(('network', str(self.elcaro.peer_count)))
        self.network_block.set_text(('network', "#" + str(self.elcaro.current_block)))
        if self.elcaro.registered is None:
            self.register_unregister_button._selectable = False
            self.register_unregister_button.set_label(('button', ""))
        else:
            if self.elcaro.registered:
                self.register_unregister_button.set_label(('button', " Unregister "))
            else:
                self.register_unregister_button.set_label(('button', " Register  "))

        if self.elcaro.syncing:
            self.network_block_title.set_text(('network title', u"Block..."))
            self.node_balance.set_text(('node', '?'))
        else:
            self.network_block_title.set_text(('network title', u"Block"))

        if self.elcaro.balance:
            self.node_balance.set_text(('node', str(self.elcaro.balance) + "Ξ"))
        else:
            self.node_balance.set_text(('node', "?"))

        if self.elcaro.active_nodes:
            self.active_nodes.set_text(('contract', str(self.elcaro.active_nodes)))
        else:
            self.active_nodes.set_text(('contract', "?"))


class Elcaro:
    palette = [
        ('logo', 'yellow,bold', 'black', 'standout'),
        ('body', 'white', 'black', 'standout'),
        ('exit', 'yellow', 'black', 'standout'),
        ('title', 'white,bold', 'black'),

        ('network title', 'yellow,bold', 'black'),
        ('network', 'yellow', 'black'),

        ('contract title', 'light blue,bold', 'black'),
        ('contract', 'light blue', 'black'),

        ('node title', 'light red,bold', 'black'),
        ('node', 'light red', 'black'),

        ('others', 'light blue', 'black'),
        ('me', 'light red', 'black'),

        ('button', 'white', 'dark blue', 'standout'),

        ('header', 'white', 'dark red', 'bold'),
        ('footer', 'black', 'light gray', 'standout'),
        ('button normal', 'light gray', 'dark blue', 'standout'),
        ('button select', 'white', 'dark green'),
        ('button disabled', 'dark gray', 'dark blue'),
        ('edit', 'light gray', 'dark blue'),
        ('bigtext', 'white', 'black'),
        ('chars', 'light gray', 'black'),
        (None, 'light gray', 'black'),
        ('heading', 'black', 'light gray'),
        ('line', 'black', 'light gray'),
        ('options', 'dark gray', 'black'),
        ('focus heading', 'white', 'dark red'),
        ('focus line', 'black', 'dark red'),
        ('focus options', 'black', 'light gray'),
        ('selected', 'white', 'dark blue'),
        ('pb-en', 'black', 'light gray', ''),
        ('pb-dis', 'white', 'dark gray', ''),
    ]

    def __init__(self, config, w3, private_key):
        urwid.set_encoding('utf8')
        self.w3 = w3
        self.w3lock = threading.Lock()
        self.transaction_queue = queue.Queue()
        self.transactions = set()
        self.config = config
        self.account = self.w3.eth.account.from_key(private_key.digest())
        self.watcher = Watcher(self.config.executor_response)
        self.response_thread = threading.Thread(target=self.import_responses,
                                                args=(),
                                                daemon=True)
        self.responder = ThreadPoolExecutor(max_workers=4)

        self.contract_json = None
        with open(self.config.elcaro_json, 'r') as json_file:
            self.contract_json = json.load(json_file)
        self.contract = self.w3.eth.contract(address=self.config.contract, abi=self.contract_json["abi"])

        self.user_contract = None
        with open(self.config.user_contract_json, 'r') as json_file:
            self.user_contract_json = json.load(json_file)
        self.user_contract = self.w3.eth.contract(address=self.config.user_contract, abi=self.user_contract_json["abi"])

        self.chain_id = "?"
        self.peer_count = 0
        self.current_block = "?"

        self.active_nodes = None
        self.registered = None
        self.balance = None
        self.syncing = True

        self.background = urwid.Frame(body=urwid.Pile([]))
        self.background = urwid.AttrWrap(self.background, 'exit')
        fonts = urwid.get_all_fonts()
        for name, fontcls in fonts:
            font = fontcls()
            if fontcls == urwid.HalfBlock5x4Font:
                self.exit_font = font

        self.filter_on_register = self.contract.events.onRegister.createFilter(fromBlock="latest")
        self.filter_on_unregister = self.contract.events.onUnregister.createFilter(fromBlock="latest")
        self.filter_on_request = self.contract.events.onRequest.createFilter(fromBlock="latest")
        self.filter_on_response = self.contract.events.onResponse.createFilter(fromBlock="latest")
        self.filter_on_multi_request = self.contract.events.onMultiRequest.createFilter(fromBlock="latest")

        self.view_transaction_text = urwid.Text(('exit', ""))
        self.view_transaction_overlay = urwid.Overlay(
            urwid.Filler(
                urwid.Pile([
                    self.view_transaction_text,
                    urwid.Button("  BACK", self.show_main)
                ])
            ), self.background, 'center', 100, 'middle', 70)

        self.n_requests = urwid.Edit('', '21', multiline=False, align=urwid.CENTER)

        self.exit_overlay = urwid.BigText(('exit', " Exit? (y/n)"), self.exit_font)
        self.exit_overlay = urwid.Overlay(self.exit_overlay, self.background, 'center', None, 'middle', None)

        self.geth_log = ViewTerminal(['tail', '-f', config.geth_log], encoding='utf-8')
        self.executor_log = ViewTerminal(['tail', '-f', config.executor_log], encoding='utf-8')
        self.refresh_thread = None
        self.update_display = True
        self.running = threading.Event()
        self.running.set()
        self.done = threading.Event()
        self.side_panel = SidePanel(self)
        self.event_viewer = EventViewer(self)
        self.body = urwid.Pile([
            ('weight', 4, self.event_viewer),
        ], focus_item=0)
        self.screen = urwid.Pile([
            urwid.Columns(
                [('fixed', 44, self.side_panel), ('weight', 1, self.body)]),
            ('fixed', 13, urwid.LineBox(self.executor_log, title="executor")),
            ('fixed', 6, urwid.LineBox(self.geth_log, title="geth")),
        ])
        self.screen = urwid.AttrWrap(self.screen, 'body')
        self.screen = urwid.Frame(body=self.screen)

        self.response_thread.start()

        self.loop = urwid.MainLoop(self.screen, self.palette,
                                   unhandled_input=self.unhandled_input)

    def on_register(self, event):
        self.event_viewer.list.append(urwid.Pile([
            urwid.Text("  onRegister(node_account=" + str(event['args']['node_account']) +
                       ", node_count=" + str(event['args']['node_count']) + ")"),
            urwid.Divider(),
        ]))
        self.event_viewer.list.focus = len(self.event_viewer.list) - 1
        return

    def on_unregister(self, event):
        self.event_viewer.list.append(urwid.Pile([
            urwid.Text("  onUnregister(node_account=" + str(event['args']['node_account']) +
                       ", node_count=" + str(event['args']['node_count']) + ")"),
            urwid.Divider(),
        ]))
        self.event_viewer.list.focus = len(self.event_viewer.list) - 1
        return

    def import_responses(self):
        while not self.done.isSet():
            while not self.watcher.queue.empty():
                request = self.watcher.queue.get(True)
                self.responder.submit(self.create_response, request)
            time.sleep(1)

    def create_response(self, _response):
        response = None
        try:
            with open(_response) as f:
                response = json.load(f)
            os.remove(_response)
        except:
            response = None

        if response is None:
            return

        self.w3lock.acquire()
        try:
            nonce = self.w3.eth.getTransactionCount(self.account.address)
            request_args = eth_abi.encode_abi(response["argument_types"], response["arguments"])
            request_data = eth_abi.encode_abi(
                # _function, _arguments, _contract, _callback, block.number, tx.origin, msg.sender
                ["string", "bytes", "address", "string", "uint256", "address", "address"],
                [
                    response["function"], request_args, response["contract"], response["callback"],
                    int(response["block.number"]), response["tx.origin"], response["msg.sender"]
                ]
            )
            response_types = response['callback'][response['callback'].find("("):response['callback'].rfind(")") + 1]
            if response_types.find(",") == -1:
                response_types = response_types[1:-1]
            result = response['response']['result']
            response_data = eth_abi.encode_single(response_types, result)
            transaction = self.contract.functions.response(
                request_data, response_data,
                response['response']['stdout'], response['response']['stderr']).buildTransaction({
                'chainId': self.w3.eth.chainId,
                'gas': 4000000,
                'gasPrice': w3.toWei('2', 'gwei'),
                'nonce': nonce,
            })
            signed = self.w3.eth.account.sign_transaction(transaction, self.account.key)
            if not (signed.hash in self.transactions):
                self.transactions.add(signed.hash)
                try:
                    self.w3.eth.sendRawTransaction(signed.rawTransaction)
                finally:
                    self.transaction_queue.put(signed.hash)
                    self.event_viewer.list.append(urwid.Pile([
                        urwid.Text("  creating response transaction → \n    " + signed.hash.hex()),
                        urwid.Text("  -> " + str(response_types) + ":" + str(result) +" -> " + response_data.hex()),
                        urwid.Button("  → View Transaction", self.view_transaction, user_data=(False, signed.hash)),
                        urwid.Button("  → View Transaction Recipe ", self.view_transaction,
                                     user_data=(True, signed.hash)),
                        urwid.Divider(),
                    ]), )
                    self.event_viewer.list.focus = len(self.event_viewer.list) - 1
        finally:
            self.w3lock.release()

        return

    def on_request(self, event):
        # _function, _arguments, _contract, _callback, block.number, tx.origin, msg.sender
        request_data = eth_abi.decode_abi(["string", "bytes", "address", "string", "uint256", "address", "address"],
                                          event['args']['data'])
        function_signature = request_data[0]
        function_signature = function_signature[function_signature.rfind("/") + 1:]
        function_argument_types = function_signature[function_signature.find("("):function_signature.rfind(")") + 1]
        function_argument_data = eth_abi.decode_single(function_argument_types, request_data[1])
        request_json = {'node_account': str(event['args']['node_account']),
                        'request_hash': "0x" + event['args']['request_hash'].hex(),
                        'function': request_data[0], 'arguments': function_argument_data,
                        'contract': str(request_data[2]), 'callback': str(request_data[3]),
                        'block.number': str(request_data[4]), 'tx.origin': str(request_data[5]),
                        'msg.sender': str(request_data[6])}

        request_for = "others"
        if request_json['node_account'] == self.account.address:
            request_for = "me"

        self.event_viewer.list.append(urwid.Pile([
            urwid.Text((request_for, "  onRequest(\n" +
                        "    [ request for: " + request_for + " ]\n" +
                        "    node_account: " + request_json[
                            'node_account'] + "\n" +
                        "    request_hash: " + request_json['request_hash'] + "\n" +
                        "    function: " + request_json['function'] + "\n" +
                        "    arguments: " + str(request_json['arguments']) + "\n" +
                        "    contract: " + request_json['contract'] + "\n" +
                        "    callback: " + request_json['callback'] + "\n" +
                        "    block.number: " + request_json['block.number'] + "\n" +
                        "    tx.origin: " + request_json['tx.origin'] + "\n" +
                        "    msg.sender: " + request_json['msg.sender'] + "\n" +
                        "  )")),
            urwid.Divider(),
        ]))
        self.event_viewer.list.focus = len(self.event_viewer.list) - 1

        if request_for == "me":
            with open(self.config.executor_request +
                      "/" + request_json['request_hash'] + ".json", "w") as outfile:
                outfile.write(json.dumps(request_json, indent=4))

    def on_multi_request(self, event):
        # _function, _arguments, _contract, _callback, block.number, tx.origin, msg.sender
        request_data = eth_abi.decode_abi(["string", "bytes", "address", "string", "uint256", "address", "address"],
                                          event['args']['data'])
        function_signature = request_data[0]
        function_signature = function_signature[function_signature.rfind("/") + 1:]
        function_argument_types = function_signature[function_signature.find("("):function_signature.rfind(")") + 1]
        function_argument_data = eth_abi.decode_single(function_argument_types, request_data[1])
        request_json = {'node_account': str(event['args']['node_account']),
                        'request_hash': "0x" + event['args']['request_hash'].hex(),
                        'index': str(event['args']['index']), 'count': str(event['args']['count']),
                        'function': request_data[0], 'arguments': function_argument_data,
                        'contract': str(request_data[2]), 'callback': str(request_data[3]),
                        'block.number': str(request_data[4]), 'tx.origin': str(request_data[5]),
                        'msg.sender': str(request_data[6])}

        request_for = "others"
        if request_json['node_account'] == self.account.address:
            request_for = "me"

        self.event_viewer.list.append(urwid.Pile([
            urwid.Text((request_for, "  onMultiRequest(\n" +
                        "    [ request for: " + request_for + " ]\n" +
                        "    node_account: " + request_json['node_account'] + "\n" +
                        "    request_hash: " + request_json['request_hash'] + "\n" +
                        "    index: " + request_json['index'] + "\n" +
                        "    count: " + request_json['count'] + "\n" +
                        "    function: " + request_json['function'] + "\n" +
                        "    arguments: " + str(request_json['arguments']) + "\n" +
                        "    contract: " + request_json['contract'] + "\n" +
                        "    callback: " + request_json['callback'] + "\n" +
                        "    block.number: " + request_json['block.number'] + "\n" +
                        "    tx.origin: " + request_json['tx.origin'] + "\n" +
                        "    msg.sender: " + request_json['msg.sender'] + "\n" +
                        "  )")),
            urwid.Divider(),
        ]))
        self.event_viewer.list.focus = len(self.event_viewer.list) - 1

        if request_for == "me":
            with open(self.config.executor_request +
                      "/" + request_json['request_hash'] + "@" + request_json['index'] + ".json", "w") as outfile:
                outfile.write(json.dumps(request_json, indent=4))

    def on_response(self, event):
        self.event_viewer.list.append(urwid.Pile([
            urwid.Text("  onResponse(node_account=" + str(event['args']['node_account']) +
                       ", request_hash=0x" + event['args']['request_hash'].hex() +
                       ", contract_address=" + str(event['args']['contract_address']) +
                       ", signature='" + str(event['args']['signature']) + "'" +
                       ", data=0x" + event['args']['data'].hex() +
                       ", stdout='" + str(event['args']['stdout']) + "'"+
                       ", stderr='" + str(event['args']['stderr']) + "'"
                       ),
            urwid.Divider(),
        ]))
        self.event_viewer.list.focus = len(self.event_viewer.list) - 1
        return

    def __del__(self):
        print("")
        self.refresh_thread.join()

    def show_main(self, button):
        self.loop.widget = self.screen
        self.update_display = True
        return True

    def ask_quit(self, button):
        self.update_display = False
        self.loop.widget = self.exit_overlay

    def view_transaction(self, button, transaction):
        (want_receipt, tx_hash) = transaction
        self.update_display = False
        self.w3lock.acquire()
        try:
            try:
                if want_receipt:
                    result = self.w3.eth.getTransactionReceipt(tx_hash)
                else:
                    result = self.w3.eth.getTransaction(tx_hash)
                self.view_transaction_text.set_text(str(result))
            except:
                self.view_transaction_text.set_text(tx_hash.hex())
        finally:
            self.w3lock.release()

        self.loop.widget = self.view_transaction_overlay

    def test_request(self, button):
        self.w3lock.acquire()
        try:
            nonce = self.w3.eth.getTransactionCount(self.account.address)
            action = None
            transaction = self.user_contract.functions.test_hello_world().buildTransaction({
                'chainId': self.w3.eth.chainId,
                'gas': 1000000,
                'gasPrice': w3.toWei('2', 'gwei'),
                'nonce': nonce,
            })
            signed = self.w3.eth.account.sign_transaction(transaction, self.account.key)
            if not (signed.hash in self.transactions):
                self.transactions.add(signed.hash)
                try:
                    self.w3.eth.sendRawTransaction(signed.rawTransaction)
                finally:
                    self.transaction_queue.put(signed.hash)
                    self.event_viewer.list.append(urwid.Pile([
                        urwid.Text(
                            "  " + self.config.user_contract + ".test_hello_world() → \n    " + signed.hash.hex()),
                        urwid.Button("  → View Transaction", self.view_transaction, user_data=(False, signed.hash)),
                        urwid.Button("  → View Transaction Recipe ", self.view_transaction,
                                     user_data=(True, signed.hash)),
                        urwid.Divider(),
                    ]), )
                    self.event_viewer.list.focus = len(self.event_viewer.list) - 1
        finally:
            self.w3lock.release()

    def test_n_requests(self, button):
        self.w3lock.acquire()
        try:
            nonce = self.w3.eth.getTransactionCount(self.account.address)
            action = None
            transaction = self.user_contract.functions.test_n(int(self.n_requests.get_edit_text())).buildTransaction({
                'chainId': self.w3.eth.chainId,
                'gas': 4000000,
                'gasPrice': w3.toWei('2', 'gwei'),
                'nonce': nonce,
            })
            signed = self.w3.eth.account.sign_transaction(transaction, self.account.key)
            if not (signed.hash in self.transactions):
                self.transactions.add(signed.hash)
                try:
                    self.w3.eth.sendRawTransaction(signed.rawTransaction)
                finally:
                    self.transaction_queue.put(signed.hash)
                    self.event_viewer.list.append(urwid.Pile([
                        urwid.Text("  " + self.config.user_contract + ".test_n() → \n    " + signed.hash.hex()),
                        urwid.Button("  → View Transaction", self.view_transaction, user_data=(False, signed.hash)),
                        urwid.Button("  → View Transaction Recipe ", self.view_transaction,
                                     user_data=(True, signed.hash)),
                        urwid.Divider(),
                    ]), )
                    self.event_viewer.list.focus = len(self.event_viewer.list) - 1
        finally:
            self.w3lock.release()

    def test_arguments_requests(self, button):
        self.w3lock.acquire()
        try:
            nonce = self.w3.eth.getTransactionCount(self.account.address)
            action = None
            transaction = self.user_contract.functions.test_get_tuple_uint256_string().buildTransaction({
                'chainId': self.w3.eth.chainId,
                'gas': 4000000,
                'gasPrice': w3.toWei('2', 'gwei'),
                'nonce': nonce,
            })
            signed = self.w3.eth.account.sign_transaction(transaction, self.account.key)
            if not (signed.hash in self.transactions):
                self.transactions.add(signed.hash)
                try:
                    self.w3.eth.sendRawTransaction(signed.rawTransaction)
                finally:
                    self.transaction_queue.put(signed.hash)
                    self.event_viewer.list.append(urwid.Pile([
                        urwid.Text(
                            "  " + self.config.user_contract + ".test_get_tuple_uint256_string() → \n    " + signed.hash.hex()),
                        urwid.Button("  → View Transaction", self.view_transaction, user_data=(False, signed.hash)),
                        urwid.Button("  → View Transaction Recipe ", self.view_transaction,
                                     user_data=(True, signed.hash)),
                        urwid.Divider(),
                    ]), )
                    self.event_viewer.list.focus = len(self.event_viewer.list) - 1
        finally:
            self.w3lock.release()

    def register_unregister(self, button):
        self.w3lock.acquire()
        try:
            nonce = self.w3.eth.getTransactionCount(self.account.address)
            action = None
            transaction = {
                'chainId': self.w3.eth.chainId,
                'gas': 1000000,
                'gasPrice': w3.toWei('2', 'gwei'),
                'nonce': nonce,
            }
            if "Unreg" in button.label:
                action = "unregister"
                transaction = self.contract.functions.unregister().buildTransaction(transaction)
            else:
                action = "register"
                transaction = self.contract.functions.register().buildTransaction(transaction)
            signed = self.w3.eth.account.sign_transaction(transaction, self.account.key)
            if not (signed.hash in self.transactions):
                self.transactions.add(signed.hash)
                try:
                    self.w3.eth.sendRawTransaction(signed.rawTransaction)
                finally:
                    self.transaction_queue.put(signed.hash)
                    self.event_viewer.list.append(urwid.Pile([
                        urwid.Text("  " + self.config.contract + "." + action + "() → \n    " + signed.hash.hex()),
                        urwid.Button("  → View Transaction", self.view_transaction, user_data=(False, signed.hash)),
                        urwid.Button("  → View Transaction Recipe ", self.view_transaction,
                                     user_data=(True, signed.hash)),
                        urwid.Divider(),
                    ]), )
                    self.event_viewer.list.focus = len(self.event_viewer.list) - 1
        finally:
            self.w3lock.release()

    def handle_events(self):
        self.w3lock.acquire()
        try:
            if self.syncing:
                return

            for event in self.filter_on_register.get_new_entries():
                self.on_register(event)
            for event in self.filter_on_unregister.get_new_entries():
                self.on_unregister(event)
            for event in self.filter_on_request.get_new_entries():
                self.on_request(event)
            for event in self.filter_on_multi_request.get_new_entries():
                self.on_multi_request(event)
            for event in self.filter_on_response.get_new_entries():
                self.on_response(event)
        finally:
            self.w3lock.release()

    def update_data(self):
        self.w3lock.acquire()
        try:
            self.syncing = self.w3.eth.syncing
            self.peer_count = self.w3.net.peer_count
            self.chain_id = self.w3.eth.chainId

            if self.syncing:
                self.balance = self.w3.fromWei(0, "ether")
                self.current_block = self.w3.eth.syncing.currentBlock
                self.registered = None
            else:
                self.current_block = self.w3.eth.blockNumber
                # basics
                try:
                    self.balance = self.w3.fromWei(self.w3.eth.getBalance(self.account.address), "ether")
                except:
                    self.balance = None

                # contract interaction, contract need to be deployed
                try:
                    self.active_nodes = self.contract.functions.nodeCount().call()
                    self.registered = self.contract.functions.isRegistered(self.account.address).call()
                except:
                    self.active_nodes = None
                    self.registered = None
        finally:
            self.w3lock.release()

    def refresh(self):
        while self.running.isSet():
            self.update_data()
            self.handle_events()
            if self.loop.screen.started:
                if self.update_display:
                    self.side_panel.refresh()
                self.loop.draw_screen()
            time.sleep(0.5)
        self.done.set()

    def main(self):
        self.refresh_thread = threading.Thread(target=self.refresh)
        self.refresh_thread.start()
        self.loop.run()
        self.done.clear()
        self.running.clear()

    def unhandled_input(self, key):
        if key == 'f8':
            self.ask_quit('q')
            return True
        if self.loop.widget != self.exit_overlay:
            self.update_display = True
            return
        if key in ('y', 'Y'):
            raise urwid.ExitMainLoop()
        else:
            self.loop.widget = self.screen
            self.update_display = True
            return True


if '__main__' == __name__:
    parser = argparse.ArgumentParser(description='elcaro oracle node.')
    parser.add_argument('--contract', help='contract address to an elcaro contract',
                        default="0x6a1c553b61db4183640707E9DdE365A6c05DF1C3")
    parser.add_argument('--user-contract', help='contract address to an elcaro contract',
                        default="0xc8C1c0EA5F307464C6258B3fBBF2f0F653688eF1")
    parser.add_argument('--geth-log', help='path to geth logfile', default="/data/geth/geth.log")
    parser.add_argument('--ipfs-log', help='path to ipfs logfile')
    parser.add_argument('--executor-log', help='path to executor logfile', default="/data/executor/executor.log")
    parser.add_argument('--executor-request', help='path to executor request directory',
                        default="/data/executor/request")
    parser.add_argument('--executor-response', help='path to executor response directory',
                        default="/data/executor/response")
    parser.add_argument('--elcaro-json', help='path elcaro standard-json compiler artefact',
                        default="/elcaro/contracts/Elcaro.json")
    parser.add_argument('--user-contract-json', help='path user contract standard-json compiler artefact',
                        default="/elcaro/contracts/UserContract.json")

    print(elcaro_logo_centered +
          "\n\n"
          "     ATTENTION  The private key of the node will be derived from\n"
          "                the username and the password you enter. That means,\n"
          "                if you use a weak username-password pair others may\n"
          "                be able to access the node account.\n"
          "\n"
          " !! THIS IS HIGHLY EXPERIMENTAL SOFTWARE AND TO BE USED AT YOUR OWN RISK !!\n")

    username = input(' - Login: ')
    password = getpass.getpass(' - Password:')
    private_key = hashlib.sha256()
    private_key.update(argon2.using(salt='elcaro-oracle'.encode("utf-8")).hash(username + password).encode('utf-8'))

    w3 = Web3(Web3.WebsocketProvider('ws://127.0.0.1:8545'))
    if not w3.isConnected():
        print("error: could not connect to geth node @ ws://127.0.0.1:8545. aborting.")
        exit(1)

    Elcaro(parser.parse_args(), w3, private_key).main()
