from collections import defaultdict
import queue
from typing import Dict, List, Set

node_id_list = [i for i in range(1, 18)]
M = [2, 4, 6]
node_list = []
edge_list = []

class Channel:

    def __init__(self, node1, node2) -> None:
        self.node1 = node1
        self.node2 = node2
        self.name = ''
    
    def get_name(self):
        return self.name

    def set_in_out(in_node, out_node):
        if in_node.get_id() < out_node.get_id():
            node1 = in_node
            node2 = out_node
        else:
            node1 = out_node
            node2 = in_node
        chan = Channel.check_in_edge_list(node1, node2)
        if chan is None:
            chan = Channel(node1, node2)
            chan.name = 'c{0}_{1}'.format(in_node.get_id(), out_node.get_id())
            edge_list.append(chan)
        else:
            chan.name += 'b'
        in_node.add_out(chan)
        out_node.add_in(chan)
    
    def check_in_edge_list(node1, node2):
        edge: Channel
        for edge in edge_list:
            if edge.node1 == node1 and edge.node2 == node2:
                return edge
        return None

    def get_another_node(self, node):
        if self.node1 == node:
            return self.node2
        else:
            return self.node1
    
    def add_to_list(self):
        edge_list.append(self)
    
    def get_change_list_str(self, to):
        '''
            TODO for bidirection
        '''
        return [f'next({self.get_name()})={to}']
    
    def get_other_set(self):
        chan_list = edge_list.copy()
        chan_list.remove(self)
        return set(chan_list)



class Node:

    def __init__(self, id) -> None:
        self.id = id
        self.out_e_list = []
        self.in_e_list = []
        self.reachable = []

    def add_out(self, out_e):
        self.out_e_list.append(out_e)
    
    def add_in(self, in_e):
        self.in_e_list.append(in_e)
    
    def get_id(self):
        return self.id
    
    def add_to_list(self):
        node_list.append(self)

    def calc_shortest_paths(self):
        visited = set()
        self.ok_set: Dict[Node, set] = defaultdict(set)
        visited.add(self)
        q = queue.SimpleQueue()
        out_e: Channel
        for out_e in self.out_e_list:
            out_node = out_e.get_another_node(self)
            if out_node not in visited:
                q.put(out_node)
                self.ok_set[out_node].add(out_e)
                visited.add(out_node)
        while True:
            next_layer = set()
            while not q.empty():
                node: Node = q.get()
                out_e: Channel
                for out_e in node.out_e_list:
                    out_node = out_e.get_another_node(node)
                    if out_node not in visited:
                        next_layer.add(out_node)
                        self.ok_set[out_node] = self.ok_set[out_node].union(self.ok_set[node])
            for node in next_layer:
                visited.add(node)
                q.put(node)
            if len(next_layer) == 0:
                break


class CTLSPECString:

    def __init__(self) -> None:
        self.cond = []
    
    def append(self, string):
        if string not in self.cond:
            self.cond.append(string)
    
    def get(self):
        all_cond = ''
        for cond in self.cond:
            all_cond += '\t({0}) |\n'.format(cond)
        all_cond = all_cond[:-2]
        string = 'CTLSPEC !EF!(\n{0}\n)'.format(all_cond)
        return string

CTLSPEC = CTLSPECString()

def init_node_list():
    for id in node_id_list:
        node = Node(id)
        node.add_to_list()

def read_graph(file):
    with open(file, 'r') as f:
        for line in f.readlines():
            in_id, out_id = line.split(' ')
            in_id, out_id = int(in_id), int(out_id)
            in_node, out_node = node_list[in_id-1], node_list[out_id-1]
            Channel.set_in_out(in_node, out_node)
    node_list.sort(key=lambda x: x.get_id())
    node: Node
    for node in node_list:
        node.calc_shortest_paths()

def genVar():
    out = 'VAR\n'
    edge: Channel
    for edge in edge_list:
        out += f'\t{edge.get_name()}: 0..{len(node_list)};\n'
    return out

def genInit():
    out = 'INIT\n\t'
    edge: Channel
    for edge in edge_list:
        out += f'{edge.get_name()} = 0 & '
    out = out[:-2]
    out += '\n'
    return out

def genModuleVarInit():
    out = 'MODULE main\n'
    out += genVar()
    out += genInit()
    return out

def get_P(channels):
    out = ''
    channel_list = edge_list.copy()
    for channel in channels:
        channel_list.remove(channel)
    for chan in channel_list:
        out += '& next({0})={0} '.format(chan.get_name())
    out += '|\n'
    return out

def integrateChangeList(change_list):
    out = ''
    for change in change_list:
        out += change + ' & '
    out = out[:-2]
    return out

def genSend():
    print('genSend')
    out = ''
    for m in M:
        src: Node = node_list[m-1]
        dest: Node
        for dest in src.ok_set.keys():
            print(src.get_id(), dest.get_id())
            ok_channels = src.ok_set[dest]
            ok_channel: Channel
            for ok_channel in ok_channels:
                send_stat = '(case {case_cond}: next({chan}) = {dest_id};\n\tTRUE: next({chan}) = {chan};\nesac) ' + get_P([ok_channel])
                case_cond = '{} = 0'.format(ok_channel.get_name())
                CTLSPEC.append(case_cond)
                out += send_stat.format(case_cond=case_cond, chan=ok_channel.get_name(), dest_id=dest.get_id())
    return out

def genRecv():
    out = ''
    node: Node
    for node in node_list:
        in_chan: Channel
        for in_chan in node.in_e_list:
            recv_stat = '(case {case_cond}: next({chan}) = 0;\n\tTRUE: next({chan}) = {chan};\nesac) ' + get_P([in_chan])
            case_cond = '{chan} = {node}'.format(chan=in_chan.get_name(), node=node.get_id())
            CTLSPEC.append(case_cond)
            out += recv_stat.format(case_cond=case_cond, chan=in_chan.get_name())
    return out

def genProcess():
    out = ''
    node: Node
    for node in node_list:
        dest: Node
        for dest in node.ok_set.keys():
            out_chan: Channel
            for out_chan in node.ok_set[dest]:
                in_chan: Channel
                for in_chan in node.in_e_list:
                    in_node: Node = in_chan.get_another_node(node)
                    if in_chan in in_node.ok_set[dest]:
                        prc_stat = '(case {case_cond}: {next_list};\n\tTRUE: {keep_next_list};\nesac) '+get_P([in_chan, out_chan])
                        case_cond = '{in_chan} = {dest} & {out_chan} = 0'.format(in_chan=in_chan.get_name(), dest=dest.get_id(), out_chan=out_chan.get_name())
                        CTLSPEC.append(case_cond)
                        out += prc_stat.format(case_cond=case_cond, next_list=integrateChangeList(in_chan.get_change_list_str(0)+out_chan.get_change_list_str(dest.get_id())), keep_next_list=integrateChangeList(in_chan.get_change_list_str(in_chan.get_name())+out_chan.get_change_list_str(out_chan.get_name())))
    out = out[:-2]
    out += '\n\n'
    return out

def genSpec():
    out = CTLSPEC.get()
    return out

def genTransSpec():
    out = 'TRANS\n'
    out += genSend()
    out += genRecv()
    out += genProcess()
    out += genSpec()
    return out

if __name__ == '__main__':
    init_node_list()
    read_graph('graph.txt')
    print('edge num:', len(edge_list))
    out = genModuleVarInit()
    out += genTransSpec()
    with open('gen.smv', 'w') as f:
        f.write(out)
