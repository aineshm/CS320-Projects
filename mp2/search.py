class Node():
    def __init__(self, key):
        self.key = key 
        self.values = []
        self.left = None
        self.right = None
    
    def __len__(self):
        size = len(self.values)
        if self.left != None:
            size += len(self.left.values)
        if self.right != None:
            size += len(self.right.values)
        return size

    def lookup(self,key):
        if(self.key == key):
            return self.values
        if key < self.key and self.left != None:
            return self.left.lookup(key)
        if key > self.key and self.right != None:
            return self.right.lookup(key)
        else:
            return []
    
    def height(self):
        if self.left == None:
            l = 0
        else:
            # recurse left
            l = self.left.height()
            
        if self.right == None:
            r = 0
        else:
            # recurse right
            r = self.right.height()
            
        return max(l, r)+1
    
    
    # def num_nodes(self):
    #     if self == None:
    #         return 0
    #     count = 1  # Count the current node
    #     if self.left == None and self.right == None:
    #         return 1
    #     if self.left != None:
    #         count += self.left.num_nodes()
    #     if self.right != None:
    #         count += self.right.num_nodes()
    #     return count

    
    
    
class BST():
    def __init__(self):
        self.root = None

    def add(self, key, val):
        if self.root == None:
            self.root = Node(key)

        curr = self.root
        while True:
            if key < curr.key:
                # go left
                if curr.left == None:
                    curr.left = Node(key)
                curr = curr.left
            elif key > curr.key:
                 # go right
                 if curr.right == None:
                     curr.right = Node(key)
                 curr = curr.right
                 
            else:
                # found it!
                assert curr.key == key
                break

        curr.values.append(val)


    def __dump(self, node):
        if node == None:
            return
        self.__dump(node.right)            # 1
        print(node.key, ":", node.values)  # 2
        self.__dump(node.left)             # 3

    def dump(self):
        self.__dump(self.root)

    
    def __getitem__(self,key):
        return self.root.lookup(key)
    
    
    def get_height(self):
        return self.root.height()

    def num_nonleaf_nodes(self):
        return self.helper_num_nonleaf(self.root)
    
    def helper_num_nonleaf(self,node):
        if node == None or (node.right == None and node.left == None):
            return 0
        return 1 + self.helper_num_nonleaf(node.right) + self.helper_num_nonleaf(node.left)
    

    def num_nodes(self,curr):
        if curr is None:
            return 0
        return 1 + self.num_nodes(curr.left) + self.num_nodes(curr.right)
        
    def num_leafs(self):
        return self.num_nodes(self.root) - self.num_nonleaf_nodes()
    
    def top_n_keys(self,n):
        self.top_n_keys_list = []
        self.helper_top_n_keys(self.root, n)
        return self.top_n_keys_list
    
    def helper_top_n_keys(self, curr, n):
        if curr is None or len(self.top_n_keys_list) >= n:
            return 
        self.helper_top_n_keys(curr.right, n)
        if len(self.top_n_keys_list) < n:
            self.top_n_keys_list.append(curr.key)
        self.helper_top_n_keys(curr.left, n)