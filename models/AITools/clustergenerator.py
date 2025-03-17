import random

class ClusterGenerator:
    def __init__(self, file_path):
        self.clusters = self.read(file_path)
        self.chunk_matrix = None

    def _read_chunk(self,chunk_string):
        self.chunk_matrix = chunk_string.split('\n')[:-1]
        for i in range(len(self.chunk_matrix)):
            self.chunk_matrix[i] = self.chunk_matrix[i].split(',')

    def generate_offsets(self):

        chunk_string = random.choice(self.clusters)
        self._read_chunk(chunk_string)

        offsets_list = []
        for offset_Y in range(len(self.chunk_matrix)):
            for offset_X in range(len(self.chunk_matrix[0])):
                if self.chunk_matrix[offset_Y][offset_X] != " ":
                    offsets_list.append((offset_Y, offset_X))

        return offsets_list

    
    def read(self, file_path):
        clusters = ""

        with open(file_path, "r") as clusters_file:
            clusters = clusters_file.read()

        clusters = clusters.split("#\n")

        return clusters