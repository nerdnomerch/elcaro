import urwid
import threading
import time
from web3 import Web3
from passlib.hash import argon2
import getpass
import hashlib
import argparse

elcaro_logo = u'         .__\n' \
              '    ____ |  |   ____ _____ _______  ____\n' \
              '  _/ __ \\|   _/ ___\\\\__  \\\\_  __ \\/  _ \\ \n' \
              '  \\  ___/|  |_\\  \\___ / __ \\|  | \\(  <_> )\n' \
              '   \\___  >____/\\___  >____  /__|   \\____/\n' \
              '       \\/          \\/     \\/'

elcaro_logo_centered = u'                          .__\n' \
                       '                     ____ |  |   ____ _____ _______  ____\n' \
                       '                   _/ __ \\|   _/ ___\\\\__  \\\\_  __ \\/  _ \\ \n' \
                       '                   \\  ___/|  |_\\  \\___ / __ \\|  | \\(  <_> )\n' \
                       '                    \\___  >____/\\___  >____  /__|   \\____/\n' \
                       '                        \\/          \\/     \\/'


class ViewTerminal(urwid.Terminal):
    _selectable = False


class SidePanel(urwid.WidgetWrap):
    def __init__(self, w3, config, account):
        self.w3 = w3
        self.account = account
        self.logo = urwid.Text(elcaro_logo)
        self.network_chain_id = urwid.Text("", align=urwid.CENTER)
        self.network_peers = urwid.Text("", align=urwid.CENTER)
        self.network_block = urwid.Text("", align=urwid.CENTER)
        self.active_nodes = urwid.Text("?", align=urwid.CENTER)
        self.contract_address = urwid.Text(config.contract, align=urwid.CENTER)
        self.contract_requests = urwid.Text("?", align=urwid.CENTER)
        self.contract_responses = urwid.Text("?", align=urwid.CENTER)
        self.node_address = urwid.Text(self.account.address, align=urwid.CENTER)
        self.node_requests = urwid.Text("?", align=urwid.CENTER)
        self.node_responses = urwid.Text("?", align=urwid.CENTER)
        self.node_balance = urwid.Text("?Ξ", align=urwid.CENTER)
        self.register_unregister_button = urwid.Button("Register Node", self.register_unregister)
        self.exit_button = urwid.Button("Shutdown Node", self.shutdown_node)

        self.pile = urwid.Pile([
            self.logo,
            urwid.Text(""),
            urwid.Columns(
                [
                    urwid.Pile([urwid.Text(('title', u"Chain ID"), align=urwid.CENTER),
                                self.network_chain_id]),
                    urwid.Pile([urwid.Text(('title', u"Peers"), align=urwid.CENTER),
                                self.network_peers]),
                    urwid.Pile([urwid.Text(('title', u"Block"), align=urwid.CENTER),
                                self.network_block]),
                ]),
            urwid.Text(""),
            urwid.Text(('title', u"Contract"), align=urwid.CENTER),
            self.contract_address,
            urwid.Columns(
                [
                    urwid.Pile([urwid.Text(('title', u"Active Nodes"), align=urwid.CENTER),
                                self.active_nodes]),
                    urwid.Pile([urwid.Text(('title', u"Requests"), align=urwid.CENTER),
                                self.contract_requests]),
                    urwid.Pile([urwid.Text(('title', u"Responses"), align=urwid.CENTER),
                                self.contract_responses]),
                ]),
            urwid.Text(""),
            urwid.Text(('title', u"Node"), align=urwid.CENTER),
            self.node_address,
            urwid.Columns(
                [
                    urwid.Pile([urwid.Text(('title', u"Balance"), align=urwid.CENTER),
                                self.node_balance]),
                    urwid.Pile([urwid.Text(('title', u"Requests"), align=urwid.CENTER),
                                self.node_requests]),
                    urwid.Pile([urwid.Text(('title', u"Responses"), align=urwid.CENTER),
                                self.node_requests]),
                ]),
            urwid.Text(""),
            self.register_unregister_button,
            urwid.Text(""),
            self.exit_button
        ], focus_item=12)
        fill = urwid.LineBox(urwid.Filler(self.pile, valign=urwid.TOP))
        fill = urwid.AttrWrap(fill, 'body')
        self.__super.__init__(urwid.AttrWrap(fill, 'chars'))

    def refresh(self):
        try:
            self.network_block.set_text("#" + str(self.w3.eth.blockNumber))
            self.network_peers.set_text(str(self.w3.net.peer_count))
            self.network_chain_id.set_text(str(self.w3.eth.chainId))
            self.node_balance.set_text(
                str(self.w3.fromWei(self.w3.eth.getBalance(self.account.address), "ether")) + "Ξ")
        except:
            self.network_block.set_text("?")
            self.network_peers.set_text("?")
            self.network_chain_id.set_text("?")
            self.node_balance.set_text("?Ξ")

    def shutdown_node(self, button):
        raise urwid.ExitMainLoop()

    def register_unregister(self, button):
        try:
            self.node_balance.set_text(
                str(self.w3.fromWei(self.w3.eth.getBalance(self.account.address), "ether")) + "Ξ")
            transaction = {'to': self.contract_address.text, 'from': self.account.address, 'value': 10000,
                           'gas': 25000,
                           'gasPrice': 20000000000,
                           'nonce': 1,
                           'chainId': self.w3.eth.chainId};
            signed = self.w3.eth.account.sign_transaction(transaction, self.account.key)
            self.w3.eth.sendRawTransaction(signed.rawTransaction)
        except:
            return


