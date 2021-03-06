# coding=utf-8

import numpy as np
import os

import networkx as nx
from tf_geometric.data.graph import Graph
from tf_geometric.data.dataset import DownloadableDataset
import json

from tf_geometric.utils.data_utils import load_cache
from tf_geometric.utils.graph_utils import convert_edge_to_directed


class TUDataset(DownloadableDataset):

    def __init__(self, dataset_name, dataset_root_path=None):
        tu_base_url = 'https://ls11-www.cs.tu-dortmund.de/people/morris/graphkerneldatasets'
        super().__init__(dataset_name=dataset_name,
                         download_urls=[
                             "{}/{}.zip".format(tu_base_url, dataset_name)
                         ],
                         download_file_name="{}.zip".format(dataset_name),
                         cache_name=None,
                         dataset_root_path=dataset_root_path,
                         )
        self.txt_root_path = os.path.join(self.raw_root_path, self.dataset_name)
        self.prefix = "{}_".format(self.dataset_name)

    def process(self):

        edges = self.read_txt_as_array("A", dtype=np.int32) - 1
        node_graph_index = self.read_txt_as_array("graph_indicator", dtype=np.int32) - 1
        edge_graph_index = node_graph_index[edges[:, 0]]
        num_graphs = node_graph_index.max() + 1

        # node_labels
        node_labels = self.read_txt_as_array("node_labels", dtype=np.int32)

        # node_labels
        edge_labels = self.read_txt_as_array("edge_labels", dtype=np.int32)

        # node_labels
        node_attributes_list = self.read_txt_as_array("node_attributes", dtype=np.float32)

        # graph_labels
        graph_labels = self.read_txt_as_array("graph_labels", dtype=np.int32)

        def create_empty_graph():
            graph = {"edge_index": []}

            if node_labels is not None:
                graph["node_labels"] = []

            if node_attributes_list is not None:
                graph["node_attributes"] = []

            if edge_labels is not None:
                graph["edge_labels"] = []

            if graph_labels is not None:
                graph["graph_label"] = None

            return graph

        graphs = [create_empty_graph() for _ in range(num_graphs)]

        start_node_index = np.full([num_graphs], -1).astype(np.int32)
        for node_index, graph_index in enumerate(node_graph_index):
            if start_node_index[graph_index] < 0:
                start_node_index[graph_index] = node_index

        # edge_index
        for graph_index, edge in zip(edge_graph_index, edges):
            graph = graphs[graph_index]
            graph["edge_index"].append(edge)


        if node_labels is not None:
            node_labels -= node_labels.min()
            for graph_index, node_label in zip(node_graph_index, node_labels):
                graph = graphs[graph_index]
                graph["node_labels"].append(node_label)

        if edge_labels is not None:
            edge_labels -= edge_labels.min()
            for graph_index, edge_label in zip(edge_graph_index, edge_labels):
                graph = graphs[graph_index]
                graph["edge_labels"].append(edge_label)


        if node_attributes_list is not None:
            node_attributes_list = node_attributes_list.reshape(node_attributes_list.shape[0], -1)
            for graph_index, node_attributes in zip(node_graph_index, node_attributes_list):
                graph = graphs[graph_index]
                graph["node_attributes"].append(node_attributes)


        # graph_labels

        if graph_labels is not None:
            graph_labels -= graph_labels.min()
            for graph, graph_label in zip(graphs, graph_labels):
                graph["graph_label"] = np.array([graph_label]).astype(np.int32)

        for i, graph in enumerate(graphs):
            graph["edge_index"] = np.array(graph["edge_index"]).T - start_node_index[i]

            if node_labels is not None:
                graph["node_labels"] = np.array(graph["node_labels"]).astype(np.int32)

            if node_attributes_list is not None:
                graph["node_attributes"] = np.array(graph["node_attributes"]).astype(np.float32)

            if edge_labels is not None:
                graph["edge_labels"] = np.array(graph["edge_labels"]).astype(np.int32)

        return graphs


    def get_path_by_fid(self, fid):
        fname = "{}_{}.txt".format(self.dataset_name, fid)
        return os.path.join(self.txt_root_path, fname)


    def read_txt_as_array(self, fid, dtype):
        path = self.get_path_by_fid(fid)
        if not os.path.exists(path):
            return None
        data_list = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if len(line) == 0:
                    continue
                items = line.split(",")
                items = [dtype(item) for item in items]
                data = items[0] if len(items) == 1 else items
                data_list.append(data)
        data_list = np.array(data_list).astype(dtype)
        return data_list