class Display:
    palette = [
        ('body', 'black', 'light gray', 'standout'),
        ('header', 'white', 'dark red', 'bold'),
        ('footer', 'white', 'dark red', 'bold'),
        ('button normal', 'light gray', 'dark blue', 'standout'),
        ('button select', 'white', 'dark green'),
        ('button disabled', 'dark gray', 'dark blue'),
        ('edit', 'light gray', 'dark blue'),
        ('bigtext', 'white', 'black'),
        ('chars', 'light gray', 'black'),
        ('exit', 'white', 'dark cyan'),
        (None, 'light gray', 'black'),
        ('heading', 'black', 'light gray'),
        ('line', 'black', 'light gray'),
        ('options', 'dark gray', 'black'),
        ('focus heading', 'white', 'dark red'),
        ('focus line', 'black', 'dark red'),
        ('focus options', 'black', 'light gray'),
        ('selected', 'white', 'dark blue'),
        ('title', 'black,bold', 'light gray')
    ]

    def __init__(self, config):
        urwid.set_encoding('utf8')
        self.w3 = Web3(Web3.WebsocketProvider('ws://127.0.0.1:8545'))
        if not self.w3.isConnected():
            print("not connected.")
            exit(1)

        print(elcaro_logo_centered +
              "\n\n"
              " !! THIS IS HIGHLY EXPERIMENTAL SOFTWARE AND TO BE USED AT YOUR OWN RISK !!\n"
              "\n"
              "     ATTENTION  The private key of the node will be derived from\n"
              "                the username and the password you enter. That means,\n"
              "                if you use a weak username-password pair others may\n"
              "                be able to access the node account.\n"
              "\n"
              " !! THIS IS HIGHLY EXPERIMENTAL SOFTWARE AND TO BE USED AT YOUR OWN RISK !!\n")

        username = input(' - Login: ')
        password = getpass.getpass(' - Password:')
        m = hashlib.sha256()
        m.update(argon2.using(salt='elcaro-oracle'.encode("utf-8")).hash(username + password).encode('utf-8'))

        self.account = self.w3.eth.account.from_key(m.digest())
        self.status = urwid.Text("STATUS")
        self.status = urwid.AttrWrap(self.status, 'footer')
        if config.geth_log is None:
            config.geth_log = "/data/geth/geth.log"
        self.geth_log = ViewTerminal(['tail', '-f', config.geth_log], encoding='utf-8')
        self.side_panel = SidePanel(self.w3, config, self.account)
        self.screen = urwid.Columns(
            [('fixed', 46, self.side_panel), ('weight', 2, urwid.LineBox(self.geth_log, title="geth"))])
        self.screen = urwid.AttrWrap(self.screen, 'body')
        self.screen = urwid.Frame(footer=self.status, body=self.screen)
        fonts = urwid.get_all_fonts()
        for name, fontcls in fonts:
            font = fontcls()
            if fontcls == urwid.HalfBlock5x4Font:
                self.exit_font = font
        self.exit = urwid.BigText(('exit', " Quit? "), self.exit_font)
        self.exit = urwid.Overlay(self.exit, self.screen, 'center', None, 'middle', None)
        self.refresh_thread = None
        self.running = True
        self.done = False
        self.loop = urwid.MainLoop(self.screen, self.palette,
                                   unhandled_input=self.unhandled_input)

    def __del__(self):
        self.refresh_thread.join()
        print("")

    def refresh(self):
        while self.running:
            self.side_panel.refresh()
            self.loop.draw_screen()
            time.sleep(0.5)
        self.done = True

    def main(self):
        self.refresh_thread = threading.Thread(target=self.refresh)
        self.refresh_thread.start()
        self.loop.run()
        self.done = False
        self.running = False

    def unhandled_input(self, key):
        if key == 'f8':
            self.loop.widget = self.exit
            return True
        if self.loop.widget != self.exit:
            return
        if key in ('y', 'Y'):
            raise urwid.ExitMainLoop()
        if key in ('n', 'N'):
            self.loop.widget = self.screen
            return True


if '__main__' == __name__:
    parser = argparse.ArgumentParser(description='elcaro oracle node.')
    parser.add_argument('--contract', help='contract address to an elcaro contract')
    parser.add_argument('--geth-log', help='path to geth logfile')
    parser.add_argument('--ipfs-log', help='path to ipfs logfile')

    Display(parser.parse_args()).main()
